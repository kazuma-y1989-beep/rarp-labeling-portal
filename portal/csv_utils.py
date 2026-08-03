import io
from typing import Iterable

import pandas as pd

from portal.config import REQUIRED_COLUMNS


def read_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
        except Exception as exc:
            last_error = exc
    raise ValueError(
        "CSVを読み込めませんでした。UTF-8、UTF-8 BOM、またはShift-JISで保存してください。"
    ) from last_error


def validate_dataframe(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        errors.append("不足している列：" + ", ".join(missing))
        return errors

    if df.empty:
        errors.append("CSVにデータ行がありません。")
        return errors

    case_ids = df["case_id"].dropna().astype(str).str.strip()
    if case_ids.empty:
        errors.append("case_idが空です。")
    elif case_ids.nunique() != 1:
        errors.append("1つのCSV内に複数のcase_idがあります。")

    phases = df["phase"].fillna("").astype(str).str.strip()
    if (phases == "").any():
        errors.append("phaseが空欄の行があります。")

    start_sec = pd.to_numeric(df["start_sec"], errors="coerce")
    end_sec = pd.to_numeric(df["end_sec"], errors="coerce")
    if start_sec.isna().any() or end_sec.isna().any():
        errors.append("start_secまたはend_secに数値でない値があります。")
    elif (end_sec <= start_sec).any():
        errors.append("end_secがstart_sec以下の行があります。")

    if not start_sec.isna().any() and not end_sec.isna().any():
        ordered = df.assign(_start=start_sec, _end=end_sec).sort_values("_start")
        previous_end = ordered["_end"].shift(1)
        if (ordered["_start"] < previous_end).fillna(False).any():
            errors.append("時間区間が重複している行があります。")

    return errors


def merged_csv_bytes(frames: Iterable[pd.DataFrame]) -> bytes:
    frames = list(frames)
    if not frames:
        return b""
    merged = pd.concat(frames, ignore_index=True)
    return merged.to_csv(index=False).encode("utf-8-sig")
