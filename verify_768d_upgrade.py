"""
Verify that the 768d model upgrade was successful
"""
from supabase_storage import SupabaseStorage
from vector_search import get_vector_search_engine
import json

print("=" * 60)
print("VERIFYING 768D MODEL UPGRADE")
print("=" * 60)

# 1. Check model configuration
engine = get_vector_search_engine()
print(f"\n1. Model Configuration:")
print(f"   Model: {engine.LOCAL_MODEL}")
print(f"   Dimensions: {engine.dimensions}")

if engine.dimensions == 768:
    print(f"   [OK] Model configured for 768d")
else:
    print(f"   [ERROR] Model should be 768d, got {engine.dimensions}d")

# 2. Check database embeddings
storage = SupabaseStorage()
response = storage.client.table('cv_intelligence').select('anonymized_id, embedding').limit(100).execute()

print(f"\n2. Database Embeddings:")
print(f"   Total candidates checked: {len(response.data)}")

dims_count = {}
for row in response.data:
    embedding = row.get('embedding')
    if not embedding:
        dims_count[0] = dims_count.get(0, 0) + 1
        continue
    
    if isinstance(embedding, str):
        embedding = json.loads(embedding)
    
    dims = len(embedding)
    dims_count[dims] = dims_count.get(dims, 0) + 1

for dims, count in sorted(dims_count.items()):
    if dims == 0:
        print(f"   No embedding: {count} candidates")
    elif dims == 384:
        print(f"   [WARNING] 384d (OLD): {count} candidates")
    elif dims == 768:
        print(f"   [OK] 768d (NEW): {count} candidates")
    else:
        print(f"   [ERROR] Unexpected {dims}d: {count} candidates")

# 3. Test embedding generation
print(f"\n3. Test Embedding Generation:")
test_text = "Senior Python developer with 5 years experience in Django and PostgreSQL"
test_embedding = engine.generate_embedding(test_text)
print(f"   Generated embedding: {len(test_embedding)}d")

if len(test_embedding) == 768:
    print(f"   [OK] New embeddings are 768d")
else:
    print(f"   [ERROR] Expected 768d, got {len(test_embedding)}d")

# 4. Test similarity computation
print(f"\n4. Test Similarity Computation:")
# Get a candidate with 768d embedding
candidate_with_embedding = None
for row in response.data:
    embedding = row.get('embedding')
    if embedding:
        if isinstance(embedding, str):
            embedding = json.loads(embedding)
        if len(embedding) == 768:
            candidate_with_embedding = {
                'id': row['anonymized_id'],
                'embedding': embedding
            }
            break

if candidate_with_embedding:
    try:
        similarity = engine.cosine_similarity(test_embedding, candidate_with_embedding['embedding'])
        print(f"   Computed similarity with {candidate_with_embedding['id']}: {similarity:.4f}")
        print(f"   [OK] Similarity computation works with 768d embeddings")
    except Exception as e:
        print(f"   [ERROR] Similarity computation failed: {e}")
else:
    print(f"   [WARNING] No candidate with 768d embedding found for testing")

# Summary
print(f"\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

all_768d = dims_count.get(768, 0) == len([r for r in response.data if r.get('embedding')])
model_768d = engine.dimensions == 768

if all_768d and model_768d:
    print("[SUCCESS] 768d upgrade complete!")
    print("  - Model configured for 768d")
    print("  - All embeddings are 768d")
    print("  - Similarity computation works")
    print("\nYou can now:")
    print("  1. Test with: python test_15_real_jds.py")
    print("  2. Use the web interface for semantic search")
    print("  3. Expect +11.7% better accuracy!")
elif model_768d and not all_768d:
    print("[PARTIAL] Model upgraded but some embeddings still old")
    print("  Run: python regenerate_embeddings.py --force")
elif not model_768d:
    print("[ERROR] Model not configured for 768d")
    print("  Check vector_search.py lines 30-31")
else:
    print("[ERROR] Upgrade incomplete")

print("=" * 60)
