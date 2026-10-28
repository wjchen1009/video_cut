"""找出 ffmpeg / ffprobe 執行檔。"""

import os
import shutil


def find_tool(name: str) -> str:
    """回傳 ffmpeg 或 ffprobe 的路徑。優先使用環境變數 FFMPEG_DIR，其次 PATH。"""
    ffmpeg_dir = os.environ.get("FFMPEG_DIR")
    if ffmpeg_dir:
        for candidate in (name, name + ".exe"):
            path = os.path.join(ffmpeg_dir, candidate)
            if os.path.isfile(path):
                return path
    path = shutil.which(name)
    if path:
        return path
    raise FileNotFoundError(f"找不到 {name}，請安裝 ffmpeg 並加入 PATH，或設定環境變數 FFMPEG_DIR。")
