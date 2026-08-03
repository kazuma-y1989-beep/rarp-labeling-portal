-- RARP AI Labeling Portal Ver.2
-- Supabase > SQL Editor で実行します。再実行可能な構成です。

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  researcher_name text not null,
  role text not null default 'researcher'
    check (role in ('admin','researcher')),
  created_at timestamptz not null default now()
);

alter table public.profiles
drop constraint if exists profiles_researcher_name_check;

alter table public.profiles
add constraint profiles_researcher_name_check
check (
  researcher_name in
  ('管理者','田坂','中野','野村','岡崎','武藤','鍵山')
);

create table if not exists public.uploads (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id),
  researcher_name text not null,
  case_id text not null,
  video_name text,
  original_filename text not null,
  storage_path text not null unique,
  row_count integer not null default 0,
  file_hash text not null,
  uploaded_at timestamptz not null default now(),
  is_deleted boolean not null default false,
  deleted_at timestamptz,
  deleted_by uuid
);

alter table public.uploads
add column if not exists deleted_by uuid;

create unique index if not exists uploads_active_case_id_unique
on public.uploads(case_id)
where is_deleted = false;

create unique index if not exists uploads_active_file_hash_unique
on public.uploads(file_hash)
where is_deleted = false;

alter table public.profiles enable row level security;
alter table public.uploads enable row level security;

drop policy if exists "profiles_read_authenticated" on public.profiles;
create policy "profiles_read_authenticated"
on public.profiles for select to authenticated
using (true);

drop policy if exists "uploads_read_authenticated" on public.uploads;
create policy "uploads_read_authenticated"
on public.uploads for select to authenticated
using (true);

drop policy if exists "uploads_insert_own" on public.uploads;
create policy "uploads_insert_own"
on public.uploads for insert to authenticated
with check (auth.uid() = user_id);

drop policy if exists "uploads_update_own_or_admin" on public.uploads;
create policy "uploads_update_own_or_admin"
on public.uploads for update to authenticated
using (
  auth.uid() = user_id
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
)
with check (
  auth.uid() = user_id
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
);

insert into storage.buckets (id, name, public)
values ('label-csv', 'label-csv', false)
on conflict (id) do update set public = false;

drop policy if exists "label_csv_read_authenticated" on storage.objects;
create policy "label_csv_read_authenticated"
on storage.objects for select to authenticated
using (bucket_id = 'label-csv');

drop policy if exists "label_csv_insert_own_folder" on storage.objects;
create policy "label_csv_insert_own_folder"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'label-csv'
  and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "label_csv_delete_own_or_admin" on storage.objects;
create policy "label_csv_delete_own_or_admin"
on storage.objects for delete to authenticated
using (
  bucket_id = 'label-csv'
  and (
    (storage.foldername(name))[1] = auth.uid()::text
    or exists (
      select 1 from public.profiles p
      where p.id = auth.uid() and p.role = 'admin'
    )
  )
);

-- 管理者登録（メールアドレスは必要に応じて変更）
insert into public.profiles (id, researcher_name, role)
select id, '管理者', 'admin'
from auth.users
where lower(email) = lower('kazuma-y1989@hotmail.com')
on conflict (id) do update
set researcher_name = excluded.researcher_name,
    role = excluded.role;

-- 研究者は Authentication > Users で作成後、以下の形式で登録します。
-- insert into public.profiles (id, researcher_name, role)
-- select id, '田坂', 'researcher' from auth.users where lower(email)=lower('メールアドレス')
-- on conflict (id) do update set researcher_name=excluded.researcher_name, role=excluded.role;
