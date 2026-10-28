# video_cut：桌球對打自動剪輯

自動找出桌球比賽影片中的每一分（對打），只保留對打片段並輸出剪輯版與時間碼清單。
剪輯規則見 [`table-tennis-rally-editing-rules.md`](table-tennis-rally-editing-rules.md)，
程式規格見 [`windows-auto-rally-editor-spec.md`](windows-auto-rally-editor-spec.md)，
開發進度見 [`development-progress.md`](development-progress.md)。

## 需求
- Python 3.10 以上
- ffmpeg / ffprobe（加入 PATH，或用環境變數 `FFMPEG_DIR` 指定所在資料夾）
- `pip install -r requirements.txt`

## 使用方式（第 1 階段，指令版）
```
python -m rally_editor info <影片檔> [<影片檔> ...] [--json]
```
印出影片長度、解析度、影格率、旋轉角度、色彩範圍、有無聲音（靜音音軌視為無聲音）。

## 資料夾結構
```
rally_editor/        程式本體
  cli.py             指令入口與子指令
  video_info.py      讀取影片資訊（ffprobe）
  ffmpeg_tools.py    尋找 ffmpeg / ffprobe
```
