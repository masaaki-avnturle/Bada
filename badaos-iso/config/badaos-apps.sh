#!/bin/sh
# badaos-apps — Ubuntu 向けアプリを「簡単に」導入する GUI (zenity チェックリスト)。
# NAT/DHCP で公式ミラーへ到達できる前提。選んだものを sudo apt で導入する。
export DISPLAY="${DISPLAY:-:0}"
export LANG=ja_JP.UTF-8
command -v zenity >/dev/null 2>&1 || { xmessage -center "zenity が必要です" 2>/dev/null; exit 1; }

xhost +si:localuser:root >/dev/null 2>&1 || true

# 一覧: FALSE(初期チェック無) パッケージ名 説明
SEL="$(zenity --list --checklist --width=640 --height=560 \
  --title="Bada VM Pro OS — Ubuntu アプリを導入" \
  --text="導入したいアプリにチェックを入れて「導入」を押してください（NAT/apt で取得）。" \
  --column="選択" --column="パッケージ" --column="内容" \
  FALSE vim-gtk3       "Vim (GUI/クリップボード対応)" \
  FALSE emacs          "Emacs エディタ" \
  FALSE neovim         "Neovim エディタ" \
  FALSE geany          "軽量 IDE (Geany)" \
  FALSE firefox-esr    "Firefox 系ブラウザ (無ければ falkon 推奨)" \
  FALSE falkon         "Falkon Web ブラウザ (Qt)" \
  FALSE libreoffice    "LibreOffice オフィス一式" \
  FALSE gimp           "GIMP 画像編集" \
  FALSE inkscape       "Inkscape ベクター描画" \
  FALSE vlc            "VLC メディアプレーヤ" \
  FALSE audacity       "Audacity 音声編集" \
  FALSE thunderbird    "Thunderbird メール" \
  FALSE filezilla      "FileZilla FTP" \
  FALSE gnome-terminal "GNOME 端末" \
  FALSE pcmanfm        "ファイルマネージャ (PCManFM)" \
  FALSE mousepad       "テキストエディタ (Mousepad)" \
  FALSE evince         "PDF ビューア (Evince)" \
  FALSE git            "git バージョン管理" \
  FALSE build-essential "C/C++ ビルド環境 (gcc/make)" \
  FALSE python3-pip    "Python パッケージ管理 (pip)" \
  FALSE fcitx-mozc     "日本語入力 fcitx-mozc (未導入時)" \
  --separator=' ')"
rc=$?
xhost -si:localuser:root >/dev/null 2>&1 || true
[ "$rc" = "0" ] || exit 0
[ -n "$SEL" ] || { zenity --info --width=380 --text="何も選択されませんでした。"; exit 0; }

# apt update → 選択パッケージを導入 (進捗をパイプ表示)
(
  echo "# パッケージ一覧を更新中 (apt update)…"
  sudo apt-get update -y 2>&1 | sed 's/^/# /'
  echo "# 導入中: $SEL"
  # shellcheck disable=SC2086
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $SEL 2>&1 | sed 's/^/# /'
  echo "# 完了"
) | zenity --progress --pulsate --auto-close --no-cancel --width=560 \
     --title="Ubuntu アプリ導入" --text="準備中…"

if [ "${PIPESTATUS:-0}" = "0" ] || true; then
  zenity --info --width=460 --title="完了" \
    --text="導入処理が終わりました。\n選択したアプリ: $SEL\n\n端末から起動できます (例: vim / emacs / libreoffice)。"
fi
