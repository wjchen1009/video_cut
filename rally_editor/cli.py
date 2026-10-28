"""指令入口：python -m rally_editor <子指令> ..."""

import argparse
import json
import sys

from rally_editor import __version__
from rally_editor.video_info import probe


def _format_time(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def cmd_info(args: argparse.Namespace) -> int:
    for path in args.videos:
        info = probe(path)
        if args.json:
            print(json.dumps(info.to_dict(), ensure_ascii=False, indent=2))
            continue
        dw, dh = info.display_size
        print(f"檔案：{info.path}")
        print(f"  長度：{_format_time(info.duration)}（{info.duration:.3f} 秒）")
        print(f"  解析度：{info.width}×{info.height}（顯示 {dw}×{dh}）")
        print(f"  影格率：{info.fps:.3f} fps")
        print(f"  旋轉：{info.rotation}°")
        print(f"  影像：{info.video_codec}，{info.pix_fmt}，{'全範圍' if info.is_full_range else '有限範圍'}色彩")
        if info.has_audio:
            print(f"  聲音：有（{info.audio_codec}，{info.audio_sample_rate} Hz）")
        elif info.audio_track:
            print(f"  聲音：無（有 {info.audio_codec} 音軌但全靜音）")
        else:
            print("  聲音：無")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rally_editor", description="桌球對打自動剪輯（指令版）")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="印出影片基本資訊")
    p_info.add_argument("videos", nargs="+", help="影片檔路徑")
    p_info.add_argument("--json", action="store_true", help="以 JSON 輸出")
    p_info.set_defaults(func=cmd_info)
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 主控台顯示中文
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 1
