APP_TITLE = "RARP AI Labeling Portal"
POINTS_PER_CASE = 3400
TARGET_CASES = 300

RESEARCHERS = ["田坂", "中野", "野村", "岡崎", "武藤", "鍵山"]


# =========================================================
# 旧ラベリングアプリのCSV形式
# =========================================================
OLD_REQUIRED_COLUMNS = [
    "case_id",
    "video_name",
    "video_path",
    "start_time",
    "end_time",
    "duration_sec",
    "start_sec",
    "end_sec",
    "start_frame",
    "end_frame",
    "phase",
    "note",
]


# =========================================================
# 新しい複数動画対応ラベリングアプリのCSV形式
# =========================================================
NEW_REQUIRED_COLUMNS = [
    "case_id",
    "source_mode",
    "source_path",
    "start_video_no",
    "start_video_name",
    "start_video_index",
    "start_local_time",
    "start_local_sec",
    "end_video_no",
    "end_video_name",
    "end_video_index",
    "end_local_time",
    "end_local_sec",
    "global_start_time",
    "global_start_sec",
    "global_end_time",
    "global_end_sec",
    "duration_sec",
    "fps",
    "start_frame_local",
    "end_frame_local",
    "phase",
    "note",
]


# 既存コードとの互換性維持用
REQUIRED_COLUMNS = OLD_REQUIRED_COLUMNS
