"""用 ffprobe 讀取影片基本資訊。"""

import json
import subprocess
from dataclasses import dataclass, asdict
from fractions import Fraction

from rally_editor.ffmpeg_tools import find_tool


@dataclass
class VideoInfo:
    path: str
    duration: float          # 秒
    width: int               # 原始編碼寬度（未套用旋轉）
    height: int
    fps: float
    rotation: int            # 順時針需旋轉的角度：0 / 90 / 180 / 270
    has_audio: bool          # 有音軌且不是全靜音
    audio_track: bool        # 是否有音軌（可能是靜音軌）
    video_codec: str
    pix_fmt: str
    color_range: str         # "pc" = 全範圍（full range），"tv" = 有限範圍
    audio_codec: str | None
    audio_sample_rate: int | None

    @property
    def display_size(self) -> tuple[int, int]:
        """套用旋轉後實際顯示的寬高。"""
        if self.rotation in (90, 270):
            return self.height, self.width
        return self.width, self.height

    @property
    def is_full_range(self) -> bool:
        return self.color_range == "pc" or self.pix_fmt.startswith("yuvj")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["display_width"], d["display_height"] = self.display_size
        d["is_full_range"] = self.is_full_range
        return d


def _parse_rotation(stream: dict) -> int:
    rotation = 0.0
    for side in stream.get("side_data_list", []):
        if "rotation" in side:
            rotation = float(side["rotation"])
            break
    else:
        tag = stream.get("tags", {}).get("rotate")
        if tag is not None:
            # 舊式 rotate 標籤是順時針角度；display matrix 的 rotation 是逆時針，統一轉成順時針
            return int(float(tag)) % 360
    return int(round(-rotation)) % 360


def _parse_fps(stream: dict) -> float:
    for key in ("avg_frame_rate", "r_frame_rate"):
        value = stream.get(key, "0/0")
        try:
            fps = Fraction(value)
        except (ValueError, ZeroDivisionError):
            continue
        if fps > 0:
            return float(fps)
    return 0.0


SILENCE_DB = -80.0  # 最大音量低於此值視為靜音軌（例如螢幕錄影的空白音軌）


def audio_max_volume(path: str) -> float:
    """解碼整條音軌，回傳最大音量（dB）。只處理聲音，速度很快。"""
    cmd = [find_tool("ffmpeg"), "-hide_banner", "-nostats", "-i", path,
           "-vn", "-sn", "-dn", "-af", "volumedetect", "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in result.stderr.splitlines():
        if "max_volume:" in line:
            return float(line.split("max_volume:")[1].split()[0])
    return float("-inf")


def probe(path: str, check_silence: bool = True) -> VideoInfo:
    cmd = [find_tool("ffprobe"), "-v", "error", "-print_format", "json",
           "-show_format", "-show_streams", path]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 讀取失敗：{result.stderr.strip()}")
    data = json.loads(result.stdout)

    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError(f"檔案沒有影像軌：{path}")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    has_audio = audio is not None
    if has_audio and check_silence:
        has_audio = audio_max_volume(path) > SILENCE_DB

    duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
    return VideoInfo(
        path=path,
        duration=duration,
        width=int(video["width"]),
        height=int(video["height"]),
        fps=_parse_fps(video),
        rotation=_parse_rotation(video),
        has_audio=has_audio,
        audio_track=audio is not None,
        video_codec=video.get("codec_name", ""),
        pix_fmt=video.get("pix_fmt", ""),
        color_range=video.get("color_range", "unknown"),
        audio_codec=audio.get("codec_name") if audio else None,
        audio_sample_rate=int(audio["sample_rate"]) if audio and audio.get("sample_rate") else None,
    )
