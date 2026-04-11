# Supabase RLS Rollout Checklist (Single Recruiting Company)

Use this checklist when your whole system belongs to one recruiting company and you only need role-based access control.

## 0) Preconditions

1. Confirm backend-only usage of SUPABASE service_role key.
2. Confirm browser/frontend does not directly write recruiter tables.
3. Run in staging first.

## 1) Run migration SQL

1. Open Supabase SQL Editor.
2. Execute [supabase_rls_single_company_pack.sql](supabase_rls_single_company_pack.sql).
3. Confirm migration succeeds.

## 2) Seed user roles

Insert at least one admin first:

INSERT INTO public.recruiter_user_roles (user_id, role, is_active)
VALUES
  ('<admin-user-uuid>'::uuid, 'admin', true),
  ('<recruiter-user-uuid>'::uuid, 'recruiter', true),
  ('<reviewer-user-uuid>'::uuid, 'reviewer', true)
ON CONFLICT (user_id) DO UPDATE
SET role = EXCLUDED.role,
    is_active = EXCLUDED.is_active;

## 3) Validate role behavior

1. Admin can read/write/delete recruiter records.
2. Recruiter can read/write but cannot delete.
3. Reviewer can read records and can call app.set_candidate_review(...).
4. Authenticated user without role sees zero recruiter data.

## 4) App integration notes

1. Keep all writes server-side (service_role on backend only).
2. Reviewer updates should use app.set_candidate_review(...) instead of direct UPDATE.
3. Store auth user UUID and role mapping process in your admin onboarding flow.

## 5) Operational controls

1. Turn on PITR/backups in Supabase.
2. Rotate keys regularly.
3. Monitor permission denied errors and slow queries.
