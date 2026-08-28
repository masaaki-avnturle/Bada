#!/usr/bin/env python3
# ============================================================================
# badaos-installer-httpd.py — backend of the BadaOS GUI installer.
#
# Serves the Ubuntu-style installer wizard (index.html, same directory) on
# http://127.0.0.1:7788/ and gives it four root-privileged endpoints:
#
#   GET  /api/disks     disks, partitions and free regions as JSON
#                       (segments in on-disk order, for the partition bar)
#   POST /api/install   mode=free|part|disk & target=/dev/XXX
#                       -> runs `badaos-install --run MODE TARGET`
#   GET  /api/progress  {"state": idle|running|done|error, "rc": n, "log": ...}
#   POST /api/reboot    systemctl reboot
#
# Runs as root from badaos-installer.service, on the live system only.
# Binds localhost only; the actual disk work stays in badaos-install.
# ============================================================================
import http.server
import json
import os
import re
import subprocess
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = "/run/badaos-installer.log"
PORT = 7788

lock = threading.Lock()
proc = None            # the running badaos-install, if any
finished_rc = None     # exit code once it finished


def sh(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ""


def live_disk():
    """The disk holding the live medium (never offered as a target)."""
    src = sh(["findmnt", "-no", "SOURCE", "/run/live/medium"]).strip()
    if not src:
        return None
    pk = sh(["lsblk", "-nro", "PKNAME", src]).strip().splitlines()
    return "/dev/" + pk[0] if pk and pk[0] else src


def part_name(disk, number):
    d = disk[len("/dev/"):]
    p = "p" if re.match(r"^(nvme|mmcblk)", d) else ""
    return f"{d}{p}{number}"


def disk_segments(disk, size_mib):
    """Partitions + free regions of one disk, in order, from parted -m."""
    out = sh(["parted", "-s", "-m", disk, "unit", "MiB", "print", "free"])
    segs = []
    for line in out.replace(";", "").splitlines():
        f = line.split(":")
        if len(f) < 5 or not f[0].isdigit():
            continue
        try:
            size = int(float(f[3].replace("MiB", "")))
        except ValueError:
            continue
        if f[4] == "free":
            if size >= 3:
                segs.append({"type": "free", "sizeMiB": size})
            continue
        name = part_name(disk, int(f[0]))
        dev = "/dev/" + name
        fstype = sh(["blkid", "-o", "value", "-s", "TYPE", dev]).strip() or f[4]
        label = sh(["blkid", "-o", "value", "-s", "LABEL", dev]).strip()
        ptype = sh(["blkid", "-p", "-o", "value", "-s", "PART_ENTRY_TYPE", dev]).strip().lower()
        esp = ptype in ("0xef", "c12a7328-f81f-11d2-ba4b-00a0c93ec93b")
        segs.append({"type": "part", "name": name, "sizeMiB": size,
                     "fstype": fstype, "label": label, "esp": esp})
    if not segs:  # blank disk without a partition table: all free
        segs = [{"type": "free", "sizeMiB": size_mib}]
    return segs


def api_disks():
    j = json.loads(sh(["lsblk", "--json", "-b", "-o", "NAME,TYPE,SIZE,MODEL"]) or '{"blockdevices":[]}')
    skip = live_disk()
    disks = []
    for d in j.get("blockdevices", []):
        if d.get("type") != "disk" or d["name"].startswith(("fd", "loop", "sr", "ram")):
            continue
        dev = "/dev/" + d["name"]
        if skip and dev == skip:
            continue
        size_mib = int(d.get("size") or 0) // (1024 * 1024)
        if size_mib < 1024:
            continue
        segs = disk_segments(dev, size_mib)
        best = max([s["sizeMiB"] for s in segs if s["type"] == "free"], default=0)
        disks.append({"dev": dev, "sizeMiB": size_mib,
                      "model": (d.get("model") or "").strip(),
                      "segments": segs, "bestFree": best})
    return {"disks": disks, "efi": 1 if os.path.isdir("/sys/firmware/efi") else 0}


class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        global proc, finished_rc
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/api/disks":
            self._send(200, json.dumps(api_disks()))
        elif self.path == "/api/progress":
            with lock:
                if proc is None:
                    state, rc = "idle", 0
                else:
                    rc = proc.poll()
                    if rc is None:
                        state, rc = "running", 0
                    else:
                        state = "done" if rc == 0 else "error"
            log = ""
            try:
                with open(LOG, "rb") as f:
                    f.seek(0, 2)
                    f.seek(max(0, f.tell() - 6000))
                    log = f.read().decode(errors="replace")
            except OSError:
                pass
            self._send(200, json.dumps({"state": state, "rc": rc, "log": log}))
        else:
            self._send(404, '{"error":"not found"}')

    def do_POST(self):
        global proc
        n = int(self.headers.get("Content-Length") or 0)
        form = urllib.parse.parse_qs(self.rfile.read(n).decode())
        if self.path == "/api/install":
            mode = (form.get("mode") or [""])[0]
            target = (form.get("target") or [""])[0]
            if mode not in ("free", "part", "disk") or not re.match(r"^/dev/[a-z0-9]+$", target):
                self._send(400, '{"error":"bad request"}')
                return
            with lock:
                if proc is not None and proc.poll() is None:
                    self._send(409, '{"error":"already running"}')
                    return
                logf = open(LOG, "wb")
                proc = subprocess.Popen(
                    ["/usr/local/sbin/badaos-install", "--run", mode, target],
                    stdout=logf, stderr=subprocess.STDOUT)
            self._send(200, '{"ok":1}')
        elif self.path == "/api/reboot":
            self._send(200, '{"ok":1}')
            subprocess.Popen(["systemctl", "reboot"])
        else:
            self._send(404, '{"error":"not found"}')

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
