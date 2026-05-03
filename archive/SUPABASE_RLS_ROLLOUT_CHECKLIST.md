# Supabase RLS Rollout Checklist (Production)

Use this checklist to safely move from broad authenticated access to strict company-scoped access.

## 0) Preconditions

1. Confirm backend-only usage of SUPABASE service_role key.
2. Confirm browser/frontend does not directly write recruiter tables.
3. Create a staging Supabase project and test there first.

## 1) Run migration SQL

1. Open Supabase SQL Editor.
2. Execute [supabase_rls_production_pack.sql](supabase_rls_production_pack.sql).
3. Ensure migration succeeds with no errors.

## 2) Backfill tenant scope

1. Choose your company UUID.
2. Backfill existing rows:

   UPDATE public.cv_intelligence
   SET company_id = '<company-uuid>'::uuid
   WHERE company_id IS NULL;

   UPDATE public.cv_filename_mapping
   SET company_id = '<company-uuid>'::uuid
   WHERE company_id IS NULL;

3. Validate no nulls remain:

   SELECT count(*) FROM public.cv_intelligence WHERE company_id IS NULL;
   SELECT count(*) FROM public.cv_filename_mapping WHERE company_id IS NULL;

## 3) Seed memberships

Add admins/recruiters/reviewers:

INSERT INTO public.company_memberships (company_id, user_id, role, is_active)
VALUES
  ('<company-uuid>'::uuid, '<auth-user-uuid-1>'::uuid, 'admin', true),
  ('<company-uuid>'::uuid, '<auth-user-uuid-2>'::uuid, 'recruiter', true),
  ('<company-uuid>'::uuid, '<auth-user-uuid-3>'::uuid, 'reviewer', true)
ON CONFLICT (company_id, user_id) DO UPDATE
SET role = EXCLUDED.role,
    is_active = EXCLUDED.is_active;

## 4) Enforce NOT NULL after backfill

ALTER TABLE public.cv_intelligence ALTER COLUMN company_id SET NOT NULL;
ALTER TABLE public.cv_filename_mapping ALTER COLUMN company_id SET NOT NULL;

## 5) Validate RLS behavior

1. As authenticated recruiter in company A:
   - Can read/write company A rows.
   - Cannot read company B rows.
2. As reviewer in company A:
   - Can read company A rows.
   - Can update override fields only through app.set_candidate_review(...).
3. As unrelated authenticated user:
   - Sees zero rows.

## 6) App integration notes

1. Keep all writes server-side (service_role on backend only).
2. Include company_id in write payloads to Supabase.
3. Reviewer updates should call app.set_candidate_review(...) instead of direct UPDATE.

## 7) Operational controls

1. Turn on PITR/backups in Supabase.
2. Add key rotation cadence.
3. Monitor failed-auth, permission denied, and high-latency queries.
4. Add audit logs for reviewer overrides and recruiter manual edits.

## 8) Rollback plan

If a production issue occurs:
1. Revert app traffic to backend-only service role paths.
2. Temporarily disable strict app-side enforcement (not SQL deletion first).
3. Restore from snapshot if data changes were unintended.
