-- Run in Supabase SQL Editor after creating tables.
-- Fixes: permission denied for table users (code 42501)

grant usage on schema public to service_role;
grant all on all tables in schema public to service_role;
grant all on all sequences in schema public to service_role;

-- Optional: if you later use anon/authenticated clients directly
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on all tables in schema public to anon, authenticated;
