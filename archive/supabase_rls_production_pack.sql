-- Production-safe Supabase RLS hardening pack for multi-tenant recruiter workflows.
--
-- What this migration does:
-- 1) Adds tenant scoping columns (company_id) to core tables.
-- 2) Creates membership table for user -> company -> role mapping.
-- 3) Replaces broad authenticated policies with strict company-scoped policies.
-- 4) Adds a reviewer-safe RPC for override updates (column-safe path).
--
-- IMPORTANT:
-- - Run in a staging project first.
-- - Backfill company_id for all existing rows before enforcing NOT NULL.
-- - Keep SUPABASE service_role key backend-only.

BEGIN;

-- Create schema namespace for helper functions.
CREATE SCHEMA IF NOT EXISTS app;

-- 1) Tenant columns
ALTER TABLE public.cv_intelligence
ADD COLUMN IF NOT EXISTS company_id uuid;

ALTER TABLE public.cv_filename_mapping
ADD COLUMN IF NOT EXISTS company_id uuid;

CREATE INDEX IF NOT EXISTS idx_cv_intelligence_company_id
ON public.cv_intelligence(company_id);

CREATE INDEX IF NOT EXISTS idx_cv_filename_mapping_company_id
ON public.cv_filename_mapping(company_id);

-- 2) Membership model
CREATE TABLE IF NOT EXISTS public.company_memberships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  user_id uuid NOT NULL,
  role text NOT NULL CHECK (role IN ('admin', 'recruiter', 'reviewer')),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (company_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_company_memberships_user_id
ON public.company_memberships(user_id);

CREATE INDEX IF NOT EXISTS idx_company_memberships_company_id
ON public.company_memberships(company_id);

-- Helper: companies available to current auth user.
CREATE OR REPLACE FUNCTION app.current_company_ids()
RETURNS SETOF uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT cm.company_id
  FROM public.company_memberships cm
  WHERE cm.user_id = auth.uid()
    AND cm.is_active = true;
$$;

REVOKE ALL ON FUNCTION app.current_company_ids() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.current_company_ids() TO authenticated;

-- Helper: role check in a tenant.
CREATE OR REPLACE FUNCTION app.user_has_role(p_company_id uuid, p_roles text[])
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.company_memberships cm
    WHERE cm.company_id = p_company_id
      AND cm.user_id = auth.uid()
      AND cm.is_active = true
      AND cm.role = ANY(p_roles)
  );
$$;

REVOKE ALL ON FUNCTION app.user_has_role(uuid, text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.user_has_role(uuid, text[]) TO authenticated;

-- 3) Backfill helper for mapping table (safe no-op for already populated rows)
UPDATE public.cv_filename_mapping m
SET company_id = c.company_id
FROM public.cv_intelligence c
WHERE m.anonymized_id = c.anonymized_id
  AND m.company_id IS NULL;

-- 4) Enable RLS
ALTER TABLE public.cv_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cv_filename_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_memberships ENABLE ROW LEVEL SECURITY;

-- 5) Remove broad policies (if present)
DROP POLICY IF EXISTS "Enable all access for authenticated users" ON public.cv_intelligence;
DROP POLICY IF EXISTS "Enable all access for authenticated users" ON public.cv_filename_mapping;

-- 6) cv_intelligence strict policies
DROP POLICY IF EXISTS cv_intelligence_select_company ON public.cv_intelligence;
CREATE POLICY cv_intelligence_select_company
ON public.cv_intelligence
FOR SELECT
TO authenticated
USING (company_id IN (SELECT app.current_company_ids()));

DROP POLICY IF EXISTS cv_intelligence_insert_recruiter_admin ON public.cv_intelligence;
CREATE POLICY cv_intelligence_insert_recruiter_admin
ON public.cv_intelligence
FOR INSERT
TO authenticated
WITH CHECK (app.user_has_role(company_id, ARRAY['admin', 'recruiter']));

DROP POLICY IF EXISTS cv_intelligence_update_recruiter_admin ON public.cv_intelligence;
CREATE POLICY cv_intelligence_update_recruiter_admin
ON public.cv_intelligence
FOR UPDATE
TO authenticated
USING (app.user_has_role(company_id, ARRAY['admin', 'recruiter']))
WITH CHECK (app.user_has_role(company_id, ARRAY['admin', 'recruiter']));

