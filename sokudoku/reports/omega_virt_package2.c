以下は、先に作成した Omega スクリプト言語版 virt-manager 機能をパッケージ化した形で、典型的なディレクトリ構成（bin, sbin, lib, include, etc, usr）に配置するソースコード一式（代表的ファイル群）です。実運用用ではなく、Omega スクリプト言語のDSLとして統合するための雛形セットです。各ファイルは実行エントリやライブラリ、設定、ヘルパースクリプトを含みます。

注意: ファイルはテキストとして表現しています。必要なファイルを指定すれば個別に展開します。

-- package/bin/virt --
```omega
#!/usr/bin/env omega
# 実行ファイル: virt (CLI 前端)
import lib.virt.manager as Manager

main {
 args := ARGV
    Manager::CLI.run(args)
    }
```

-- package/bin/virtctl --
```omega
#!/usr/bin/env omega
# シンプルな管理ユーティリティ（非対話）
import lib.virt.manager as Manager

main {
 cmd := ARGV[0] || "help"
    args := ARGV
    Manager::CLI.run(args)
    }
```

-- package/sbin/setup-ovmf --
```omega
#!/usr/bin/env omega
# OVMF (UEFI) の初期 NVRAM ファイルを作る簡易セットアップスクリプト
# root 権限を想定
main {
 name := ARGV[0] || "default"
    dest_dir := "/var/lib/libvirt/qemu/nvram"
    system.exec("mkdir -p #{dest_dir}")
  # 実環境では OVMF ファイルの存在を確認してコピーする
    if system.exec("test -f /usr/share/OVMF/OVMF_CODE.fd && echo OK").strip == "OK"
	       system.exec("cp /usr/share/OVMF/OVMF_VARS.fd #{dest_dir}/#{name}_VARS.fd")
    puts "nvram prepared: #{dest_dir}/#{name}_VARS.fd"
      else
    puts "OVMF not found. Install OVMF package."
  end
      }
```

-- package/etc/virt/virt.conf --
```text
# virt-manager Omega package 設定
[global]
driver = libvirt
default_bridge = virbr0
default_image_dir = /var/lib/libvirt/images
ovmf_code = /usr/share/OVMF/OVMF_CODE.fd
ovmf_vars_dir = /var/lib/libvirt/qemu/nvram
allow_physical_passthrough = true
```

-- package/include/virt.h.omega --
```omega
# 公開 API ヘッダ（Omega 記法）
module Virt
  {
  # VM 管理 API シグネチャ
    def list_vms() -> Array
    def create_vm(params) -> VM
    def start_vm(id) -> VM
    def shutdown_vm(id, force: Bool) -> VM
    def reboot_vm(id) -> VM
    def create_snapshot(id, name) -> Snapshot
    def list_snapshots(id) -> Array
    def revert_snapshot(id, name) -> Bool
    def open_console(id, protocol: Symbol) -> Any
    def attach_disk(id, path, target) -> VM
    def attach_physical(id, host_dev, target='vdb') -> Bool
  }
```

