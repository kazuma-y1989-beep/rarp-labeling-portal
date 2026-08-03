import hashlib
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import Client

from portal.config import POINTS_PER_CASE, RESEARCHERS, TARGET_CASES
from portal.csv_utils import merged_csv_bytes, read_csv_bytes, validate_dataframe
from portal.db import (
    find_duplicate,
    get_active_uploads,
    get_deleted_uploads,
    insert_upload,
    soft_delete_upload,
)


def _ranking(active_uploads: pd.DataFrame) -> pd.DataFrame:
    master = pd.DataFrame({"研究者名": RESEARCHERS})

    if active_uploads.empty:
        counts = pd.DataFrame(columns=["研究者名", "登録症例数"])
    else:
        counts = (
            active_uploads.groupby("researcher_name", as_index=False)
            .size()
            .rename(
                columns={
                    "researcher_name": "研究者名",
                    "size": "登録症例数",
                }
            )
        )

    ranking = master.merge(counts, on="研究者名", how="left").fillna(0)
    ranking["登録症例数"] = ranking["登録症例数"].astype(int)
    ranking["獲得ポイント"] = ranking["登録症例数"] * POINTS_PER_CASE
    ranking = ranking.sort_values(
        ["登録症例数", "研究者名"],
        ascending=[False, True],
    ).reset_index(drop=True)
    ranking.index = ranking.index + 1
    ranking.index.name = "順位"
    return ranking


def render_dashboard(client: Client, profile: dict) -> None:
    active = get_active_uploads(client)
    ranking = _ranking(active)

    if profile["role"] == "admin":
        my_cases = 0
        my_points = 0
        my_rank_text = "管理者"
    else:
        row = ranking[ranking["研究者名"] == profile["researcher_name"]]
        my_cases = int(row["登録症例数"].iloc[0]) if not row.empty else 0
        my_points = my_cases * POINTS_PER_CASE
        my_rank_text = f'{int(row.index[0])} / {len(RESEARCHERS)}' if not row.empty else "-"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("登録症例数", my_cases)
    c2.metric("獲得ポイント", f"{my_points:,}")
    c3.metric("現在順位", my_rank_text)
    c4.metric("全体症例数", len(active))

    st.subheader("ランキング")
    st.dataframe(ranking, use_container_width=True)

    st.subheader("全体進捗")
    progress = min(len(active) / TARGET_CASES, 1.0)
    st.progress(progress)
    st.caption(f"{len(active)} / {TARGET_CASES} 症例")


def render_upload(client: Client, profile: dict) -> None:
    if profile["role"] == "admin":
        st.info("管理者アカウントからもCSVを登録できますが、ランキング対象にはなりません。")

    uploaded = st.file_uploader(
        "ラベリングアプリから出力したCSVを選択してください",
        type=["csv"],
        accept_multiple_files=False,
    )

    if uploaded is None:
        return

    file_bytes = uploaded.getvalue()
    try:
        df = read_csv_bytes(file_bytes)
    except ValueError as exc:
        st.error(str(exc))
        return

    errors = validate_dataframe(df)
    if errors:
        st.error("CSV形式を確認してください。")
        for error in errors:
            st.write("・" + error)
        return

    case_id = str(df["case_id"].iloc[0]).strip()
    video_name = str(df["video_name"].iloc[0]).strip()
    duration = float(pd.to_numeric(df["end_sec"], errors="coerce").max())

    a, b, c, d = st.columns(4)
    a.metric("症例ID", case_id)
    b.metric("動画名", video_name)
    c.metric("ラベル行数", len(df))
    d.metric("最終時刻", f"{duration / 60:.1f}分")

    st.dataframe(df.head(30), use_container_width=True)

    if st.button("このCSVを登録する", type="primary", use_container_width=True):
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        if find_duplicate(client, case_id, file_hash):
            st.error("同じ症例IDまたは同一内容のCSVがすでに登録されています。")
            return

        safe_name = "".join(
            char if char.isalnum() or char in "._-" else "_"
            for char in uploaded.name
        )
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        storage_path = f'{profile["id"]}/{timestamp}_{safe_name}'

        try:
            client.storage.from_("label-csv").upload(
                storage_path,
                file_bytes,
                {"content-type": "text/csv", "upsert": "false"},
            )
            insert_upload(
                client,
                {
                    "user_id": profile["id"],
                    "researcher_name": profile["researcher_name"],
                    "case_id": case_id,
                    "video_name": video_name,
                    "original_filename": uploaded.name,
                    "storage_path": storage_path,
                    "row_count": int(len(df)),
                    "file_hash": file_hash,
                },
            )
        except Exception as exc:
            try:
                client.storage.from_("label-csv").remove([storage_path])
            except Exception:
                pass
            st.error(f"登録に失敗しました：{exc}")
            return

        st.success(f"{case_id}を登録しました。")
        st.rerun()


