  /* pkggen.c
   Generate omega-script-package files under given prefix when executed.
   Usage: pkggen PREFIX
   If PREFIX is omitted, use "./package_out" as target root.
  */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>

  static void mkdir_p(const char *path) {
  char tmp[4096];
  char *p = NULL;
  size_t len;
  snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if (len == 0) return;
    if (tmp[len - 1] == '/') tmp[len - 1] = 0;
    for (p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = 0;
            if (mkdir(tmp, 0755) && errno != EEXIST) {
                fprintf(stderr, "mkdir %s: %s\n", tmp, strerror(errno));
                exit(1);
            }
            *p = '/';
        }
    }
    if (mkdir(tmp, 0755) && errno != EEXIST) {
        fprintf(stderr, "mkdir %s: %s\n", tmp, strerror(errno));
		exit(1);
		}
		}

		static void write_file(const char *path, const char *content, mode_t mode) {
		FILE *f;
		mkdir_p(path[0]=='/'? (char*)path : (char*)"");
    /* ensure parent directories exist */
    char buf[4096];
    strncpy(buf, path, sizeof(buf)-1); buf[sizeof(buf)-1]=0;
    char *slash = strrchr(buf, '/');
    if (slash) {
        *slash = 0;
        mkdir_p(buf);
    }
    f = fopen(path, "w");
    if (!f) {
        fprintf(stderr, "fopen %s: %s\n", path, strerror(errno));
        exit(1);
    }
    if (fputs(content, f) == EOF) {
        fprintf(stderr, "write %s: %s\n", path, strerror(errno));
        fclose(f);
        exit(1);
    }
    fclose(f);
    if (mode) chmod(path, mode);
}

int main(int argc, char **argv) {
    const char *prefix = argc > 1 ? argv[1] : "./package_out";
    char path[4096];

    /* directories */
    const char *dirs[] = {
        "/bin", "/sbin", "/lib/virt", "/libexec/helpers", "/include", "/etc/virt", "/usr/share/doc/virt", NULL
    };
    for (const char **d = dirs; *d; ++d) {
        snprintf(path, sizeof(path), "%s%s", prefix, *d);
        mkdir_p(path);
    }

    /* bin/virt */
    const char *bin_virt =
#!/usr/bin/env python3\n"
import sys\n"
from lib.virt.manager import CLI\n\n"
def main():\n"
    CLI.run(sys.argv[1:])\n\n"
if __name__ == \"__main__\":\n"
    main()\n";
    snprintf(path, sizeof(path), "%s/bin/virt", prefix);
    write_file(path, bin_virt, 0755);

    /* bin/virtctl */
    const char *bin_virtctl =
#!/usr/bin/env python3\n"
import sys\n"
from lib.virt.manager import CLI\n\n"
def main():\n"
    CLI.run(sys.argv[1:])\n\n"
if __name__ == \"__main__\":\n"
      "    main()\n";
    snprintf(path, sizeof(path), "%s/bin/virtctl", prefix);
    write_file(path, bin_virtctl, 0755);

    /* sbin/setup-ovmf */
    const char *sbin_setup =
#!/usr/bin/env python3\n"
import os, shutil, sys\n"
from pathlib import Path\n"
def main():\n"
    if os.geteuid() != 0:\n"
        print('run as root')\n"
        return\n"
    name = sys.argv[1] if len(sys.argv) > 1 else 'default'\n"
    dest_dir = Path('/var/lib/libvirt/qemu/nvram')\n"
    dest_dir.mkdir(parents=True, exist_ok=True)\n"
    code = Path('/usr/share/OVMF/OVMF_CODE.fd')\n"
    varsfile = Path('/usr/share/OVMF/OVMF_VARS.fd')\n"
    if code.exists() and varsfile.exists():\n"
        dst = dest_dir / f'{name}_VARS.fd'\n"
        shutil.copy(varsfile, dst)\n"
        print(f'nvram prepared: {dst}')\n"
    else:\n"
        print('OVMF not found. Install OVMF package.')\n"
if __name__ == '__main__':\n"
      "    main()\n";
    snprintf(path, sizeof(path), "%s/sbin/setup-ovmf", prefix);
    write_file(path, sbin_setup, 0755);

    /* etc/virt/virt.conf */
    const char *etc_conf =
# virt-manager package config\n"
[global]\n"
driver = libvirt\n"
default_bridge = virbr0\n"
default_image_dir = /var/lib/libvirt/images\n"
ovmf_code = /usr/share/OVMF/OVMF_CODE.fd\n"
ovmf_vars_dir = /var/lib/libvirt/qemu/nvram\n"
      "allow_physical_passthrough = true\n";
    snprintf(path, sizeof(path), "%s/etc/virt/virt.conf", prefix);
    write_file(path, etc_conf, 0644);

    /* include/virt.h.omega (API header placeholder) */
    const char *include_hdr =
# Omega Virt API (header placeholder)\n"
      "# Functions provided by the package are available in lib/virt/manager.py\n";
    snprintf(path, sizeof(path), "%s/include/virt.h.omega", prefix);
    write_file(path, include_hdr, 0644);

    /* libexec/helpers/lock_device.py */
    const char *lock_device =
import subprocess, shlex\n"
def runcmd(cmd):\n"
    p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)\n"
    return p.stdout.strip()\n"
