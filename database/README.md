# CyberSentinel database

This folder contains PostgreSQL scripts for **Supabase**.

Do **not** use SQLite. The application is designed for hosted PostgreSQL.

## Setup

1. Create a Supabase project.
2. Open **SQL Editor**.
3. Run `schema.sql` (tables, indexes, RLS, auth trigger).
4. Run `seed.sql` (demo analysts metadata, assets, detection rules, sample threat intel).
5. Create Auth users that match seeded emails **or** use backend `DEMO_MODE` login (see root README).

## Auth users (recommended for production)

In **Authentication → Users**, create:

| Email | Suggested password | Role (user metadata) |
| --- | --- | --- |
| maya.chen@cybersentinel.demo | choose a strong password | admin |
| daniel.okonkwo@cybersentinel.demo | choose a strong password | senior_analyst |
| sofia.alvarez@cybersentinel.demo | choose a strong password | analyst |

Set user metadata `full_name` and `role` so the `handle_new_user` trigger can populate `profiles`. If the trigger created a profile with a different UUID than seed, either skip seed profiles or update `profiles.id` to match `auth.users.id`.

The FastAPI backend uses `SUPABASE_SERVICE_ROLE_KEY` and **bypasses RLS**. Row Level Security remains enabled so the anon key cannot read incident data from the browser.

## Notes

- `is_demo` columns let **Reset Demo** delete only demonstration records.
- Incident number `CS-1042` is reserved for the Demo Attack workflow.
- Threat intelligence rows are **sample / internal** indicators, not a live commercial feed.
