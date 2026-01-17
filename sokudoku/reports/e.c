以下は先に示した Omega スクリプト版を Python に置き換えたパッケージ一式の代表ファイル群です。実行には Python 3、root 権限（物理ディスク透過や OVMF 操作時）、およびホストに libvirt/virsh と OVMF がインストールされていることを前提とします。

パッケージ構成（抜粋）と内容：

- bin/virt
- bin/virtctl
- sbin/setup-ovmf
- etc/virt/virt.conf
- lib/virt/manager.py
- lib/virt/config.py
- libexec/helpers/lock_device.py
- usr/share/doc/virt/README
- setup: README_install

必要に応じて各ファイルをそれぞれ保存してください。

ファイル: bin/virt
```python
#!/usr/bin/env python3
import sys
from lib.virt.manager import CLI

def main():
CLI.run(sys.argv[1:])

if __name__ == "__main__":
  main()
```

  ファイル: bin/virtctl
```python
#!/usr/bin/env python3
import sys
from lib.virt.manager import CLI

  def main():
  CLI.run(sys.argv[1:])

  if __name__ == "__main__":
  main()
```

  ファイル: sbin/setup-ovmf
```python
#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

  def main():
  if os.geteuid() != 0:
    print("run as root")
        return
      name = sys.argv[1] if len(sys.argv) > 1 else "default"
						     dest_dir = Path("/var/lib/libvirt/qemu/nvram")
						     dest_dir.mkdir(parents=True, exist_ok=True)
						     code = Path("/usr/share/OVMF/OVMF_CODE.fd")
						     varsfile = Path("/usr/share/OVMF/OVMF_VARS.fd")
						     if code.exists() and varsfile.exists():
        dst = dest_dir / f"{name}_VARS.fd"
        shutil.copy(varsfile, dst)
        print(f"nvram prepared: {dst}")
	else:
	  print("OVMF not found. Install OVMF package.")

	    if __name__ == "__main__":
	    main()
```

	    ファイル: etc/virt/virt.conf
```ini
# virt-manager Python package config
[global]
driver = libvirt
default_bridge = virbr0
default_image_dir = /var/lib/libvirt/images
ovmf_code = /usr/share/OVMF/OVMF_CODE.fd
ovmf_vars_dir = /var/lib/libvirt/qemu/nvram
allow_physical_passthrough = true
```

	    ファイル: lib/virt/config.py
```python
import configparser
from pathlib import Path

	    def load(path="/etc/virt/virt.conf"):
	    cfg = {}
	    p = Path(path)
	    if not p.exists():
        return cfg
	  cp = configparser.ConfigParser()
	  cp.read(path)
	  if "global" in cp:
	  for k, v in cp["global"].items():
            cfg[k] = v
    return cfg
```

	      ファイル: lib/virt/manager.py
