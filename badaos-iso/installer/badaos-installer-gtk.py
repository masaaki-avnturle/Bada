#!/usr/bin/python3
# -*- coding: utf-8 -*-
# =============================================================================
# badaos-installer-gtk — Ubuntu のインストーラ (Ubiquity) と同じ流れの GUI インストーラ
#
#   ようこそ → キーボードレイアウト → 無線 (Wi-Fi) → インストールの種類
#   (ディスクの割り当てを色付きの帯で表示) → どこに住んでいますか? → あなたの情報
#   → インストール (スライドショー + 進行状況) → 完了 (今すぐ再起動する)
#
#   実際のディスク操作は badaos-triboot-core.sh が行う:
#     [Windows][BADAVMBOOT (FAT32, ブートローダ)][BADAVMPRO (OS)][Linux / UBUNTU]
#   ディスク先頭 (MBR) と Windows の起動パーティションは書き換えない。
#   root で実行する (install-badaos-triboot ランチャが sudo で起動)。
# =============================================================================
import os
import re
import subprocess
import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, Pango  # noqa: E402

CORE = os.environ.get("BADAOS_CORE", "/usr/local/lib/badaos/badaos-triboot-core.sh")
DISKS = os.environ.get("BADAOS_DISKS", "/usr/local/lib/badaos/badaos-disks")
LOG = "/tmp/badaos-triboot.log"
ORANGE = "#E95420"

CSS = b"""
window { background: #f6f6f5; }
.header { background: #2c001e; }
.header label { color: #ffffff; font-size: 17pt; font-weight: bold; }
.page-title { font-size: 15pt; font-weight: bold; }
.hint { color: #555555; }
.dot { color: #c0c0c0; font-size: 14pt; }
.dot-on { color: #E95420; font-size: 14pt; }
.slide-title { font-size: 20pt; font-weight: bold; color: #ffffff; }
.slide-text { font-size: 12pt; color: #ffffff; }
.slide { background: #77216f; }
.error { color: #c7162b; }
.ok { color: #0e8420; }
button.suggested-action { background: #E95420; color: #ffffff; }
"""

COLORS = {"ntfs": (0.23, 0.44, 0.83), "vfat": (0.78, 0.64, 0.29), "bada": (0.91, 0.33, 0.13),
          "ubuntu": (0.47, 0.13, 0.44), "linux": (0.20, 0.60, 0.30), "other": (0.60, 0.60, 0.60)}

SLIDES = [
    ("Bada VM Pro OS へようこそ", "Ubuntu 22.04 をもとにした、速くて軽いデスクトップです。\nウィンドウマネージャは w9wm。"
     "Windows / Linux (Ubuntu) と共存して、起動メニューで選べます。"),
    ("日本語がすぐ使えます", "fcitx-mozc で日本語入力 (半角/全角 キー)。\n日本語 106/109 キーボード配列、Noto CJK フォント。"),
    ("文書作成と開発", "texlive-full (platex / uplatex / lualatex)、vim、emacs、\npython3、perl、build-essential (gcc / make) を最初から用意しています。"),
    ("インターネットとネットワーク", "有線 / Wi-Fi は NetworkManager (右上のアイコン)。\nssh、xinetd、NAT が使えます。"),
    ("ソフトウェアの追加", "Ubuntu と同じく apt でインストールできます:\n  sudo apt update\n  sudo apt install <パッケージ名>"),
    ("端末とプリンター", "mlterm / xterm / screen。\nCUPS でプリンターを追加して印刷できます。"),
]


def sh(cmd, **kw):
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)
    except OSError as e:
        return subprocess.CompletedProcess(cmd, 127, str(e), "")


def parse_plan(text):
    """badaos-triboot-core.sh の PLAN_ONLY 出力から (名前, fs, GiB, 注記) の列を取り出す"""
    rows, fw = [], ""
    m = re.search(r"起動方式:\s*(\S+(?: BIOS)?)", text)
    if m:
        fw = m.group(1)
    inlayout = False
    for line in text.splitlines():
        if line.startswith("--- 予定のレイアウト"):
            inlayout = True
            continue
        if not inlayout:
            continue
        mm = re.match(r"^  (.+?)\s+(\S+)\s+([\d.]+)(GiB|MiB)(?:\s+★\s*(.*))?$", line)
        if not mm:
            continue
        name, fs, num, unit, note = mm.groups()
        if "拡張区画" in name:
            continue
        gib = float(num) / (1024.0 if unit == "MiB" else 1.0)
        rows.append((name, fs, gib, note or ""))
    return rows, fw


def kind_of(name, fs):
    if "BADAVMBOOT" in name:
        return "vfat"
    if "BADAVMPRO" in name:
        return "bada"
    if "UBUNTU" in name:
        return "ubuntu"
    if fs == "ntfs":
        return "ntfs"
    if fs in ("ext4", "ext3", "ext2", "btrfs", "xfs"):
        return "linux"
    return "other"