DROP POLICY IF EXISTS cv_intelligence_delete_admin ON public.cv_intelligence;
CREATE POLICY cv_intelligence_delete_admin
ON public.cv_intelligence
FOR DELETE
TO authenticated
USING (app.user_has_role(company_id, ARRAY['admin']));

-- 7) cv_filename_mapping strict policies via parent row company scope
DROP POLICY IF EXISTS cv_filename_mapping_select_company ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_select_company
ON public.cv_filename_mapping
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM public.cv_intelligence c
    WHERE c.anonymized_id = cv_filename_mapping.anonymized_id
      AND c.company_id IN (SELECT app.current_company_ids())
  )
);

DROP POLICY IF EXISTS cv_filename_mapping_insert_recruiter_admin ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_insert_recruiter_admin
ON public.cv_filename_mapping
FOR INSERT
TO authenticated
WITH CHECK (
  app.user_has_role(company_id, ARRAY['admin', 'recruiter'])
);

DROP POLICY IF EXISTS cv_filename_mapping_update_recruiter_admin ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_update_recruiter_admin
ON public.cv_filename_mapping
FOR UPDATE
TO authenticated
USING (app.user_has_role(company_id, ARRAY['admin', 'recruiter']))
WITH CHECK (app.user_has_role(company_id, ARRAY['admin', 'recruiter']));

DROP POLICY IF EXISTS cv_filename_mapping_delete_admin ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_delete_admin
ON public.cv_filename_mapping
FOR DELETE
TO authenticated
USING (app.user_has_role(company_id, ARRAY['admin']));

-- 8) membership visibility policies (users can view their own memberships)
DROP POLICY IF EXISTS company_memberships_select_own ON public.company_memberships;
CREATE POLICY company_memberships_select_own
ON public.company_memberships
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

DROP POLICY IF EXISTS company_memberships_admin_manage ON public.company_memberships;
CREATE POLICY company_memberships_admin_manage
ON public.company_memberships
FOR ALL
TO authenticated
USING (app.user_has_role(company_id, ARRAY['admin']))
WITH CHECK (app.user_has_role(company_id, ARRAY['admin']));

-- 9) Reviewer-safe function (column-safe update path)
CREATE OR REPLACE FUNCTION app.set_candidate_review(
  p_anonymized_id text,
  p_recruiter_override text,
  p_reviewer_notes text DEFAULT NULL
)
RETURNS public.cv_intelligence
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_row public.cv_intelligence;
BEGIN
  UPDATE public.cv_intelligence c
  SET recruiter_override = p_recruiter_override,
      reviewer_notes = p_reviewer_notes,
      reviewer_id = auth.uid()::text,
      reviewed_at = now()
  WHERE c.anonymized_id = p_anonymized_id
    AND app.user_has_role(c.company_id, ARRAY['admin', 'reviewer'])
  RETURNING * INTO v_row;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Not allowed or candidate not found';
  END IF;

  RETURN v_row;
END;
$$;

REVOKE ALL ON FUNCTION app.set_candidate_review(text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.set_candidate_review(text, text, text) TO authenticated;

COMMIT;

-- -----------------------------------------------------------------------------
-- POST-MIGRATION MANUAL STEPS (run intentionally, not automatic):
--
-- 1) Backfill company_id on existing rows:
--    UPDATE public.cv_intelligence
--    SET company_id = '<your-company-uuid>'::uuid
--    WHERE company_id IS NULL;
--
--    UPDATE public.cv_filename_mapping
--    SET company_id = '<your-company-uuid>'::uuid
--    WHERE company_id IS NULL;
--
-- 2) Enforce NOT NULL only after backfill is complete:
--    ALTER TABLE public.cv_intelligence ALTER COLUMN company_id SET NOT NULL;
--    ALTER TABLE public.cv_filename_mapping ALTER COLUMN company_id SET NOT NULL;
--
-- 3) Verify RLS:
--    SELECT tablename, rowsecurity FROM pg_tables
--    WHERE schemaname='public' AND tablename IN ('cv_intelligence','cv_filename_mapping','company_memberships');
-- -----------------------------------------------------------------------------
