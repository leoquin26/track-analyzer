-- Keyflow · SaaS Fase 2 — core schema
-- profiles (role per user), sets (saved playlists), feature_cache (shared,
-- service-role only). Mirrors the plan in docs/planning + the Fase 2 spec.

-- ---------------------------------------------------------------------------
-- profiles: 1:1 with auth.users. role is the plan; users must NOT be able to
-- change it themselves (column-level grants below), only the service role
-- (Gumroad webhook / license linking) can.
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  name text not null default '',
  role text not null default 'free' check (role in ('free', 'pro', 'lifetime')),
  license_key text,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "read own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "update own profile"
  on public.profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- Column-level lockdown: authenticated users may only update their name.
-- (role/license_key stay service-role-only even though the row policy allows
-- the UPDATE statement itself.)
revoke update on public.profiles from authenticated;
grant update (name) on public.profiles to authenticated;
grant select on public.profiles to authenticated;

-- Auto-provision a profile on signup, carrying the name from user metadata.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'name', split_part(new.email, '@', 1)));
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ---------------------------------------------------------------------------
-- sets: a user's saved playlists (order + params as JSON; no audio ever).
-- ---------------------------------------------------------------------------
create table if not exists public.sets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null,
  playlist jsonb not null,
  params jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists sets_user_idx on public.sets (user_id, created_at desc);

alter table public.sets enable row level security;

create policy "own sets: select" on public.sets for select using (auth.uid() = user_id);
create policy "own sets: insert" on public.sets for insert with check (auth.uid() = user_id);
create policy "own sets: update" on public.sets for update using (auth.uid() = user_id);
create policy "own sets: delete" on public.sets for delete using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- feature_cache: shared content-hash cache written/read by the API with the
-- service role. RLS enabled with NO policies = invisible to end users.
-- ---------------------------------------------------------------------------
create table if not exists public.feature_cache (
  content_hash text not null,
  duration real not null,
  features jsonb not null,
  created_at timestamptz not null default now(),
  primary key (content_hash, duration)
);

alter table public.feature_cache enable row level security;