-- package/lib/virt/manager.omega --
```omega
# ライブラリ: Virt Manager コア実装 (先の Manager クラスと driver を統合)
import etc.virt.virt_config as Config

Omega::VIRTMANAGER[virt]
{
  # 構造体定義
  struct VM { id,name,uuid,state,cpu,memory_mb,disk_paths,iso_paths,networks,created_at }
    struct Snapshot { vm_uuid,name,created_at,desc }

  # 設定ロード
 config := Config.load() rescue { default_bridge: "virbr0", image_dir: "/var/lib/libvirt/images" }

# ドライバ: 抽象化された system.exec ベースの実装
 vm.driver := {
   list() => system.exec("virsh list --all --uuid-name --name --state") |> parse_vm_list,
   define(xml) => system.exec("virsh define -") << xml,
   undefine(uuid) => system.exec("virsh undefine #{uuid}"),
   start(uuid) => system.exec("virsh start #{uuid}"),
   shutdown(uuid) => system.exec("virsh shutdown #{uuid}"),
   destroy(uuid) => system.exec("virsh destroy #{uuid}"),
   reboot(uuid) => system.exec("virsh reboot #{uuid}"),
   snapshot-create(uuid, name) => system.exec("virsh snapshot-create-as #{uuid} #{name}"),
   snapshot-list(uuid) => system.exec("virsh snapshot-list #{uuid}") |> parse_snapshot_list,
   snapshot-revert(uuid, name) => system.exec("virsh snapshot-revert #{uuid} #{name}"),
   console(uuid, protocol) => system.exec("virsh console #{uuid}"),
   attach-disk(uuid, path, target) => system.exec("virsh attach-disk #{uuid} #{path} #{target} --persistent"),
   detach-disk(uuid, target) => system.exec("virsh detach-disk #{uuid} #{target} --persistent"),
   attach-net(uuid, xml) => system.exec("virsh attach-interface #{uuid} --file - --live --config") << xml,
   export(uuid) => system.exec("virsh dumpxml #{uuid}")
 }

# 物理ディスク透過拡張 (安全チェックと attach XML)
  if Config.allow_physical_passthrough
	     vm.driver.extend({
		 attach-physical-disk(uuid, host_dev, target_dev='vdb', persistent=true) =>
		   if system.exec("lsblk -no MOUNTPOINT #{host_dev}").strip != ""
          raise "Device #{host_dev} is mounted; unmount first"
        end
        disk_xml = <<-XML
<disk type='block' device='disk'>
  <driver name='qemu' type='raw' io='native'/>
			      <source dev='#{host_dev}'/>
		   <target dev='#{target_dev}' bus='virtio'/>
</disk>
XML
        if persistent
          xml := system.exec("virsh dumpxml #{uuid}")
	    new_xml := xml.sub("</devices>", "#{disk_xml}\n</devices>")
	    system.exec("virsh define -") << new_xml
	    system.exec("virsh attach-device #{uuid} -") << disk_xml
	  else
	    system.exec("virsh attach-device #{uuid} -") << disk_xml
        end
        true
	      end,
	      detach-physical-disk(uuid, target_dev='vdb') =>
        disk_xml = <<-XML
<disk type='block' device='disk'>
	      <target dev='#{target_dev}' bus='virtio'/>
</disk>
XML
	      system.exec("virsh detach-device #{uuid} -") << disk_xml
        true
      end
	       })
  end

  # パーサ / ユーティリティ
	     def parse_vm_list(output) { vms := []; output.each_line{|l| if l =~ /([0-9a-f-]{36})\s+(\S+)\s+(\S+)/ then vms << VM{id:$2,name:$2,uuid:$1,state:($3=='running'? :running : :shutoff)} end}; vms }
  def parse_snapshot_list(output) { snaps := []; output.each_line{|l| if l.strip != "" then snaps << Snapshot{name:l.strip, created_at:Time.now} end}; snaps }

# Manager クラス定義 (主要メソッド)
  class Manager
    def list_vms() vm.driver.list() end
    def get_vm(id) list_vms().find{|v| v.uuid==id || v.name==id} end
								   def create_vm(params) xml := build_domain_xml(params); vm.driver.define(xml); VM{name:params.name, uuid:UUID.generate(), state: :shutoff, cpu:params.cpu, memory_mb:params.memory_mb, disk_paths:[params.disk_path], networks:[{bridge:params.network_bridge}]} end
																																								     def start_vm(id) vm := get_vm(id); raise "not found" unless vm; vm.driver.start(vm.uuid || vm.name); vm.state = :running; vm end
																																																								 def shutdown_vm(id, force:false) vm := get_vm(id); raise "not found" unless vm; force ? vm.driver.destroy(vm.uuid) : vm.driver.shutdown(vm.uuid); vm.state = :shutoff; vm end
																																																																													  def reboot_vm(id) vm := get_vm(id); raise "not found" unless vm; vm.driver.reboot(vm.uuid); vm.state = :running; vm end
																																																																																											     def create_snapshot(id,name,desc:"") vm := get_vm(id); vm.driver.snapshot-create(vm.uuid,name); Snapshot{vm_uuid:vm.uuid,name:name,desc:desc,created_at:Time.now} end
																																																																																																																 def list_snapshots(id) vm := get_vm(id); vm.driver.snapshot-list(vm.uuid) end
																																																																																																																					    def revert_snapshot(id,name) vm := get_vm(id); vm.driver.snapshot-revert(vm.uuid,name); true end
																																																																																																																																      def open_console(id, protocol: :vnc) vm := get_vm(id); vm.driver.console(vm.uuid, protocol) end
																																																																																																																																							       def attach_disk(id,path,target) vm := get_vm(id); vm.driver.attach-disk(vm.uuid,path,target); vm.disk_paths << path; vm end
																																																																																																																																																						      def attach_physical(id, host_dev, target='vdb') vm := get_vm(id); vm.driver.attach-physical-disk(vm.uuid, host_dev, target); vm.disk_paths << host_dev; vm end

    private
																																																																																																																																																																										def build_domain_xml(params)
																																																																																																																																																																										disk := "<disk type='file' device='disk'><driver name='qemu' type='qcow2'/><source file='#{params.disk_path}'/><target dev='vda' bus='virtio'/></disk>"
																																																																																																																																																																										iso := params.iso_path ? "<disk type='file' device='cdrom'><source file='#{params.iso_path}'/></disk>" : ""
      xml = <<-XML
<domain type='kvm'>
																																																																																																																																																																										<name>#{params.name}</name>
																																																																																																																																																																										<memory unit='MiB'>#{params.memory_mb}</memory>
																																																																																																																																																																										<vcpu>#{params.cpu}</vcpu>
  <os><type arch='x86_64'>hvm</type></os>
  <devices>
																																																																																																																																																																										#{disk}
  #{iso}
    <interface type='bridge'><source bridge='#{params.network_bridge}'/><model type='virtio'/></interface>
    <graphics type='vnc' autoport='yes'/>
  </devices>
</domain>
XML
      xml
    end
  end

  # CLI インターフェース提供
  module CLI
									   def run(args)
									   m := Manager.new
      case args[0]
									   when "list" then puts m.list_vms()
									   when "start" then puts m.start_vm(args[1])
									   when "shutdown" then puts m.shutdown_vm(args[1], force: args.include?("--force"))
									   when "create-physical-win" then params := parse_cli_args(args[1..-1]); puts m.create_vm_booting_physical_disk(params)
																		    when "attach-physical" then puts m.attach_physical(args[1], args[2], args[3] || 'vdb')
  else puts "usage: virt [list|start|shutdown|create-physical-win|attach-physical|...]" end
    end

	 def parse_cli_args(pairs)
	 params := {name:nil,cpu:4,memory_mb:8192,host_device:nil,iso_path:nil,network_bridge:config.default_bridge}
 i := 0
	 while i < pairs.length
        case pairs[i]
		     when "--name" then params[:name]=pairs[i+1]; i += 2
								    when "--cpu" then params[:cpu]=pairs[i+1].to_i; i +=2
														      when "--mem" then params[:memory_mb]=pairs[i+1].to_i; i +=2
																					      when "--host-device" then params[:host_device]=pairs[i+1]; i +=2
																													   when "--iso" then params[:iso_path]=pairs[i+1]; i +=2
																																			     when "--bridge" then params[:network_bridge]=pairs[i+1]; i +=2
  else i +=1
        end
      end
      params
    end
  end
	 }
```

