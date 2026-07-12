-- Keyflow · SaaS Fase 2 — explicit table grants (incremento 3 fix)
--
-- Empirical finding on the local stack (supabase CLI, PG17): tables created in
-- migrations do NOT receive select/insert/update/delete for the API roles via
-- default privileges — only truncate/references/trigger/maintain came through.
-- So PostgREST returned 42501 when the FastAPI (service_role) read profiles,
-- and the sets RLS policies were unusable by authenticated users. State every
-- grant explicitly; on stacks that DO auto-grant these are harmless no-ops and
-- the 0001 role-column lockdown still applies.

-- Belt and braces: strip what nobody should hold through PostgREST.
revoke all on public.profiles from anon;
revoke all on public.sets from anon;
revoke all on public.feature_cache from anon, authenticated;
revoke truncate on public.profiles, public.sets from authenticated;

-- profiles: users read their own row (RLS scopes it); 0001 already reduced
-- their UPDATE to the name column. The service role (API role lookup, Gumroad
-- webhook flipping role) manages any profile.
grant select on public.profiles to authenticated;
grant select, insert, update, delete on public.profiles to service_role;

-- sets: owner CRUD through the 0001 RLS policies.
grant select, insert, update, delete on public.sets to authenticated;
grant select, insert, update, delete on public.sets to service_role;

-- feature_cache: service-only. RLS has no policies and service_role bypasses
-- RLS anyway — but BYPASSRLS does not skip table privileges, hence the grant.
grant select, insert, update, delete on public.feature_cache to service_role;