```python
#!/usr/bin/env python3
import subprocess
import shlex
import sys
import os
import uuid
from pathlib import Path
from datetime import datetime
from lib.virt.config import load as load_config
from libexec.helpers.lock_device import ensure_device_unmounted

		   CONFIG = load_config()
		   DEFAULT_BRIDGE = CONFIG.get("default_bridge", "virbr0")
		   IMAGE_DIR = Path(CONFIG.get("default_image_dir", "/var/lib/libvirt/images"))
		   ALLOW_PHYS = CONFIG.get("allow_physical_passthrough", "true").lower() in ("1","true","yes")

		   def runcmd(cmd, input_data=None):
		   p = subprocess.run(shlex.split(cmd), input=input_data, text=True, capture_output=True)
		     if p.returncode != 0:
		     raise RuntimeError(f"cmd failed: {cmd}\n{p.stderr.strip()}")
    return p.stdout

    def parse_vm_list(output):
    vms = []
      for line in output.splitlines():
      parts = line.strip().split()
# naive: try to find uuid and name/state
# accept lines like: <id> <name> ...
        if not line.strip():
            continue
	      vms.append({"raw": line.strip()})
    return vms

	      def parse_snapshot_list(output):
    snaps = []
      for line in output.splitlines():
      if line.strip():
	snaps.append({"name": line.strip(), "created_at": datetime.now().isoformat()})
    return snaps

	  class VM:
	def __init__(self, name, uuid_, state="shutoff", cpu=1, memory_mb=512, disk_paths=None, networks=None):
        self.name = name
        self.uuid = uuid_
        self.state = state
        self.cpu = cpu
        self.memory_mb = memory_mb
        self.disk_paths = disk_paths or []
        self.networks = networks or []
        self.created_at = datetime.now().isoformat()

	class Driver:
    @staticmethod
	def list():
        out = runcmd("virsh list --all")
        return parse_vm_list(out)

    @staticmethod
	def define(xml):
        proc = subprocess.Popen(["virsh", "define", "-"], stdin=subprocess.PIPE, text=True)
        proc.communicate(xml)
        if proc.returncode != 0:
	raise RuntimeError("virsh define failed")
        return True

    @staticmethod
	  def dumpxml(name):
	  return runcmd(f"virsh dumpxml {shlex.quote(name)}")

    @staticmethod
	    def start(name):
	    return runcmd(f"virsh start {shlex.quote(name)}")

    @staticmethod
	      def shutdown(name):
	      return runcmd(f"virsh shutdown {shlex.quote(name)}")

    @staticmethod
		def destroy(name):
		return runcmd(f"virsh destroy {shlex.quote(name)}")

    @staticmethod
		  def reboot(name):
		  return runcmd(f"virsh reboot {shlex.quote(name)}")

    @staticmethod
		    def snapshot_create(name, snap):
		    return runcmd(f"virsh snapshot-create-as {shlex.quote(name)} {shlex.quote(snap)}")

    @staticmethod
		      def snapshot_list(name):
		      return parse_snapshot_list(runcmd(f"virsh snapshot-list {shlex.quote(name)}"))

    @staticmethod
			def snapshot_revert(name, snap):
			return runcmd(f"virsh snapshot-revert {shlex.quote(name)} {shlex.quote(snap)}")

    @staticmethod
			  def console(name):
# interactive: just call virsh console
			  subprocess.run(["virsh", "console", name])
        return True

    @staticmethod
			    def attach_disk(name, path, target):
			    return runcmd(f"virsh attach-disk {shlex.quote(name)} {shlex.quote(path)} {shlex.quote(target)} --persistent")

    @staticmethod
			      def detach_disk(name, target):
			      return runcmd(f"virsh detach-disk {shlex.quote(name)} {shlex.quote(target)} --persistent")

    @staticmethod
				def attach_interface(name, xml):
				proc = subprocess.Popen(["virsh", "attach-interface", name, "--file", "-", "--live", "--config"], stdin=subprocess.PIPE, text=True)
				  proc.communicate(xml)
				  if proc.returncode != 0:
				  raise RuntimeError("virsh attach-interface failed")
        return True

    @staticmethod
				    def dumpxml_def(name):
				    return runcmd(f"virsh dumpxml {shlex.quote(name)}")

    # physical passthrough helpers
    @staticmethod
				      def attach_physical_block(name, host_dev, target_dev="vdb", persistent=True):
				      if not ALLOW_PHYS:
					raise RuntimeError("Physical passthrough disabled by config")
					ensure_device_unmounted(host_dev)
        disk_xml = f"""<disk type='block' device='disk'>
  <driver name='qemu' type='raw' io='native'/>
					<source dev='{host_dev}'/>
					<target dev='{target_dev}' bus='virtio'/>
</disk>"""
  if persistent:
  xml = Driver.dumpxml_def(name)
    if "</devices>" not in xml:
    raise RuntimeError("unexpected domain xml")
      new_xml = xml.replace("</devices>", f"{disk_xml}\n</devices>")
      proc = subprocess.Popen(["virsh", "define", "-"], stdin=subprocess.PIPE, text=True)
      proc.communicate(new_xml)
      if proc.returncode != 0:
    raise RuntimeError("virsh define failed (persist attach)")
      proc2 = subprocess.Popen(["virsh", "attach-device", name, "-"], stdin=subprocess.PIPE, text=True)
      proc2.communicate(disk_xml)
      if proc2.returncode != 0:
      raise RuntimeError("virsh attach-device failed (live attach)")
            return True
      else:
	proc = subprocess.Popen(["virsh", "attach-device", name, "-"], stdin=subprocess.PIPE, text=True)
	  proc.communicate(disk_xml)
	  if proc.returncode != 0:
	  raise RuntimeError("virsh attach-device failed")
            return True

    @staticmethod
	    def detach_physical_block(name, target_dev="vdb"):
        disk_xml = f"""<disk type='block' device='disk'>
	  <target dev='{target_dev}' bus='virtio'/>
</disk>"""
  proc = subprocess.Popen(["virsh", "detach-device", name, "-"], stdin=subprocess.PIPE, text=True)
  proc.communicate(disk_xml)
  if proc.returncode != 0:
  raise RuntimeError("virsh detach-device failed")
        return True

    class Manager:
  def __init__(self):
  self.driver = Driver()

  def list_vms(self):
  return self.driver.list()

  def create_vm(self, params):
        name = params["name"]
  cpu = params.get("cpu", 1)
  mem = params.get("memory_mb", 512)
  disk_path = params.get("disk_path", str(IMAGE_DIR / f"{name}.qcow2"))
  iso = params.get("iso_path")
  bridge = params.get("network_bridge", DEFAULT_BRIDGE)
        disk_xml = f"""<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2'/>
  <source file='{disk_path}'/>
  <target dev='vda' bus='virtio'/>
</disk>"""
        iso_xml = f"""<disk type='file' device='cdrom'><source file='{iso}'/></disk>""" if iso else ""
        xml = f"""<domain type='kvm'>
												      <name>{name}</name>
												      <memory unit='MiB'>{mem}</memory>
												      <vcpu>{cpu}</vcpu>
  <os><type arch='x86_64'>hvm</type></os>
  <devices>
	  {disk_xml}
    {iso_xml}
<interface type='bridge'><source bridge='{bridge}'/><model type='virtio'/></interface>
    <graphics type='vnc' autoport='yes'/>
  </devices>
</domain>"""
      self.driver.define(xml)
      return VM(name, str(uuid.uuid4()), state="shutoff", cpu=cpu, memory_mb=mem, disk_paths=[disk_path], networks=[{"bridge":bridge}])

      def start_vm(self, name):
      self.driver.start(name)
        return True

      def shutdown_vm(self, name, force=False):
      if force:
	self.driver.destroy(name)
        else:
	  self.driver.shutdown(name)
        return True

	    def reboot_vm(self, name):
	    self.driver.reboot(name)
        return True

	    def create_snapshot(self, name, snap):
	    self.driver.snapshot_create(name, snap)
	    return {"vm": name, "snapshot": snap}

def list_snapshots(self, name):
return self.driver.snapshot_list(name)

def revert_snapshot(self, name, snap):
return self.driver.snapshot_revert(name, snap)

def open_console(self, name):
return self.driver.console(name)

def attach_disk(self, name, path, target):
return self.driver.attach_disk(name, path, target)

def attach_physical(self, name, host_dev, target="vdb"):
return self.driver.attach_physical_block(name, host_dev, target)

def detach_physical(self, name, target="vdb"):
return self.driver.detach_physical_block(name, target)

class CLI:
    @staticmethod
def usage():
print("""virt commands:
  list
  create --name NAME [--cpu N] [--mem MB] [--disk PATH] [--iso PATH] [--bridge BR]
  start NAME
  shutdown NAME [--force]
  reboot NAME
  snapshot create NAME SNAP
  snapshot list NAME
  snapshot revert NAME SNAP
  console NAME
  attach-disk NAME PATH TARGET
  attach-physical NAME /dev/sdX [TARGET]
  detach-physical NAME [TARGET]
  export NAME
""")

    @staticmethod
def run(argv):
if not argv:
CLI.usage(); return
        cmd = argv[0]
	       m = Manager()
	       try:
	       if cmd == "list":
		 print(m.list_vms())
		 elif cmd == "create":
		 args = CLI._parse_args(argv[1:])
		 vm = m.create_vm(args)
		 print("created", vm.name, vm.uuid)
		 elif cmd == "start":
		 m.start_vm(argv[1])
		 print("started", argv[1])
		 elif cmd == "shutdown":
                force = "--force" in argv
		 m.shutdown_vm(argv[1], force=force)
		 print("shutdown", argv[1])
		 elif cmd == "reboot":
		 m.reboot_vm(argv[1])
		 print("rebooted", argv[1])
		 elif cmd == "snapshot":
                sub = argv[1]
		 if sub == "create":
		 m.create_snapshot(argv[2], argv[3]); print("snapshot created")
		 elif sub == "list":
							print(m.list_snapshots(argv[2]))
							elif sub == "revert":
							m.revert_snapshot(argv[2], argv[3]); print("reverted")
 else:
   CLI.usage()
     elif cmd == "console":
     m.open_console(argv[1])
     elif cmd == "attach-disk":
     m.attach_disk(argv[1], argv[2], argv[3]); print("attached disk")
     elif cmd == "attach-physical":
						 target = argv[3] if len(argv) > 3 else "vdb"
											  m.attach_physical(argv[1], argv[2], target); print("attached physical")
											  elif cmd == "detach-physical":
																	 target = argv[2] if len(argv) > 2 else "vdb"
																						  m.detach_physical(argv[1], target); print("detached physical")
																						  elif cmd == "export":
																											print(Driver.dumpxml_def(argv[1]))
 else:
   CLI.usage()
     except Exception as e:
     print("error:", e)

    @staticmethod
     def _parse_args(pairs):
     args = {"name": None, "cpu":1, "memory_mb":512, "disk_path": None, "iso_path": None, "network_bridge": DEFAULT_BRIDGE}
        i = 0
      while i < len(pairs):
            p = pairs[i]
      if p == "--name":
      args["name"] = pairs[i+1]; i += 2
      elif p == "--cpu":
				   args["cpu"] = int(pairs[i+1]); i += 2
								    elif p == "--mem":
								    args["memory_mb"] = int(pairs[i+1]); i += 2
													   elif p == "--disk":
													   args["disk_path"] = pairs[i+1]; i += 2
																	     elif p == "--iso":
																	     args["iso_path"] = pairs[i+1]; i += 2
																					      elif p == "--bridge":
																					      args["network_bridge"] = pairs[i+1]; i += 2
 else:
                i += 1
        return args
```

		  ファイル: libexec/helpers/lock_device.py
