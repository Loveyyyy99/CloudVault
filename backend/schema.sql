-- CloudVault schema — run once in Supabase → SQL Editor
create extension if not exists pgcrypto;

create table if not exists public.users (
  id uuid primary key,                    -- same id as Supabase Auth user
  email text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.files (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  filename text not null,
  size bigint not null check (size >= 0),
  mime_type text not null default 'application/octet-stream',
  sha256 char(64) not null,
  description text,
  storage_key text,
  status text not null default 'PENDING'
    check (status in ('PENDING','UPLOADING','PARTIAL','VERIFIED','FAILED')),
  restore_status text check (restore_status in ('RESTORING','RESTORED')),
  created_at timestamptz not null default now(),
  unique (user_id, sha256)                -- deduplication
);

create table if not exists public.backups (
  id uuid primary key default gen_random_uuid(),
  file_id uuid not null references public.files(id) on delete cascade,
  provider text not null check (provider in ('b2','supabase')),
  status text not null default 'PENDING'
    check (status in ('PENDING','UPLOADING','VERIFIED','FAILED')),
  provider_hash char(64),
  uploaded_at timestamptz,
  verified_at timestamptz,
  error_message text,
  duration_ms integer,
  unique (file_id, provider)
);

create table if not exists public.backup_events (
  id uuid primary key default gen_random_uuid(),
  file_id uuid references public.files(id) on delete cascade,
  event_type text not null,
  message text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.simulation (
  user_id uuid primary key references public.users(id) on delete cascade,
  b2_down boolean not null default false,
  supabase_down boolean not null default false,
  updated_at timestamptz not null default now()
);

create index if not exists idx_files_user_created on public.files(user_id, created_at desc);
create index if not exists idx_backups_file on public.backups(file_id);
create index if not exists idx_events_file on public.backup_events(file_id, created_at desc);

-- The Flask backend connects with the database owner role (bypasses RLS).
-- Enabling RLS with no policies blocks all direct access through Supabase's public API.
alter table public.users enable row level security;
alter table public.files enable row level security;
alter table public.backups enable row level security;
alter table public.backup_events enable row level security;
alter table public.simulation enable row level security;
