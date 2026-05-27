from __future__ import annotations

from supabase_storage import SupabaseStorage


def main() -> int:
    storage = SupabaseStorage()
    client = storage.client

    # Pull only the rows created by the archive ingester.
    # Note: `like` is supported by supabase-py postgrest query builder.
    resp = (
        client.table("cv_intelligence")
        .select(
            "anonymized_id,llm_provider,llm_model,core_technical_skills,years_experience,years_of_experience,cleaned_text,cleaned_narrative,primary_domain,embedding,created_at",
            count="exact",
        )
        .eq("llm_provider", "none")
        .limit(1000)
        .execute()
    )

    rows = resp.data or []
    exact_count = getattr(resp, "count", None)

    total_archive = exact_count if exact_count is not None else len(rows)

    with_embedding = [r for r in rows if r.get("embedding") is not None]
    empty_skills = [r for r in rows if not r.get("core_technical_skills")]
    short_text = [
        r
        for r in rows
        if not (r.get("cleaned_text") or "").strip()
        or len((r.get("cleaned_text") or "").strip()) < 200
    ]

    print("Archive-ingested rows (llm_provider=none)")
    print("- count:", total_archive)
    print("- with embedding:", len(with_embedding), "/", len(rows))
    print("- empty core_technical_skills:", len(empty_skills), "/", len(rows))
    print("- cleaned_text < 200 chars:", len(short_text), "/", len(rows))

    if short_text:
        print("\nExamples of short/empty cleaned_text (up to 10)")
        for r in short_text[:10]:
            cleaned = (r.get("cleaned_text") or "").strip()
            print(
                "-",
                r.get("anonymized_id"),
                "| len=",
                len(cleaned),
            )

    missing_embed = [r for r in rows if r.get("embedding") is None]
    if missing_embed:
        print("\nExamples missing embeddings (up to 10)")
        for r in missing_embed[:10]:
            print(
                "-",
                r.get("anonymized_id"),
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