```python
import subprocess
import shlex

		  def runcmd(cmd):
		  p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
		  return p.stdout.strip()

		  def ensure_device_unmounted(dev):
		  mounts = runcmd(f"lsblk -no MOUNTPOINT {dev}")
		  if mounts:
		  raise RuntimeError(f"Device {dev} is mounted: {mounts}")
# TODO: add multipath/LVM checks, exclusive lock if needed
    return True
```

		    ファイル: usr/share/doc/virt/README
```text
		      Virt package (Python) README
		      - Requires: libvirt/virsh, OVMF (for UEFI)
- Use 'virt' CLI in bin/ to manage VMs
		      - Physical device passthrough is dangerous: unmount device and backup data.
```

		    ファイル: README_install
```text
		    Install:
		    1. Place files under /usr/local/virt (or appropriate prefix)
2. Ensure bin/* are executable and in PATH
3. Put etc/virt/virt.conf to /etc/virt/virt.conf
4. Run as root: sbin/setup-ovmf <vmname> to prepare NVRAM
5. Use 'virt' CLI to create/start VMs. For physical passthrough, unmount host device first.
```

注意とセキュリティ:
- 物理ディスク透過はデータ消失リスクがあります。事前にバックアップを必ず行ってください。
- 実運用では Python の libvirt バインディング（python3-libvirt）を用いて直接 API を呼ぶ実装に置き換えることを推奨します（本例は外部コマンド virsh に依存）。
- root 権限が必要な操作（ディスク透過、define/start 等）があります。

必要なら:
- libvirt Python バインディング版へ変換。
- systemd ユニット、パッケージ化（deb/rpm）用スクリプトの追加。
どれを進めますか？
