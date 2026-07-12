"""Hardware control panel via symbolic links and hard links.

Builds a sandboxed control-panel directory where each hardware device is a real
file; the control-panel entries are **symbolic links** to those device files,
and a shared driver-config file is **hard-linked** into every device so they
share one inode.  All operations stay under a caller-provided root (a temp dir
in tests), so nothing on the host is touched.
"""

from __future__ import annotations

import os

DEVICES = {
    "cpu": "vendor=ACME model=QX cores=8",
    "gpu": "vendor=ACME vram=16GB",
    "disk": "type=NVMe size=1TB",
    "net": "type=wifi6 mac=00:11:22:33:44:55",
    "audio": "codec=HD channels=2",
}


def build_control_panel(root: str) -> dict:
    devices_dir = os.path.join(root, "devices")
    panel_dir = os.path.join(root, "control_panel")
    os.makedirs(devices_dir, exist_ok=True)
    os.makedirs(panel_dir, exist_ok=True)

    # shared driver config (one inode, hard-linked into every device)
    shared_cfg = os.path.join(root, "driver.cfg")
    with open(shared_cfg, "w") as f:
        f.write("policy=balanced\n")

    symlinks = {}
    hardlinks = {}
    for name, info in DEVICES.items():
        dev_file = os.path.join(devices_dir, name)
        with open(dev_file, "w") as f:
            f.write(info + "\n")

        # control-panel entry = SYMBOLIC link to the device file
        link = os.path.join(panel_dir, name + ".ctl")
        if os.path.lexists(link):
            os.remove(link)
        os.symlink(dev_file, link)
        symlinks[name] = link

        # shared config = HARD link (same inode as driver.cfg)
        hl = os.path.join(devices_dir, name + ".cfg")
        if os.path.lexists(hl):
            os.remove(hl)
        os.link(shared_cfg, hl)
        hardlinks[name] = hl

    return {
        "panel_dir": panel_dir,
        "symlinks": symlinks,
        "hardlinks": hardlinks,
        "shared_cfg": shared_cfg,
    }


def inspect(panel: dict) -> dict:
    """Verify the link kinds: symlinks resolve to device files; hardlinks
    share the shared-config inode."""
    sym_ok = all(os.path.islink(p) and os.path.exists(os.path.realpath(p))
                 for p in panel["symlinks"].values())
    shared_inode = os.stat(panel["shared_cfg"]).st_ino
    hard_ok = all(os.stat(p).st_ino == shared_inode
                  for p in panel["hardlinks"].values())
    nlink = os.stat(panel["shared_cfg"]).st_nlink
    return {
        "symlinks": len(panel["symlinks"]),
        "symlinks_ok": sym_ok,
        "hardlinks": len(panel["hardlinks"]),
        "hardlinks_share_inode": hard_ok,
        "shared_link_count": nlink,
    }