class Installer(Gtk.Window):
    def __init__(self):
        super().__init__(title="インストール")
        self.set_default_size(900, 620)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", self.on_quit)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.st = {"lang": "ja", "kb": "jp", "disk": None, "size": 0, "shrink": False,
                   "tz": "Asia/Tokyo", "plan": "", "rows": [], "installing": False}
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(outer)
        hdr = Gtk.Box()
        hdr.get_style_context().add_class("header")
        self.title_lbl = Gtk.Label(xalign=0)
        self.title_lbl.set_margin_start(20)
        self.title_lbl.set_margin_top(12)
        self.title_lbl.set_margin_bottom(12)
        hdr.pack_start(self.title_lbl, True, True, 0)
        outer.pack_start(hdr, False, False, 0)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_margin_start(24)
        self.stack.set_margin_end(24)
        self.stack.set_margin_top(16)
        outer.pack_start(self.stack, True, True, 0)

        bar = Gtk.Box(spacing=8)
        bar.set_margin_start(24)
        bar.set_margin_end(24)
        bar.set_margin_top(10)
        bar.set_margin_bottom(14)
        self.btn_quit = Gtk.Button.new_with_mnemonic("終了(_Q)")
        self.btn_quit.connect("clicked", self.on_quit)
        self.btn_back = Gtk.Button.new_with_mnemonic("戻る(_B)")
        self.btn_back.connect("clicked", lambda *_: self.go(self.idx - 1))
        self.btn_next = Gtk.Button.new_with_mnemonic("続ける")
        self.btn_next.get_style_context().add_class("suggested-action")
        self.btn_next.connect("clicked", self.on_next)
        bar.pack_end(self.btn_next, False, False, 0)
        bar.pack_end(self.btn_back, False, False, 0)
        bar.pack_end(self.btn_quit, False, False, 0)
        outer.pack_start(bar, False, False, 0)

        self.dots = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        self.dots.set_margin_bottom(10)
        outer.pack_start(self.dots, False, False, 0)

        self.pages = [
            ("welcome", "ようこそ", self.page_welcome()),
            ("keyboard", "キーボードレイアウト", self.page_keyboard()),
            ("wifi", "無線", self.page_wifi()),
            ("updates", "アップデートと他のソフトウェア", self.page_updates()),
            ("type", "インストールの種類", self.page_type()),
            ("tz", "どこに住んでいますか?", self.page_tz()),
            ("user", "あなたの情報", self.page_user()),
            ("progress", "インストール", self.page_progress()),
        ]
        for name, _t, w in self.pages:
            self.stack.add_named(w, name)
        for _ in self.pages[:-1]:
            lb = Gtk.Label(label="●")
            self.dots.pack_start(lb, False, False, 0)
        self.idx = 0
        self.show_all()
        self.go(0)

    # ------------------------------------------------------------------ pages
    def page_box(self, heading=None):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        if heading:
            lb = Gtk.Label(label=heading, xalign=0)
            lb.set_line_wrap(True)
            b.pack_start(lb, False, False, 0)
        return b

    def page_welcome(self):
        b = Gtk.Box(spacing=24)
        sw = Gtk.ScrolledWindow()
        sw.set_size_request(260, -1)
        self.lang_list = Gtk.ListBox()
        for code, name in (("ja", "日本語"), ("en", "English")):
            row = Gtk.ListBoxRow()
            row.code = code
            lb = Gtk.Label(label=name, xalign=0)
            lb.set_margin_start(8)
            lb.set_margin_top(6)
            lb.set_margin_bottom(6)
            row.add(lb)
            self.lang_list.add(row)
        self.lang_list.select_row(self.lang_list.get_row_at_index(0))
        self.lang_list.connect("row-selected", lambda _l, r: r and self.st.update(lang=r.code))
        sw.add(self.lang_list)
        b.pack_start(sw, False, True, 0)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, valign=Gtk.Align.CENTER)
        t = Gtk.Label(xalign=0)
        t.set_markup("<span size='xx-large' weight='bold'>Bada VM Pro OS をインストール</span>")
        right.pack_start(t, False, False, 0)
        d = Gtk.Label(xalign=0)
        d.set_line_wrap(True)
        d.set_markup(
            "このコンピューターに <b>Bada VM Pro OS</b> をインストールします。\n\n"
            "• Windows の<b>後ろ</b>に、Bada VM Pro 専用ブートローダの <b>FAT32 パーティション (BADAVMBOOT)</b>\n"
            "  と <b>OS 本体 (BADAVMPRO)</b> を作ります (Windows と Linux の間)\n"
            "• Linux がまだ無いディスクでは、残りを <b>Ubuntu 用 (UBUNTU)</b> に割り当てます\n"
            "• 既存の Windows / Linux は消しません。ディスク先頭 (MBR) と Windows の\n"
            "  起動パーティションは書き換えません\n"
            "• <b>UEFI / Legacy BIOS</b> のどちらでも起動メニューで Bada VM Pro / Windows / Linux を選べます\n\n"
            "<span foreground='#c7162b'>⚠ 先に Windows の<b>高速スタートアップを無効</b>にし、BitLocker を一時停止し、\n"
            "大切なデータはバックアップしてください。</span>\n\n"
            "このまま試すには「終了」を押してください (ライブ環境を続けます)。")
        right.pack_start(d, False, False, 0)
        b.pack_start(right, True, True, 0)
        return b

    def page_keyboard(self):
        b = self.page_box()
        lb = Gtk.Label(label="キーボードレイアウトを選んでください:", xalign=0)
        b.pack_start(lb, False, False, 0)
        hb = Gtk.Box(spacing=16)
        self.kb_list = Gtk.ListBox()
        for code, name in (("jp", "日本語 — 日本語 (106/109 キーボード)"), ("us", "英語 (US)")):
            row = Gtk.ListBoxRow()
            row.code = code
            l2 = Gtk.Label(label=name, xalign=0)
            l2.set_margin_start(8)
            l2.set_margin_top(8)
            l2.set_margin_bottom(8)
            row.add(l2)
            self.kb_list.add(row)
        self.kb_list.select_row(self.kb_list.get_row_at_index(0))
        self.kb_list.connect("row-selected", self.on_kb)
        fr = Gtk.Frame()
        fr.add(self.kb_list)
        hb.pack_start(fr, True, True, 0)
        b.pack_start(hb, False, False, 0)
        self.kb_test = Gtk.Entry(placeholder_text="ここに入力してキーボードをテストしてください (例: @ \" : * ~ ¥)")
        b.pack_start(self.kb_test, False, False, 8)
        h = Gtk.Label(xalign=0)
        h.get_style_context().add_class("hint")
        h.set_markup("日本語入力は、インストール後に <b>半角/全角</b> キー (または Ctrl+Space) で切り替えます (fcitx-mozc)。")
        b.pack_start(h, False, False, 0)
        return b

    def on_kb(self, _l, row):
        if not row:
            return
        self.st["kb"] = row.code
        m, la = ("jp106", "jp") if row.code == "jp" else ("pc105", "us")
        subprocess.call(["setxkbmap", "-model", m, "-layout", la], stderr=subprocess.DEVNULL)

    def page_wifi(self):
        b = self.page_box()
        self.net_status = Gtk.Label(xalign=0)
        b.pack_start(self.net_status, False, False, 0)
        self.wifi_none = Gtk.RadioButton.new_with_label(None, "今はインターネットに接続しない (有線 LAN は自動で接続されます)")
        self.wifi_conn = Gtk.RadioButton.new_with_label_from_widget(self.wifi_none, "Wi-Fi ネットワークに接続する:")
        b.pack_start(self.wifi_none, False, False, 0)
        b.pack_start(self.wifi_conn, False, False, 0)
        self.wifi_store = Gtk.ListStore(str, int, str)
        tv = Gtk.TreeView(model=self.wifi_store)
        for i, t in enumerate(("ネットワーク (SSID)", "強度", "セキュリティ")):
            col = Gtk.TreeViewColumn(t, Gtk.CellRendererText(), text=i)
            col.set_expand(i == 0)
            tv.append_column(col)
        self.wifi_tv = tv
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(200)
        sw.add(tv)
        b.pack_start(sw, True, True, 0)
        hb = Gtk.Box(spacing=8)
        hb.pack_start(Gtk.Label(label="パスワード:"), False, False, 0)
        self.wifi_pw = Gtk.Entry(visibility=False)
        hb.pack_start(self.wifi_pw, True, True, 0)
        cb = Gtk.Button(label="接続")
        cb.connect("clicked", self.wifi_connect)
        hb.pack_start(cb, False, False, 0)
        rb = Gtk.Button(label="再検索")
        rb.connect("clicked", lambda *_: self.wifi_scan())
        hb.pack_start(rb, False, False, 0)
        b.pack_start(hb, False, False, 0)
        self.wifi_msg = Gtk.Label(xalign=0)
        b.pack_start(self.wifi_msg, False, False, 0)
        return b

    def net_refresh(self):
        def work():
            out = sh(["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "dev"]).stdout
            con = [ln.split(":") for ln in out.splitlines() if ":connected:" in ln or ":接続済み:" in ln]
            txt = ("<span foreground='#0e8420'>✔ インターネットに接続しています (%s)</span>" % ", ".join(
                "%s: %s" % (c[0], c[2]) for c in con if len(c) > 2)) if con else \
                "有線 LAN は未接続です。Wi-Fi を使う場合は下から選んでください。"
            GLib.idle_add(self.net_status.set_markup, txt)
        threading.Thread(target=work, daemon=True).start()

    def wifi_scan(self):
        self.wifi_msg.set_text("Wi-Fi を検索中…")

        def work():
            out = sh(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "yes"]).stdout
            seen, rows = set(), []
            for ln in out.splitlines():
                p = re.split(r"(?<!\\):", ln)
                if len(p) >= 3 and p[0] and p[0] not in seen:
                    seen.add(p[0])
                    try:
                        sig = int(p[1])
                    except ValueError:
                        sig = 0
                    rows.append((p[0].replace("\\:", ":"), sig, p[2] or "なし"))

            def done():
                self.wifi_store.clear()
                for r in sorted(rows, key=lambda r: -r[1]):
                    self.wifi_store.append(list(r))
                self.wifi_msg.set_text("" if rows else "Wi-Fi が見つかりません (Wi-Fi アダプタが無いか、無効です)")
            GLib.idle_add(done)
        threading.Thread(target=work, daemon=True).start()

    def wifi_connect(self, *_):
        m, it = self.wifi_tv.get_selection().get_selected()
        if not it:
            self.wifi_msg.set_text("ネットワークを選んでください")
            return
        self.wifi_conn.set_active(True)
        ssid, pw = m[it][0], self.wifi_pw.get_text()
        self.wifi_msg.set_text("%s に接続中…" % ssid)

        def work():
            cmd = ["nmcli", "dev", "wifi", "connect", ssid] + (["password", pw] if pw else [])
            r = sh(cmd)
            GLib.idle_add(self.wifi_msg.set_markup,
                          "<span foreground='#0e8420'>✔ 接続しました</span>" if r.returncode == 0 else
                          "<span foreground='#c7162b'>接続できません: %s</span>" % GLib.markup_escape_text(r.stdout.strip()[-200:]))
            self.net_refresh()
        threading.Thread(target=work, daemon=True).start()

    def page_updates(self):
        b = self.page_box()
        b.pack_start(Gtk.Label(label="最初からインストールされるもの:", xalign=0), False, False, 0)
        inc = Gtk.Label(xalign=0)
        inc.set_line_wrap(True)
        inc.set_markup("  Ubuntu 22.04 標準一式 (ubuntu-standard)・日本語環境 (fcitx-mozc)・w9wm\n"
                       "  vim / emacs・python3・perl・build-essential (gcc / make)・ssh・xinetd・screen・mlterm\n"
                       "  NetworkManager (有線 / Wi-Fi・NAT)・CUPS (プリンター)・apt")
        b.pack_start(inc, False, False, 0)
        b.pack_start(Gtk.Separator(), False, False, 6)
        b.pack_start(Gtk.Label(label="他のオプション", xalign=0), False, False, 0)
        self.cb_tex = Gtk.CheckButton()
        self.cb_tex.add(Gtk.Label(xalign=0))
        self.cb_tex.get_child().set_markup(
            "<b>texlive-full</b> (日本語 platex / uplatex / lualatex を含む TeX 一式) をインストールする\n"
            "<small>約 2.5GB をインターネット (NAT) からダウンロードします。インストール中に接続できない時は、\n"
            "インストール後にネットにつながった時点で自動でインストールされます。</small>")
        self.cb_tex.set_active(True)
        b.pack_start(self.cb_tex, False, False, 0)
        h = Gtk.Label(xalign=0)
        h.get_style_context().add_class("hint")
        h.set_text("他のソフトウェアも、インストール後に Ubuntu と同じく sudo apt install で追加できます。")
        b.pack_start(h, False, False, 8)
        return b

    def page_type(self):
        b = self.page_box()
        hb = Gtk.Box(spacing=8)
        hb.pack_start(Gtk.Label(label="インストール先のディスク:"), False, False, 0)
        self.disk_combo = Gtk.ComboBoxText()
        for ln in sh([DISKS]).stdout.splitlines():
            p = ln.split(None, 2)
            if p:
                dev = p[0] if p[0].startswith("/") else "/dev/" + p[0]
                self.disk_combo.append(dev, "%s  (%s)  %s" % (dev, p[1] if len(p) > 1 else "",
                                                                         p[2] if len(p) > 2 else ""))
        self.disk_combo.set_active(0)
        self.disk_combo.connect("changed", lambda *_: self.replan(reset=True))
        hb.pack_start(self.disk_combo, True, True, 0)
        b.pack_start(hb, False, False, 0)

        self.opt_mid = Gtk.RadioButton(label="")
        self.opt_mid.get_child().set_markup(
            "<b>Windows と Linux の間に Bada VM Pro をインストール</b>  (推奨)\n"
            "<small>Windows の後ろに BADAVMBOOT (FAT32, ブートローダ) と BADAVMPRO (OS) を作ります。"
            "Linux が無い時は残りを Ubuntu 用に。</small>")
        self.opt_shrink = Gtk.RadioButton.new_from_widget(self.opt_mid)
        self.opt_shrink.set_label("")
        self.opt_shrink.get_child().set_markup(
            "<b>Windows を縮小して Bada VM Pro をインストール</b>\n"
            "<small>空き領域が足りない時に、Windows (NTFS) の末尾を縮小して場所を作ります。</small>")
        self.opt_mid.connect("toggled", lambda *_: self.replan(reset=True))
        b.pack_start(self.opt_mid, False, False, 0)
        b.pack_start(self.opt_shrink, False, False, 0)

        hb2 = Gtk.Box(spacing=8)
        hb2.pack_start(Gtk.Label(label="Bada VM Pro の大きさ:"), False, False, 0)
        self.size_adj = Gtk.Adjustment(value=40, lower=31, upper=200, step_increment=1, page_increment=10)
        self.size_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.size_adj)
        self.size_scale.set_digits(0)
        self.size_scale.set_hexpand(True)
        self.size_scale.connect("format-value", lambda _s, v: "%d GiB" % v)
        self.size_scale.connect("value-changed", self.on_size)
        hb2.pack_start(self.size_scale, True, True, 0)
        b.pack_start(hb2, False, False, 0)

        self.bar = Gtk.DrawingArea()
        self.bar.set_size_request(-1, 64)
        self.bar.connect("draw", self.draw_bar)
        b.pack_start(self.bar, False, False, 0)
        self.legend = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=8,
                                  min_children_per_line=4, column_spacing=14, row_spacing=4)
        b.pack_start(self.legend, False, False, 0)
        self.plan_msg = Gtk.Label(xalign=0)
        self.plan_msg.set_line_wrap(True)
        b.pack_start(self.plan_msg, False, False, 0)
        ex = Gtk.Expander(label="詳細 (計画の全文)")
        self.plan_view = Gtk.Label(xalign=0, yalign=0, selectable=True)
        self.plan_view.modify_font(Pango.FontDescription("Monospace 9"))
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(110)
        sw.add(self.plan_view)
        ex.add(sw)
        b.pack_start(ex, True, True, 0)
        self._size_tm = None
        return b

    def on_size(self, *_):
        if getattr(self, "_setting", False):
            return
        if self._size_tm:
            GLib.source_remove(self._size_tm)
        self._size_tm = GLib.timeout_add(400, lambda: (self.replan(), False)[1])

    def run_plan(self, disk, size, shrink):
        env = dict(os.environ, TARGET_DISK=disk, BADA_SIZE_GB=str(size), PLAN_ONLY="1",
                   SHRINK_WINDOWS="1" if shrink else "0")
        r = subprocess.run(["bash", CORE], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return r.returncode, r.stdout

    def replan(self, reset=False):
        disk = self.disk_combo.get_active_id()
        if not disk:
            self.plan_msg.set_markup("<span foreground='#c7162b'>ディスクが見つかりません。</span>")
            self.st["rows"] = []
            self.bar.queue_draw()
            return
        shrink = self.opt_shrink.get_active()
        size = 0 if reset else int(self.size_adj.get_value())
        if reset and shrink:
            size = 40
        self.plan_msg.set_text("計画を作成中…")
        self.btn_next.set_sensitive(False)

        def work():
            rc, out = self.run_plan(disk, size, shrink)
            GLib.idle_add(self.plan_done, disk, size, shrink, rc, out, reset)
        threading.Thread(target=work, daemon=True).start()

    def plan_done(self, disk, size, shrink, rc, out, reset):
        rows, fw = parse_plan(out)
        self.st.update(disk=disk, shrink=shrink, plan=out, rows=rows if rc == 0 else [])
        self.plan_view.set_text(out.replace("PLAN_ONLY=1: ディスクは変更していません", ""))
        if rc != 0:
            err = next((ln for ln in out.splitlines() if ln.startswith("ERROR")), out.strip()[-300:])
            hint = ""
            if "空きがありません" in out and not shrink:
                hint = "\n→「Windows を縮小して Bada VM Pro をインストール」を選んでください。"
            self.plan_msg.set_markup("<span foreground='#c7162b'>%s</span>%s" % (
                GLib.markup_escape_text(err.replace("ERROR: ", "")), GLib.markup_escape_text(hint)))
            self.btn_next.set_sensitive(False)
        else:
            new = [r for r in rows if r[0].startswith("(新規)")]
            bada = sum(r[2] for r in new if kind_of(r[0], r[1]) in ("vfat", "bada"))
            ubu = sum(r[2] for r in new if kind_of(r[0], r[1]) == "ubuntu")
            self._setting = True
            if reset:
                avail = bada + ubu
                upper = max(31, int(avail - (20 if ubu else 0))) if not shrink else max(41, int(
                    sum(r[2] for r in rows if r[1] == "ntfs") + bada - 30))
                self.size_adj.set_upper(upper)
            self.size_adj.set_value(round(bada))
            self._setting = False
            self.st["size"] = size   # 0 = 既定 (空きを全部 / Linux が無い時は半分)
            msg = "起動方式: <b>%s</b>   Bada VM Pro: <b>%.1f GiB</b>" % (fw or "?", bada)
            if ubu:
                msg += "   Ubuntu 用: <b>%.1f GiB</b>" % ubu
            msg += "\nディスク先頭 (MBR) と Windows の起動パーティションは変更しません。"
            self.plan_msg.set_markup(msg)
            self.btn_next.set_sensitive(True)
        self.fill_legend()
        self.bar.queue_draw()
        return False

    def fill_legend(self):
        for c in self.legend.get_children():
            self.legend.remove(c)
        for name, fs, gib, _n in self.st["rows"]:
            k = kind_of(name, fs)
            col = COLORS[k]
            lb = Gtk.Label()
            lb.set_markup("<span foreground='#%02x%02x%02x'>■</span> %s\n<small>%s  %.1f GiB</small>" % (
                int(col[0] * 255), int(col[1] * 255), int(col[2] * 255),
                GLib.markup_escape_text(os.path.basename(name.replace("(新規)", ""))), fs, gib))
            self.legend.add(lb)
        self.legend.show_all()

    def draw_bar(self, w, cr):
        rows = self.st["rows"]
        W, H = w.get_allocated_width(), w.get_allocated_height()
        cr.set_source_rgb(0.85, 0.85, 0.85)
        cr.rectangle(0, 8, W, H - 16)
        cr.fill()
        tot = sum(max(r[2], 0.01) for r in rows)
        if not tot:
            return False
        # 小さい区画 (512MiB の FAT など) も見えるように最小幅をとる
        minw = 18
        widths = [max(minw, W * max(r[2], 0.01) / tot) for r in rows]
        scale = W / sum(widths)
        x = 0
        for (name, fs, gib, _n), wd in zip(rows, widths):
            wd *= scale
            col = COLORS[kind_of(name, fs)]
            cr.set_source_rgb(*col)
            cr.rectangle(x, 8, wd - 2, H - 16)
            cr.fill()
            if name.startswith("(新規)"):
                cr.set_source_rgb(1, 1, 1)
                cr.set_line_width(2)
                cr.rectangle(x + 2, 10, wd - 6, H - 20)
                cr.stroke()
            label = os.path.basename(name.replace("(新規)", ""))
            cr.set_source_rgb(1, 1, 1)
            cr.select_font_face("Sans")
            cr.set_font_size(11)
            ext = cr.text_extents(label)
            if ext.width < wd - 8:
                cr.move_to(x + (wd - ext.width) / 2, H / 2 + 4)
                cr.show_text(label)
            x += wd
        return False

    def page_tz(self):
        b = self.page_box()
        b.pack_start(Gtk.Label(label="タイムゾーン (時間帯) を選んでください:", xalign=0), False, False, 0)
        zones = []
        base = "/usr/share/zoneinfo"
        for reg in ("Africa", "America", "Antarctica", "Asia", "Atlantic", "Australia", "Europe", "Indian", "Pacific", "Etc"):
            for root, _d, files in os.walk(os.path.join(base, reg)):
                for f in files:
                    zones.append(os.path.relpath(os.path.join(root, f), base))
        zones = sorted(set(zones)) or ["Asia/Tokyo"]
        self.tz_combo = Gtk.ComboBoxText.new_with_entry()
        for z in zones:
            self.tz_combo.append(z, z)
        self.tz_combo.set_active_id("Asia/Tokyo")
        comp = Gtk.EntryCompletion()
        st = Gtk.ListStore(str)
        for z in zones:
            st.append([z])
        comp.set_model(st)
        comp.set_text_column(0)
        self.tz_combo.get_child().set_completion(comp)
        b.pack_start(self.tz_combo, False, False, 0)
        self.tz_time = Gtk.Label(xalign=0)
        self.tz_time.get_style_context().add_class("hint")
        b.pack_start(self.tz_time, False, False, 0)
        self.tz_combo.connect("changed", lambda *_: self.tz_show())
        h = Gtk.Label(xalign=0)
        h.set_line_wrap(True)
        h.get_style_context().add_class("hint")
        h.set_text("日本の場合は Asia/Tokyo (日本標準時) のままで構いません。")
        b.pack_start(h, False, False, 0)
        return b

    def tz_show(self):
        z = self.tz_combo.get_child().get_text().strip()
        if os.path.isfile("/usr/share/zoneinfo/" + z):
            t = sh(["date", "+%Y年%m月%d日 %H:%M"], env=dict(os.environ, TZ=z)).stdout.strip()
            self.tz_time.set_text("現在の時刻: " + t)
        else:
            self.tz_time.set_text("そのタイムゾーンは見つかりません")

    def page_user(self):
        b = self.page_box()
        g = Gtk.Grid(column_spacing=12, row_spacing=10)
        b.pack_start(g, False, False, 0)
        self.e_name = Gtk.Entry()
        self.e_host = Gtk.Entry()
        self.e_user = Gtk.Entry()
        self.e_pw = Gtk.Entry(visibility=False)
        self.e_pw2 = Gtk.Entry(visibility=False)
        self.pw_strength = Gtk.Label(xalign=0)
        self.pw_match = Gtk.Label(xalign=0)
        rows = [("あなたの名前:", self.e_name, None),
                ("コンピューターの名前:", self.e_host, "他のコンピューターと通信するときに使う名前です。"),
                ("ユーザー名の入力:", self.e_user, None),
                ("パスワードの入力:", self.e_pw, self.pw_strength),
                ("パスワードの確認:", self.e_pw2, self.pw_match)]
        for i, (t, e, hint) in enumerate(rows):
            g.attach(Gtk.Label(label=t, xalign=1), 0, i, 1, 1)
            e.set_hexpand(True)
            g.attach(e, 1, i, 1, 1)
            if isinstance(hint, str):
                hl = Gtk.Label(label=hint, xalign=0)
                hl.get_style_context().add_class("hint")
                g.attach(hl, 2, i, 1, 1)
            elif hint is not None:
                g.attach(hint, 2, i, 1, 1)
        self.e_host.set_text("badaos")
        self._host_auto = self._user_auto = True
        self.e_name.connect("changed", self.on_name)
        self.e_host.connect("changed", lambda *_: setattr(self, "_host_auto", self.e_host.has_focus() is False and self._host_auto))
        self.e_user.connect("changed", lambda *_: (setattr(self, "_user_auto", self.e_user.has_focus() is False and self._user_auto), self.check_user()))
        self.e_pw.connect("changed", lambda *_: self.check_user())
        self.e_pw2.connect("changed", lambda *_: self.check_user())
        self.e_host.connect("changed", lambda *_: self.check_user())
        self.r_auto = Gtk.RadioButton.new_with_label(None, "自動的にログインする")
        self.r_pw = Gtk.RadioButton.new_with_label_from_widget(self.r_auto, "ログイン時にパスワードを要求する")
        b.pack_start(self.r_auto, False, False, 0)
        b.pack_start(self.r_pw, False, False, 0)
        self.user_msg = Gtk.Label(xalign=0)
        b.pack_start(self.user_msg, False, False, 0)
        return b

    def on_name(self, *_):
        n = self.e_name.get_text()
        first = re.sub(r"[^a-z0-9]", "", (n.split() or [""])[0].lower())
        if self._user_auto:
            self.e_user.set_text(first)
        if self._host_auto:
            self.e_host.set_text((first + "-badaos") if first else "badaos")
        self.check_user()

    def check_user(self):
        pw, pw2 = self.e_pw.get_text(), self.e_pw2.get_text()
        if pw:
            score = (len(pw) >= 8) + bool(re.search(r"[A-Z]", pw)) + bool(re.search(r"[0-9]", pw)) + \
                bool(re.search(r"[^A-Za-z0-9]", pw))
            self.pw_strength.set_markup(["<span foreground='#c7162b'>短いパスワード</span>",
                                         "<span foreground='#c7162b'>弱いパスワード</span>",
                                         "まあまあのパスワード", "<span foreground='#0e8420'>良いパスワード</span>",
                                         "<span foreground='#0e8420'>強いパスワード</span>"][min(score, 4) if len(pw) >= 4 else 0])
        else:
            self.pw_strength.set_text("")
        self.pw_match.set_markup("" if not pw2 else ("<span foreground='#0e8420'>✔ 一致</span>" if pw == pw2 else
                                                       "<span foreground='#c7162b'>パスワードが一致しません</span>"))
        u, h = self.e_user.get_text(), self.e_host.get_text()
        ok_u = bool(re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", u)) and u not in ("root", "daemon", "bin", "sys", "nobody")
        ok_h = bool(re.fullmatch(r"[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?", h))
        msg = []
        if u and not ok_u:
            msg.append("ユーザー名は半角の小文字・数字・ - _ で、小文字から始めてください")
        if h and not ok_h:
            msg.append("コンピューターの名前は半角英数字と - だけにしてください")
        self.user_msg.set_markup("<span foreground='#c7162b'>%s</span>" % "\n".join(msg))
        ok = ok_u and ok_h and bool(pw) and pw == pw2
        if self.pages[self.idx][0] == "user":
            self.btn_next.set_sensitive(ok)
        return ok

    def page_progress(self):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        ev = Gtk.EventBox()
        ev.get_style_context().add_class("slide")
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, valign=Gtk.Align.CENTER)
        sb.set_margin_start(40)
        sb.set_margin_end(40)
        self.sl_title = Gtk.Label(xalign=0)
        self.sl_title.get_style_context().add_class("slide-title")
        self.sl_text = Gtk.Label(xalign=0)
        self.sl_text.set_line_wrap(True)
        self.sl_text.get_style_context().add_class("slide-text")
        sb.pack_start(self.sl_title, False, False, 0)
        sb.pack_start(self.sl_text, False, False, 0)
        ev.add(sb)
        ev.set_size_request(-1, 330)
        b.pack_start(ev, True, True, 0)
        self.pg_label = Gtk.Label(xalign=0)
        b.pack_start(self.pg_label, False, False, 0)
        self.pg = Gtk.ProgressBar()
        b.pack_start(self.pg, False, False, 0)
        self.slide_i = 0
        return b

    def next_slide(self):
        t, x = SLIDES[self.slide_i % len(SLIDES)]
        self.sl_title.set_text(t)
        self.sl_text.set_text(x)
        self.slide_i += 1
        return self.st["installing"]

    # ------------------------------------------------------------ navigation
    def go(self, i):
        i = max(0, min(i, len(self.pages) - 1))
        self.idx = i
        name, title, _w = self.pages[i]
        self.stack.set_visible_child_name(name)
        self.title_lbl.set_text(title)
        for k, d in enumerate(self.dots.get_children()):
            d.get_style_context().remove_class("dot-on")
            d.get_style_context().remove_class("dot")
            d.get_style_context().add_class("dot-on" if k <= i else "dot")
        self.btn_back.set_sensitive(0 < i < len(self.pages) - 1)
        self.btn_next.set_sensitive(True)
        self.btn_next.set_label({"welcome": "インストール", "type": "インストール(_I)"}.get(name, "続ける"))
        self.btn_next.set_use_underline(True)
        self.btn_next.set_visible(name != "progress")
        self.btn_back.set_visible(name != "progress")
        self.btn_quit.set_visible(name != "progress")
        if name == "wifi":
            self.net_refresh()
            self.wifi_scan()
        elif name == "type":
            if not self.st["rows"]:
                self.replan(reset=True)
            else:
                self.btn_next.set_sensitive(bool(self.st["rows"]))
        elif name == "tz":
            self.tz_show()
        elif name == "user":
            self.check_user()
            self.e_name.grab_focus()

    def on_next(self, *_):
        name = self.pages[self.idx][0]
        if name == "type" and not self.confirm_disk():
            return
        if name == "tz":
            z = self.tz_combo.get_child().get_text().strip()
            if not os.path.isfile("/usr/share/zoneinfo/" + z):
                return
            self.st["tz"] = z
        if name == "user":
            if not self.check_user():
                return
            self.go(self.idx + 1)
            self.start_install()
            return
        self.go(self.idx + 1)

    def confirm_disk(self):
        rows = [r for r in self.st["rows"] if r[0].startswith("(新規)")]
        txt = "以下のデバイスのパーティションテーブルが変更されます:\n    %s\n\n以下のパーティションがフォーマットされます:\n" % self.st["disk"]
        for name, fs, gib, _n in rows:
            if fs in ("vfat", "ext4"):
                txt += "    %s  (%s, %.1f GiB)\n" % (name.replace("(新規)", ""), fs, gib)
        if self.st["shrink"]:
            txt += "\n<b>Windows (NTFS) の末尾を縮小します。</b>\n"
        txt += "\n既存の Windows / Linux のパーティションは消しません。\nディスク先頭 (MBR) は書き換えません。"
        d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.NONE, text="変更をディスクに書き込みますか?")
        d.format_secondary_markup(GLib.markup_escape_text(txt).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>"))
        d.add_button("戻る", Gtk.ResponseType.CANCEL)
        btn = d.add_button("続ける", Gtk.ResponseType.OK)
        btn.get_style_context().add_class("suggested-action")
        r = d.run()
        d.destroy()
        return r == Gtk.ResponseType.OK

    def start_install(self):
        self.st["installing"] = True
        self.next_slide()
        GLib.timeout_add_seconds(9, self.next_slide)
        GLib.timeout_add(300, lambda: (self.pg.pulse() if self.pg.get_fraction() == 0 else None,
                                        self.st["installing"])[1])
        env = dict(os.environ, TARGET_DISK=self.st["disk"], BADA_SIZE_GB=str(self.st["size"]),
                   SHRINK_WINDOWS="1" if self.st["shrink"] else "0",
                   NEW_HOST=self.e_host.get_text(), NEW_USER=self.e_user.get_text(),
                   NEW_PASS=self.e_pw.get_text(), NEW_FULLNAME=self.e_name.get_text(),
                   NEW_AUTOLOGIN="1" if self.r_auto.get_active() else "0",
                   NEW_TZ=self.st["tz"], NEW_KBLAYOUT=self.st["kb"],
                   NEW_TEXLIVE="1" if self.cb_tex.get_active() else "0")
        self.pg_label.set_text("インストールを準備しています…")

        def work():
            with open(LOG, "w") as log:
                p = subprocess.Popen(["bash", CORE], env=env, stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1)
                for line in p.stdout:
                    line = line.rstrip("\n")
                    if line.startswith("# "):
                        GLib.idle_add(self.pg_label.set_text, line[2:])
                    elif line.strip().isdigit():
                        GLib.idle_add(self.pg.set_fraction, min(int(line) / 100.0, 1.0))
                rc = p.wait()
            GLib.idle_add(self.finished, rc)
        threading.Thread(target=work, daemon=True).start()

    def finished(self, rc):
        self.st["installing"] = False
        if rc == 0:
            self.pg.set_fraction(1.0)
            self.pg_label.set_text("インストールが完了しました")
            extra = ""
            if any(kind_of(r[0], r[1]) == "ubuntu" for r in self.st["rows"]):
                extra = ("\n\nUbuntu 用パーティション (UBUNTU, ext4) を作りました。Ubuntu を入れるときは"
                         "「それ以外」を選び、UBUNTU を ext4 / マウントポイント「/」に、"
                         "「ブートローダをインストールするデバイス」に同じ UBUNTU パーティションを選んでください。"
                         "その後 Bada VM Pro で sudo update-grub を実行すると起動メニューに Ubuntu が出ます。")
            d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.INFO,
                                  buttons=Gtk.ButtonsType.NONE, text="インストールが完了しました")
            d.format_secondary_text("新しいシステムを使うには、USB メモリを抜いてからコンピューターを再起動してください。\n"
                                    "起動メニュー「Bada VM Pro」から Bada VM Pro / Windows / Linux を選べます。" + extra)
            d.add_button("試用を続ける", 1)
            btn = d.add_button("今すぐ再起動する", 2)
            btn.get_style_context().add_class("suggested-action")
            r = d.run()
            d.destroy()
            if r == 2:
                subprocess.call(["systemctl", "reboot"])
            Gtk.main_quit()
        else:
            try:
                tail = "".join(open(LOG, encoding="utf-8", errors="replace").readlines()[-18:])
            except OSError:
                tail = ""
            self.pg_label.set_text("インストールに失敗しました")
            d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                                  buttons=Gtk.ButtonsType.CLOSE, text="インストールに失敗しました (終了コード %d)" % rc)
            d.format_secondary_text("ログの末尾:\n\n%s\n全文: %s\n\n画面が乱れる場合は起動メニューの"
                                    "「インストール: テキスト画面」もお試しください。" % (tail, LOG))
            d.run()
            d.destroy()
            Gtk.main_quit()
        return False

    def on_quit(self, *_):
        if self.st["installing"]:
            return True
        Gtk.main_quit()
        return False


if __name__ == "__main__":
    os.environ.setdefault("LANG", "ja_JP.UTF-8")
    Installer()
    Gtk.main()
