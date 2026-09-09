import io
from typing import Iterable

import pandas as pd

from portal.config import (
    OLD_REQUIRED_COLUMNS,
    NEW_REQUIRED_COLUMNS,
)


def read_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    last_error = None

    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
            )
        except Exception as exc:
            last_error = exc

    raise ValueError(
        "CSVを読み込めませんでした。"
        "UTF-8、UTF-8 BOM、またはShift-JISで保存してください。"
    ) from last_error


def detect_csv_format(df: pd.DataFrame) -> str:
    """
    CSV形式を判定する。

    old:
        従来の単一動画ラベリングCSV

    new:
        新しい単一動画・複数動画対応CSV
    """

    columns = set(df.columns)

    old_columns = set(OLD_REQUIRED_COLUMNS)
    new_columns = set(NEW_REQUIRED_COLUMNS)

    if new_columns.issubset(columns):
        return "new"

    if old_columns.issubset(columns):
        return "old"

    return "unknown"


def validate_dataframe(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    if df.empty:
        errors.append("CSVにデータ行がありません。")
        return errors

    csv_format = detect_csv_format(df)

    # =====================================================
    # CSV形式確認
    # =====================================================
    if csv_format == "unknown":
        old_missing = [
            column
            for column in OLD_REQUIRED_COLUMNS
            if column not in df.columns
        ]

        new_missing = [
            column
            for column in NEW_REQUIRED_COLUMNS
            if column not in df.columns
        ]

        errors.append(
            "CSV形式を確認してください。"
        )

        errors.append(
            "旧形式として不足している列："
            + ", ".join(old_missing)
        )

        errors.append(
            "新形式として不足している列："
            + ", ".join(new_missing)
        )

        return errors

    # =====================================================
    # case_id
    # =====================================================
    case_ids = (
        df["case_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    if case_ids.empty:
        errors.append("case_idが空です。")

    elif case_ids.nunique() != 1:
        errors.append(
            "1つのCSV内に複数のcase_idがあります。"
        )

    # =====================================================
    # phase
    # =====================================================
    phases = (
        df["phase"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if (phases == "").any():
        errors.append(
            "phaseが空欄の行があります。"
        )

    # =====================================================
    # 時間データ
    # =====================================================
    if csv_format == "old":

        start_sec = pd.to_numeric(
            df["start_sec"],
            errors="coerce",
        )

        end_sec = pd.to_numeric(
            df["end_sec"],
            errors="coerce",
        )

        start_name = "start_sec"
        end_name = "end_sec"

    else:

        # 新形式では複数動画をまたいだ
        # 「通算時間」を基準に判定する
        start_sec = pd.to_numeric(
            df["global_start_sec"],
            errors="coerce",
        )

        end_sec = pd.to_numeric(
            df["global_end_sec"],
            errors="coerce",
        )

        start_name = "global_start_sec"
        end_name = "global_end_sec"

    if start_sec.isna().any() or end_sec.isna().any():

        errors.append(
            f"{start_name}または"
            f"{end_name}に数値でない値があります。"
        )

    elif (end_sec <= start_sec).any():

        errors.append(
            f"{end_name}が"
            f"{start_name}以下の行があります。"
        )

    # =====================================================
    # 区間重複
    # =====================================================
    if (
        not start_sec.isna().any()
        and not end_sec.isna().any()
    ):

        ordered = (
            df.assign(
                _start=start_sec,
                _end=end_sec,
            )
            .sort_values("_start")
        )

        previous_end = (
            ordered["_end"]
            .shift(1)
        )

        overlap = (
            ordered["_start"]
            < previous_end
        ).fillna(False)

        if overlap.any():
            errors.append(
                "時間区間が重複している行があります。"
            )

    # =====================================================
    # 新形式のみ追加確認
    # =====================================================
    if csv_format == "new":

        start_video_index = pd.to_numeric(
            df["start_video_index"],
            errors="coerce",
        )

        end_video_index = pd.to_numeric(
            df["end_video_index"],
            errors="coerce",
        )

        if (
            start_video_index.isna().any()
            or end_video_index.isna().any()
        ):
            errors.append(
                "start_video_indexまたは"
                "end_video_indexに数値でない値があります。"
            )

        elif (
            end_video_index
            < start_video_index
        ).any():

            errors.append(
                "終了動画が開始動画より前になっている行があります。"
            )

        start_local_sec = pd.to_numeric(
            df["start_local_sec"],
            errors="coerce",
        )

        end_local_sec = pd.to_numeric(
            df["end_local_sec"],
            errors="coerce",
        )

        if (
            start_local_sec.isna().any()
            or end_local_sec.isna().any()
        ):
            errors.append(
                "start_local_secまたは"
                "end_local_secに数値でない値があります。"
            )

    return errors


def merged_csv_bytes(
    frames: Iterable[pd.DataFrame],
) -> bytes:

    frames = list(frames)

    if not frames:
        return b""

    merged = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    return merged.to_csv(
        index=False,
    ).encode("utf-8-sig")
