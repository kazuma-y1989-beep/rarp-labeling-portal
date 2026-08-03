from datetime import datetime, timezone

import pandas as pd
from supabase import Client


def get_profile(client: Client, user_id: str) -> dict:
    result = (
        client.table("profiles")
        .select("id,researcher_name,role")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise RuntimeError("profilesテーブルに利用者情報がありません。")
    return result.data


def get_active_uploads(client: Client) -> pd.DataFrame:
    result = (
        client.table("uploads")
        .select(
            "id,user_id,researcher_name,case_id,video_name,original_filename,"
            "storage_path,row_count,file_hash,uploaded_at,is_deleted"
        )
        .eq("is_deleted", False)
        .order("uploaded_at", desc=True)
        .execute()
    )
    return pd.DataFrame(result.data or [])


def get_deleted_uploads(client: Client) -> pd.DataFrame:
    result = (
        client.table("uploads")
        .select(
            "id,user_id,researcher_name,case_id,original_filename,"
            "deleted_at,deleted_by"
        )
        .eq("is_deleted", True)
        .order("deleted_at", desc=True)
        .execute()
    )
    return pd.DataFrame(result.data or [])


def find_duplicate(client: Client, case_id: str, file_hash: str) -> bool:
    result = (
        client.table("uploads")
        .select("id")
        .eq("is_deleted", False)
        .or_(f"case_id.eq.{case_id},file_hash.eq.{file_hash}")
        .limit(1)
        .execute()
    )
    return bool(result.data)


def insert_upload(client: Client, payload: dict) -> None:
    client.table("uploads").insert(payload).execute()


def soft_delete_upload(client: Client, upload_id: str, deleted_by: str) -> None:
    client.table("uploads").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": deleted_by,
        }
    ).eq("id", upload_id).execute()
