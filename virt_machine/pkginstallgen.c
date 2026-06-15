// pkginstallgen.c
// Safe libvirt-based VM creator: refuses raw physical devices.
// Usage: pkginstallgen <vm_name> <disk_image_path> <memory_mb> <vcpus>
// Compile: gcc -o pkginstallgen pkginstallgen.c `pkg-config --cflags --libs libvirt`

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libvirt/libvirt.h>
#include <sys/stat.h>

static int is_physical_path(const char *p) {
    if (!p) return 0;
    if (strncmp(p, "\\\\.\\", 4) == 0) return 1; // Windows raw device pattern
    if (strncmp(p, "/dev/", 5) == 0) return 1;    // Unix device
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <vm_name> <disk_image_path> <memory_mb> <vcpus>\n", argv[0]);
        return 1;
    }
    const char *vmname = argv[1];
    const char *disk = argv[2];
    int memory_mb = atoi(argv[3]);
    int vcpus = atoi(argv[4]);

    if (is_physical_path(disk)) {
        fprintf(stderr, "ERROR: physical device paths are not allowed. Provide a disk image file instead.\n");
        return 2;
    }

    struct stat st;
    if (stat(disk, &st) != 0 || !S_ISREG(st.st_mode)) {
        fprintf(stderr, "ERROR: disk image not found or not a regular file: %s\n", disk);
        return 3;
    }

    // Connect to system libvirt
    virConnectPtr conn = virConnectOpen(NULL);
    if (!conn) {
        fprintf(stderr, "ERROR: failed to connect to libvirt\n");
        return 4;
    }

    // Build minimal domain XML. Adjust OS/boot/devices as needed.
    char xml[8192];
    snprintf(xml, sizeof(xml),
        "<domain type='kvm'>"
          "<name>%s</name>"
          "<memory unit='MiB'>%d</memory>"
          "<vcpu>%d</vcpu>"
          "<os>"
            "<type arch='x86_64' machine='q35'>hvm</type>"
          "</os>"
          "<features><acpi/><apic/><pae/></features>"
          "<clock offset='utc'/>"
          "<on_poweroff>destroy</on_poweroff>"
          "<on_reboot>restart</on_reboot>"
          "<on_crash>restart</on_crash>"
          "<devices>"
            "<emulator>/usr/bin/qemu-system-x86_64</emulator>"
            "<disk type='file' device='disk'>"
              "<driver name='qemu' type='qcow2' cache='none' io='native'/>"
              "<source file='%s'/>"
              "<target dev='vda' bus='virtio'/>"
            "</disk>"
            "<interface type='network'>"
              "<source network='default'/>"
              "<model type='virtio'/>"
            "</interface>"
            "<graphics type='vnc' port='-1' autoport='yes'/>"
            "<console type='pty'/>"
            "<input type='tablet' bus='usb'/>"
            "<channel type='unix'><target type='virtio' name='org.qemu.guest_agent.0'/></channel>"
          "</devices>"
        "</domain>",
        vmname, memory_mb, vcpus, disk
    );

    // Define the domain (but do not autostart)
    virDomainPtr dom = virDomainDefineXML(conn, xml);
    if (!dom) {
        fprintf(stderr, "ERROR: failed to define domain\n");
        virConnectClose(conn);
        return 5;
    }

    // Start the domain
    if (virDomainCreate(dom) < 0) {
        fprintf(stderr, "ERROR: failed to start domain\n");
        virDomainFree(dom);
        virConnectClose(conn);
        return 6;
    }

    printf("Domain '%s' created and started successfully.\n", vmname);
    printf("Note: disk image used: %s\n", disk);
    printf("Safety: This tool refused raw physical devices. To use a physical partition, first create a read-only image.\n");

    // Cleanup
    virDomainFree(dom);
    virConnectClose(conn);
    return 0;
}