-- package/lib/virt/config.omega (etc accessor) --
```omega
# etc ファイルを読み込む簡易ローダ
module etc.virt.virt_config
{
  def load()
    path := "/etc/virt/virt.conf"
    cfg := {}
  if File.exist?(path)
	   File.read(path).each_line{|l|
	     next if l.strip.start_with?("#") || l.strip == ""
			if l =~ /^(\w+)\s*=\s*(.*)$/
          cfg[$1.to_sym] = $2.strip
        end
				    }
    end
    cfg
  end
      }
```

-- package/usr/share/doc/virt/README.omega --
```text
Virt Omega package README
このパッケージは Omega スクリプト言語で書かれた仮想マシン管理ツールの雛形です。
主要機能:
 - VM 作成/起動/停止/再起動
 - スナップショット操作
 - コンソール接続
 - 物理ディスクのパススルー（注意: データ破壊の危険あり）
 設定: /etc/virt/virt.conf を編集してください。
```

-- package/libexec/helpers/lock_device.omega --
```omega
# デバイス安全処理ヘルパー: アンマウント確認とロック（簡易）
 def ensure_device_unmounted(dev)
 mounts = system.exec("lsblk -no MOUNTPOINT #{dev}").strip
  if mounts != ""
    raise "Device #{dev} is mounted (#{mounts}). Unmount before passthrough."
  end
  # 追加ロック処理等はここに実装
  true
end
```

-- package/README_install --
```text
   インストール手順 (例)
1. /usr/local/virt に展開
2. /usr/local/virt/bin 以下を PATH に追加
3. /etc/virt/virt.conf を確認・編集
4. root で /usr/local/virt/sbin/setup-ovmf <vmname> を実行して NVRAM を準備
5. 実機の物理ディスク透過はデータ損失のリスクがあるため必ずバックアップを取ること
```

   以上がパッケージの主要ファイル群（bin, sbin, lib, include, etc, usr）としての雛形です。個別ファイルの追加・内容修正、別のディレクトリや実際の libvirt バインディングに合わせた変換を行う場合は、どのファイルを詳細化するか指示してください。
