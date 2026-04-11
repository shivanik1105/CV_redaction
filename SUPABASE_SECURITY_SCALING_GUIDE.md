# Supabase Security and Scaling Guide

## 1) Multi-user API keys (10 users with own keys)

Recommended model:
- Keep company default key in server environment as fallback.
- Allow per-request runtime LLM config from API/UI:
  - llm_provider
  - llm_model
  - llm_api_key
- Never store raw user LLM keys in database logs.
- Validate provider against allowlist: openai, anthropic, gemini, groq, ollama.

Safer production option:
- Use your own auth layer and store encrypted user keys in a dedicated vault table.
- Decrypt only server-side at request time.
- Attach key ownership to authenticated user id.

## 2) Concurrent usage for 20-30 users

Application layer:
- Run app with a production WSGI server (gunicorn/uvicorn workers) instead of single-process debug server.
- Use at least 4 workers and horizontal scaling across 2 instances for 20-30 moderate users.
- Move long-running CV extraction to background jobs (Celery/RQ/Arq) and return job ids.
- Add rate limits per user (requests/minute) for upload and extraction endpoints.

Supabase layer:
- Ensure indexes exist on anonymized_id, confidence_score, years_of_experience, key_skills, domain_expertise.
- Keep pgvector index for semantic/hybrid search.
- Use pagination for list endpoints; avoid fetching all rows in hot paths.

## 3) Recommendation quality beyond keyword matching

Current direction implemented in app:
- Weighted ranking combining:
  - skill alignment
  - capability focus (case study/problem solving/dsa/ML/backend intent)
  - token overlap
  - experience fit
  - domain fit

Result:
- JD intent matters. Example: case-study/data-science requirements can outrank DSA-heavy-only profiles when the role needs experimentation and business analytics.

## 4) Supabase security hardening checklist

Auth and access:
- Enable RLS on all business tables.
- Remove broad "allow all authenticated" policies in production.
- Create role-scoped policies:
  - recruiter can read/write company records
  - reviewer can update override fields
  - candidate cannot access recruiter tables
- Use service-role key only on backend server, never in browser.

Data protection:
- Encrypt sensitive columns at app layer before storage (if required by policy).
- Strip PII from payloads before DB writes.
- Enable point-in-time recovery and scheduled backups.

Operational controls:
- Add audit logs for recruiter overrides and manual edits.
- Add request-id tracing for upload/extract/search API calls.
- Monitor query latency and failed auth attempts.
- Rotate keys regularly.

## 5) Suggested rollout order

1. Deploy runtime key support + weighted ranking.
2. Run cleanup script in dry-run mode.
3. Run cleanup apply mode, then validate search quality.
4. Enforce strict RLS policies.
5. Move extraction to async workers and add rate limiting.

## 6) Production rollout artifacts

- Strict SQL migration pack: [supabase_rls_production_pack.sql](supabase_rls_production_pack.sql)
- Step-by-step rollout checklist: [SUPABASE_RLS_ROLLOUT_CHECKLIST.md](SUPABASE_RLS_ROLLOUT_CHECKLIST.md)
- Single-company SQL migration pack: [supabase_rls_single_company_pack.sql](supabase_rls_single_company_pack.sql)
- Single-company rollout checklist: [SUPABASE_RLS_SINGLE_COMPANY_CHECKLIST.md](SUPABASE_RLS_SINGLE_COMPANY_CHECKLIST.md)

These two files are designed to replace broad authenticated policies with company-scoped access and a reviewer-safe override flow.

If your deployment is one recruiting company with internal role-based users only, use the single-company pack and checklist.
