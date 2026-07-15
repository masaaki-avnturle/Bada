"""コマンドラインインターフェース / CLI entry point.

サブコマンド:
    mayu check     <config>              設定を解析して要約を表示 (構文検証)
    mayu simulate  <config> --keys "..."  打鍵をシミュレートし変換結果を表示
    mayu keys                            既知のキー名一覧を表示
    mayu list-devices                    (Linux) 入力デバイス一覧
    mayu run       <config> [--device]   (Linux) 実キーフックを開始
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .config import ConfigError, parse_file
from .engine import Engine
from .keys import KeyTable

# 同梱設定の検索パス
_BUILTIN_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")


def _search_paths() -> list[str]:
    paths = [os.path.abspath(_BUILTIN_CONFIG_DIR)]
    env = os.environ.get("MAYU_PATH")
    if env:
        paths = env.split(os.pathsep) + paths
    return paths


def _load(config_path: str, keymap: str) -> Engine:
    cfg = parse_file(config_path, search_paths=_search_paths())
    return Engine(cfg, keymap=keymap)


# --- サブコマンド -----------------------------------------------------------
def cmd_check(args: argparse.Namespace) -> int:
    try:
        cfg = parse_file(args.config, search_paths=_search_paths())
    except ConfigError as e:
        print(f"設定エラー: {e}", file=sys.stderr)
        return 1
    print(f"OK: {args.config}")
    print(f"  キーマップ: {len(cfg.keymaps)}")
    for name, km in cfg.keymaps.items():
        parent = f" : {km.parent}" if km.parent else ""
        win = "  (window)" if km.window_regex else ""
        print(f"    - {name}{parent}{win}  ... {len(km.entries)} 定義")
    print(f"  修飾子割り当て:")
    for mod, keys in sorted(cfg.mod_assign.items()):
        if keys:
            print(f"    {mod}: {', '.join(sorted(keys))}")
    if cfg.substitutions:
        print(f"  def subst: {len(cfg.substitutions)} 件")
    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    from .backends.simulate import SimulateBackend, format_events, format_taps

    try:
        engine = _load(args.config, args.keymap)
    except ConfigError as e:
        print(f"設定エラー: {e}", file=sys.stderr)
        return 1
    backend = SimulateBackend(engine)
    outs = backend.translate_spec(args.keys)
    print(f"入力 : {args.keys}")
    if args.raw:
        print(f"出力 : {format_events(outs)}")
    else:
        print(f"出力 : {format_taps(outs)}")
    if engine.warnings:
        for w in engine.warnings:
            print(f"  ! {w}", file=sys.stderr)
    return 0


def cmd_keys(args: argparse.Namespace) -> int:
    table = KeyTable()
    names = table.all_names()
    if args.grep:
        names = [n for n in names if args.grep.lower() in n.lower()]
    width = max((len(n) for n in names), default=0)
    for n in names:
        print(f"{n:<{width}}  0x{table.code(n):02x} ({table.code(n)})")
    print(f"\n合計 {len(names)} キー", file=sys.stderr)
    return 0


def cmd_list_devices(args: argparse.Namespace) -> int:
    from .backends.linux_evdev import EvdevBackend

    try:
        devs = EvdevBackend.list_devices()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    for path, name in devs:
        print(f"{path}\t{name}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .backends.linux_evdev import EvdevBackend

    if sys.platform != "linux":
        print("run は Linux 専用です。他OSでは simulate を使ってください。", file=sys.stderr)
        return 1
    try:
        engine = _load(args.config, args.keymap)
    except ConfigError as e:
        print(f"設定エラー: {e}", file=sys.stderr)
        return 1
    backend = EvdevBackend(engine, device_path=args.device, grab=not args.no_grab)
    try:
        backend.run()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    except PermissionError:
        print("権限がありません。sudo で実行するか /dev/uinput の権限を確認してください。",
              file=sys.stderr)
        return 1
    return 0


# --- パーサ構築 -------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mayu",
        description="窓使いの憂鬱 — クロスプラットフォームなキー再割り当て",
    )
    p.add_argument("--version", action="version", version=f"mayu {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("check", help="設定ファイルを検証")
    pc.add_argument("config")
    pc.set_defaults(func=cmd_check)

    ps = sub.add_parser("simulate", help="打鍵変換をシミュレート")
    ps.add_argument("config")
    ps.add_argument("--keys", "-k", required=True, help='例: "C-b C-f a"')
    ps.add_argument("--keymap", default="Global", help="使用するキーマップ (既定 Global)")
    ps.add_argument("--raw", action="store_true", help="down/up をそのまま表示")
    ps.set_defaults(func=cmd_simulate)

    pk = sub.add_parser("keys", help="既知のキー名一覧")
    pk.add_argument("--grep", "-g", help="名前で絞り込み")
    pk.set_defaults(func=cmd_keys)

    pl = sub.add_parser("list-devices", help="(Linux) 入力デバイス一覧")
    pl.set_defaults(func=cmd_list_devices)

    pr = sub.add_parser("run", help="(Linux) 実キーフックを開始")
    pr.add_argument("config")
    pr.add_argument("--device", "-d", help="入力デバイスのパス (/dev/input/eventN)")
    pr.add_argument("--keymap", default="Global")
    pr.add_argument("--no-grab", action="store_true",
                    help="デバイスを grab しない (デバッグ用、元入力も残る)")
    pr.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
