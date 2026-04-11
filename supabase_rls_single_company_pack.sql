-- Production-safe Supabase RLS hardening pack for a single recruiting company.
--
-- What this migration does:
-- 1) Creates a user role table (admin/recruiter/reviewer).
-- 2) Enables strict role-based RLS on recruiter tables.
-- 3) Removes broad authenticated policies.
-- 4) Adds a reviewer-safe RPC for override updates.
--
-- IMPORTANT:
-- - Run in staging first.
-- - Keep SUPABASE service_role key backend-only.

BEGIN;

-- Helper schema for security functions.
CREATE SCHEMA IF NOT EXISTS app;
GRANT USAGE ON SCHEMA app TO authenticated;

-- 1) Single-company membership model (no tenant key required)
CREATE TABLE IF NOT EXISTS public.recruiter_user_roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL UNIQUE,
  role text NOT NULL CHECK (role IN ('admin', 'recruiter', 'reviewer')),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_recruiter_user_roles_user_id
ON public.recruiter_user_roles(user_id);

CREATE INDEX IF NOT EXISTS idx_recruiter_user_roles_role
ON public.recruiter_user_roles(role);

-- Helper: role check for current auth user.
CREATE OR REPLACE FUNCTION app.user_has_role(p_roles text[])
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.recruiter_user_roles rur
    WHERE rur.user_id = auth.uid()
      AND rur.is_active = true
      AND rur.role = ANY(p_roles)
  );
$$;

REVOKE ALL ON FUNCTION app.user_has_role(text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.user_has_role(text[]) TO authenticated;

-- 2) Enable RLS
ALTER TABLE public.cv_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cv_filename_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recruiter_user_roles ENABLE ROW LEVEL SECURITY;

-- 3) Remove broad policies (if present)
DROP POLICY IF EXISTS "Enable all access for authenticated users" ON public.cv_intelligence;
DROP POLICY IF EXISTS "Enable all access for authenticated users" ON public.cv_filename_mapping;

-- 4) cv_intelligence strict role policies
DROP POLICY IF EXISTS cv_intelligence_select_roles ON public.cv_intelligence;
CREATE POLICY cv_intelligence_select_roles
ON public.cv_intelligence
FOR SELECT
TO authenticated
USING (app.user_has_role(ARRAY['admin', 'recruiter', 'reviewer']));

DROP POLICY IF EXISTS cv_intelligence_insert_recruiter_admin ON public.cv_intelligence;
CREATE POLICY cv_intelligence_insert_recruiter_admin
ON public.cv_intelligence
FOR INSERT
TO authenticated
WITH CHECK (app.user_has_role(ARRAY['admin', 'recruiter']));

DROP POLICY IF EXISTS cv_intelligence_update_recruiter_admin ON public.cv_intelligence;
CREATE POLICY cv_intelligence_update_recruiter_admin
ON public.cv_intelligence
FOR UPDATE
TO authenticated
USING (app.user_has_role(ARRAY['admin', 'recruiter']))
WITH CHECK (app.user_has_role(ARRAY['admin', 'recruiter']));

DROP POLICY IF EXISTS cv_intelligence_delete_admin ON public.cv_intelligence;
CREATE POLICY cv_intelligence_delete_admin
ON public.cv_intelligence
FOR DELETE
TO authenticated
USING (app.user_has_role(ARRAY['admin']));

-- 5) cv_filename_mapping strict role policies
DROP POLICY IF EXISTS cv_filename_mapping_select_roles ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_select_roles
ON public.cv_filename_mapping
FOR SELECT
TO authenticated
USING (app.user_has_role(ARRAY['admin', 'recruiter', 'reviewer']));

DROP POLICY IF EXISTS cv_filename_mapping_insert_recruiter_admin ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_insert_recruiter_admin
ON public.cv_filename_mapping
FOR INSERT
TO authenticated
WITH CHECK (app.user_has_role(ARRAY['admin', 'recruiter']));

DROP POLICY IF EXISTS cv_filename_mapping_update_recruiter_admin ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_update_recruiter_admin
ON public.cv_filename_mapping
FOR UPDATE
TO authenticated
USING (app.user_has_role(ARRAY['admin', 'recruiter']))
WITH CHECK (app.user_has_role(ARRAY['admin', 'recruiter']));

DROP POLICY IF EXISTS cv_filename_mapping_delete_admin ON public.cv_filename_mapping;
CREATE POLICY cv_filename_mapping_delete_admin
ON public.cv_filename_mapping
FOR DELETE
TO authenticated
USING (app.user_has_role(ARRAY['admin']));

-- 6) role table policies
DROP POLICY IF EXISTS recruiter_user_roles_select_own ON public.recruiter_user_roles;
CREATE POLICY recruiter_user_roles_select_own
ON public.recruiter_user_roles
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

DROP POLICY IF EXISTS recruiter_user_roles_admin_manage ON public.recruiter_user_roles;
CREATE POLICY recruiter_user_roles_admin_manage
ON public.recruiter_user_roles
FOR ALL
TO authenticated
USING (app.user_has_role(ARRAY['admin']))
WITH CHECK (app.user_has_role(ARRAY['admin']));

-- 7) Reviewer-safe function (column-safe update path)
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
    AND app.user_has_role(ARRAY['admin', 'reviewer'])
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
-- POST-MIGRATION MANUAL STEPS:
--
-- 1) Seed user roles:
--    INSERT INTO public.recruiter_user_roles (user_id, role, is_active)
--    VALUES
--      ('<admin-user-uuid>'::uuid, 'admin', true),
--      ('<recruiter-user-uuid>'::uuid, 'recruiter', true),
--      ('<reviewer-user-uuid>'::uuid, 'reviewer', true)
--    ON CONFLICT (user_id) DO UPDATE
--    SET role = EXCLUDED.role,
--        is_active = EXCLUDED.is_active;
--
-- 2) Verify RLS:
--    SELECT tablename, rowsecurity FROM pg_tables
--    WHERE schemaname='public' AND tablename IN ('cv_intelligence','cv_filename_mapping','recruiter_user_roles');
-- -----------------------------------------------------------------------------
