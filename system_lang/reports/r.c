以下は、先の Omega スクリプト言語風ソースに「裏の物理ハードディスク（Windows 11 を含む）をホスト上の Linux（Ubuntu）上の VM に透過させて起動する」機能（リピーター経由のブロックデバイスパススルー）を追加した改良版です。実運用ではホスト側で該当デバイスがアンマウント・ロックされていること、適切なパーミッション（libvirt グループや root）とリスク理解が必要です。ドライバの `attach-physical-disk` と `build_domain_xml_with_block` を追加します。

```omega
Omega::VIRTMANAGER[virt]
{
# 既存定義（VM, Snapshot, vm.driver 等）は省略（先のコードと同等）

# --- 物理ディスク透過（リピーター経由）用ドライバ拡張 ---
# 実装注記:
  #  - host_dev はホストのブロックデバイスパス例: /dev/sdb など
  #  - 実際は udev, multipath, LVM, dm-crypt 等の状況を確認すること
  vm.driver.extend({
  # 物理ブロックデバイスを VM に永続的に割当てる（libvirt define + <source dev='...'/>）
      attach-physical-disk(uuid, host_dev, target_dev='vdb', persistent: true) =>
    # 安全チェック（アンマウント確認）
	if system.exec("lsblk -no MOUNTPOINT #{host_dev}").strip != ""
      raise "Device #{host_dev} is mounted; unmount before passthrough"
    end
    # libvirt 用の disk XML 断片を組立てて attach
    disk_xml = <<-XML
<disk type='block' device='disk'>
  <driver name='qemu' type='raw' io='native'/>
		   <source dev='#{host_dev}'/>
	<target dev='#{target_dev}' bus='virtio'/>
  <shareable/>  <!-- 共有が必要な場合のみ -->
</disk>
XML
    # ライブでの attach と定義に persist を入れる
    if persistent
      # 一旦ドメインの定義 XML を取得、差し替えして再定義する簡易処理を想定
      xml := system.exec("virsh dumpxml #{uuid}")
	new_xml := xml.sub("</devices>", "#{disk_xml}\n</devices>")
	system.exec("virsh define -") << new_xml
      # ライブアタッチも行う
	system.exec("virsh attach-device #{uuid} -") << disk_xml
      else
	system.exec("virsh attach-device #{uuid} -") << disk_xml
    end
    return true
	  end,

	  detach-physical-disk(uuid, target_dev='vdb') =>
# detach by target dev (approx): libvirt detach-device requires same xml used to attach
# 簡易: build xml from target_dev and call detach
    disk_xml = <<-XML
<disk type='block' device='disk'>
	  <target dev='#{target_dev}' bus='virtio'/>
</disk>
XML
	  system.exec("virsh detach-device #{uuid} -") << disk_xml
    # さらに定義から削除する（再定義）
    # 実装簡略化のため呼び出し側で再定義を行うことを想定
    return true
  end
    })

# --- Windows 11 を物理ディスクから起動する VM 作成補助 ---
class Manager
  # 既存メソッドは省略

  # 物理ディスクを直接マウントして Windows 11 を起動する VM を作る
# params: name, cpu, memory_mb, host_device (例: /dev/sdb), network_bridge
  def create_vm_booting_physical_disk(params)
    # 安全チェック
  host_dev := params.host_device
    raise "host_device not specified" unless host_dev
    # デバイスがマウントされていないか確認
  if system.exec("lsblk -no MOUNTPOINT #{host_dev}").strip != ""
      raise "Device #{host_dev} is mounted; unmount it before passthrough"
    end
    # ディスク XML をブロックデバイスで生成（Windows 側ブート用）
	     xml := build_domain_xml_with_block(params, host_dev)
	     vm.driver.define(xml)
# 定義後、uuid を取得（簡易: virsh dumpxml から抽出）
    # 実際は libvirt API で返る UUID を使用する
	     uuid := system.exec("virsh dumpxml #{params.name} | xpath -q -e '/domain/@uuid' 2>/dev/null").strip rescue nil
    # ライブ起動
	     vm.driver.start(params.name)
	     return VM{name: params.name, uuid: uuid || UUID.generate(), state: :running, cpu: params.cpu, memory_mb: params.memory_mb, disk_paths: [host_dev], networks: [{bridge: params.network_bridge}] , created_at: Time.now}
  end

  private

    def build_domain_xml_with_block(params, host_dev)
    # Windows 向けに UEFI/OVMF と PCI/virtio ドライバ指定を想定。必要に応じて vnc/spice を調整
    iso := params.iso_path ? "<disk type='file' device='cdrom'><source file='#{params.iso_path}'/></disk>" : ""
  net_bridge := params.network_bridge || "virbr0"
    xml = <<-XML
<domain type='kvm'>
  <name>#{params.name}</name>
  <memory unit='MiB'>#{params.memory_mb}</memory>
  <vcpu>#{params.cpu}</vcpu>
  <os>
    <type arch='x86_64' machine='q35'>hvm</type>
    <loader readonly='yes' type='pflash'>/usr/share/OVMF/OVMF_CODE.fd</loader>
  <nvram>/var/lib/libvirt/qemu/nvram/#{params.name}_VARS.fd</nvram>
  </os>
  <features>
    <acpi/>
    <apic/>
    <hyperv>
      <relaxed state='on'/>
      <vapic state='on'/>
      <spinlocks state='on' retries='8191'/>
    </hyperv>
  </features>
  <devices>
    <!-- 物理ブロックデバイスを直接割当 -->
    <disk type='block' device='disk'>
      <driver name='qemu' type='raw' io='native'/>
						     <source dev='#{host_dev}'/>
      <target dev='vda' bus='virtio'/>
      <address type='drive' controller='0' bus='0' target='0' unit='0'/>
    </disk>
	 #{iso}
    <interface type='bridge'>
	 <source bridge='#{net_bridge}'/>
      <model type='virtio'/>
    </interface>
    <input type='tablet' bus='usb'/>
    <graphics type='spice' autoport='yes' listen='0.0.0.0'/>
    <video>
      <model type='qxl' vram='65536' heads='1'/>
    </video>
    <controller type='usb' index='0' model='qemu-xhci'/>
    <memballoon model='virtio'/>
  </devices>
</domain>
XML
    return xml
  end
end

# --- CLI 拡張 ---
interface CLI
	 {
  # 既存 help に以下を追加
  # virt create-physical-win --name NAME --cpu N --mem MB --host-device /dev/sdb [--bridge BR]

	   run(args) {
	   m := Manager.new
    case args[0]
    when "create-physical-win"
	   params := parse_args(args[1..-1])
	   vm := m.create_vm_booting_physical_disk(params)
      display vm
    when "attach-physical"
      # virt attach-physical NAME /dev/sdb vdb
	   m := Manager.new
	   m.vm.driver.attach-physical-disk(args[1], args[2], args[3] || 'vdb')
      puts "attached #{args[2]} to #{args[1]}"
    when "detach-physical"
	   m := Manager.new
	   m.vm.driver.detach-physical-disk(args[1], args[2] || 'vdb')
      puts "detached #{args[2]} from #{args[1]}"
	     else
      # 既存処理
      # ...
	       help()
    end
	}

	   parse_args(pairs)
	   {
	     params = {name: nil, cpu: 4, memory_mb:8192, host_device: nil, iso_path: nil, network_bridge: "virbr0"}
	   i := 0
	       while i < pairs.length
      case pairs[i]
			   when "--name" then params[:name] = pairs[i+1]; i += 2
									    when "--cpu" then params[:cpu] = pairs[i+1].to_i; i += 2
																when "--mem" then params[:memory_mb] = pairs[i+1].to_i; i += 2
																							  when "--host-device" then params[:host_device] = pairs[i+1]; i += 2
																															 when "--iso" then params[:iso_path] = pairs[i+1]; i += 2
																																					     when "--bridge" then params[:network_bridge] = pairs[i+1]; i += 2
	     else i += 1
      end
    end
    return params
		    }
	 }

# --- 実行時安全注意（コメント化） ---
# 注意: 物理ディスク透過はデータ損失・ファイルシステム破壊や Windows 側のライセンス/ドライバ問題を引き起こす可能性あり。
# ホストでデバイスのアンマウント、swap 単体解除、LVM/RAID の場合の対応、バックアップを確実に行うこと。

  }
```

必要なら次を行います：
- 実際の libvirt API（Python libvirt / Ruby libvirt）呼び出し版に変換。
- UEFI（OVMF）NVRAM ファイルの自動準備スクリプト追加。
- multipath / LVM / RAID 環境での安全な処理フロー（ロック・排他）の追加。

どれを先に進めますか？