def render_files(client: Client, profile: dict) -> None:
    active = get_active_uploads(client)
    if active.empty:
        st.info("登録済みのCSVはありません。")
        return

    if profile["role"] == "admin":
        visible = active
        st.caption("管理者として全研究者の登録ファイルを表示しています。")
    else:
        visible = active[active["user_id"] == profile["id"]]

    if visible.empty:
        st.info("自分が登録したCSVはありません。")
        return

    for _, row in visible.iterrows():
        title = f'{row["case_id"]}｜{row["researcher_name"]}｜{row["original_filename"]}'
        with st.expander(title):
            st.write(f'動画名：{row["video_name"]}')
            st.write(f'ラベル行数：{row["row_count"]}')
            st.write(f'登録日時：{row["uploaded_at"]}')
            confirm = st.checkbox(
                "削除することを確認",
                key=f'confirm_delete_{row["id"]}',
            )
            if confirm and st.button(
                "このCSVを削除",
                key=f'delete_{row["id"]}',
                type="secondary",
            ):
                soft_delete_upload(client, row["id"], profile["id"])
                st.success("削除しました。集計とランキングから除外されました。")
                st.rerun()


def render_admin(client: Client, profile: dict) -> None:
    if profile["role"] != "admin":
        st.error("管理者専用です。")
        return

    active = get_active_uploads(client)
    deleted = get_deleted_uploads(client)
    ranking = _ranking(active)

    st.subheader("研究者別集計")
    st.dataframe(ranking, use_container_width=True)

    summary_bytes = ranking.reset_index().to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "研究者別集計をダウンロード",
        data=summary_bytes,
        file_name=f'researcher_summary_{datetime.now().strftime("%Y%m%d")}.csv',
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("全CSV結合")
    if active.empty:
        st.info("結合対象のCSVはありません。")
    else:
        frames = []
        try:
            for _, row in active.iterrows():
                raw = client.storage.from_("label-csv").download(row["storage_path"])
                frame = read_csv_bytes(raw)
                frame["uploaded_by"] = row["researcher_name"]
                frame["uploaded_at"] = row["uploaded_at"]
                frame["source_file"] = row["original_filename"]
                frames.append(frame)

            combined = merged_csv_bytes(frames)
            st.download_button(
                "全CSVを1つに結合してダウンロード",
                data=combined,
                file_name=f'rarp_all_labels_{datetime.now().strftime("%Y%m%d")}.csv',
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"結合CSVを作成できませんでした：{exc}")

    st.subheader("有効ファイル一覧")
    if not active.empty:
        st.dataframe(
            active[
                [
                    "researcher_name",
                    "case_id",
                    "video_name",
                    "original_filename",
                    "row_count",
                    "uploaded_at",
                ]
            ],
            use_container_width=True,
        )

    st.subheader("削除履歴")
    if deleted.empty:
        st.caption("削除履歴はありません。")
    else:
        st.dataframe(deleted, use_container_width=True)