def ensure_device_unmounted(dev):\n"
    mounts = runcmd(f'lsblk -no MOUNTPOINT {dev}')\n"
    if mounts:\n"
      "        raise RuntimeError(f'Device {dev} is mounted: {mounts}')\n    return True\n";
    snprintf(path, sizeof(path), "%s/libexec/helpers/lock_device.py", prefix);
    write_file(path, lock_device, 0644);

    /* lib/virt/config.py */
    const char *lib_config =
import configparser\nfrom pathlib import Path\n\ndef load(path='/etc/virt/virt.conf'):\n"
    cfg = {}\n    p = Path(path)\n"
    if not p.exists():\n"
        return cfg\n"
    cp = configparser.ConfigParser()\n"
    cp.read(path)\n"
    if 'global' in cp:\n"
        for k,v in cp['global'].items():\n"
            cfg[k]=v\n"
      "    return cfg\n";
    snprintf(path, sizeof(path), "%s/lib/virt/config.py", prefix);
    write_file(path, lib_config, 0644);

    /* lib/virt/manager.py (core) - simplified but functional wrapper to virsh */
    const char *lib_manager =
#!/usr/bin/env python3\n"
      "import subprocess, shlex, sys, os, uuid\nfrom pathlib import Path\nfrom datetime import datetime\nfrom lib.virt.config import load as load_config\nfrom libexec.helpers.lock_device import ensure_device_unmounted\n\nCONFIG = load_config()\nDEFAULT_BRIDGE = CONFIG.get('default_bridge','virbr0')\nIMAGE_DIR = Path(CONFIG.get('default_image_dir','/var/lib/libvirt/images'))\nALLOW_PHYS = CONFIG.get('allow_physical_passthrough','true').lower() in ('1','true','yes')\n\ndef runcmd(cmd, input_data=None):\n    p = subprocess.run(shlex.split(cmd), input=input_data, text=True, capture_output=True)\n    if p.returncode != 0:\n        raise RuntimeError(f'cmd failed: {cmd}\\n{p.stderr.strip()}')\n    return p.stdout\n\nclass Driver:\n    @staticmethod\n    def define(xml):\n        proc = subprocess.Popen(['virsh','define','-'], stdin=subprocess.PIPE, text=True)\n        proc.communicate(xml)\n        if proc.returncode != 0: raise RuntimeError('virsh define failed')\n    @staticmethod\n    def start(name): return runcmd(f\"virsh start {shlex.quote(name)}\")\n    @staticmethod\n    def shutdown(name): return runcmd(f\"virsh shutdown {shlex.quote(name)}\")\n    @staticmethod\n    def destroy(name): return runcmd(f\"virsh destroy {shlex.quote(name)}\")\n    @staticmethod\n    def reboot(name): return runcmd(f\"virsh reboot {shlex.quote(name)}\")\n    @staticmethod\n    def dumpxml(name): return runcmd(f\"virsh dumpxml {shlex.quote(name)}\")\n    @staticmethod\n    def attach_device(name, xml):\n        proc = subprocess.Popen(['virsh','attach-device',name,'-'], stdin=subprocess.PIPE, text=True)\n        proc.communicate(xml)\n        if proc.returncode != 0: raise RuntimeError('virsh attach-device failed')\n\n    @staticmethod\n    def attach_physical(name, host_dev, target='vdb'):\n        if not ALLOW_PHYS: raise RuntimeError('Physical passthrough disabled')\n        ensure_device_unmounted(host_dev)\n        disk_xml = f\"\"\"<disk type='block' device='disk'>\\n  <driver name='qemu' type='raw' io='native'/>\\n  <source dev='{host_dev}'/>\\n  <target dev='{target}' bus='virtio'/>\\n</disk>\"\"\"\n        xml = Driver.dumpxml(name)\n        if '</devices>' not in xml: raise RuntimeError('unexpected xml')\n        new_xml = xml.replace('</devices>', disk_xml + '\\n</devices>')\n        proc = subprocess.Popen(['virsh','define','-'], stdin=subprocess.PIPE, text=True)\n        proc.communicate(new_xml)\n        if proc.returncode != 0: raise RuntimeError('virsh define failed')\n        proc2 = subprocess.Popen(['virsh','attach-device',name,'-'], stdin=subprocess.PIPE, text=True)\n        proc2.communicate(disk_xml)\n        if proc2.returncode != 0: raise RuntimeError('virsh attach-device failed')\n\nclass Manager:\n    def __init__(self): self.driver = Driver()\n    def create_vm(self, name, cpu=1, mem=512, disk_path=None, iso=None, bridge=DEFAULT_BRIDGE):\n        disk_path = disk_path or str(IMAGE_DIR / f\"{name}.qcow2\")\n        disk_xml = f\"\"\"<disk type='file' device='disk'>\\n  <driver name='qemu' type='qcow2'/>\\n  <source file='{disk_path}'/>\\n  <target dev='vda' bus='virtio'/>\\n</disk>\"\"\"\n        iso_xml = f\"<disk type='file' device='cdrom'><source file='{iso}'/></disk>\" if iso else ''\n        xml = f\"\"\"<domain type='kvm'>\\n  <name>{name}</name>\\n  <memory unit='MiB'>{mem}</memory>\\n  <vcpu>{cpu}</vcpu>\\n  <devices>\\n    {disk_xml}\\n    {iso_xml}\\n    <interface type='bridge'><source bridge='{bridge}'/><model type='virtio'/></interface>\\n    <graphics type='vnc' autoport='yes'/>\\n  </devices>\\n</domain>\"\"\"\n        self.driver.define(xml)\n\n    def start_vm(self, name): self.driver.start(name)\n    def shutdown_vm(self, name, force=False): self.driver.destroy(name) if force else self.driver.shutdown(name)\n    def attach_physical(self, name, host_dev, target='vdb'): self.driver.attach_physical(name, host_dev, target)\n\n# Minimal CLI wrapper\nif __name__ == '__main__':\n    print('This is a packaged Omega-script virt manager (python). Use bin/virt or bin/virtctl to run CLI.')\n";
    snprintf(path, sizeof(path), "%s/lib/virt/manager.py", prefix);
    write_file(path, lib_manager, 0755);

    /* include placeholder (copy) */
    snprintf(path, sizeof(path), "%s/include/virt.h.omega", prefix);
    write_file(path, include_hdr, 0644);

    /* usr/share/doc/virt/README */
    const char *usr_readme =
      "Virt omega-package README\n- Requires libvirt/virsh, OVMF for UEFI\n- Use bin/virt to manage VMs\n- Physical passthrough is dangerous; unmount before use and backup data.\n";
    snprintf(path, sizeof(path), "%s/usr/share/doc/virt/README", prefix);
    write_file(path, usr_readme, 0644);

    printf("Package files generated under: %s\n", prefix);
    return 0;
}
