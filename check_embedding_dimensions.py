"""Check embedding dimensions in database"""
from supabase_storage import SupabaseStorage
import json

storage = SupabaseStorage()
response = storage.client.table('cv_intelligence').select('anonymized_id, embedding').limit(50).execute()

print("Checking embedding dimensions...")
print("=" * 60)

dims_384 = []
dims_768 = []
no_embedding = []

for row in response.data:
    anon_id = row['anonymized_id']
    embedding = row.get('embedding')
    
    if not embedding:
        no_embedding.append(anon_id)
        continue
    
    if isinstance(embedding, str):
        embedding = json.loads(embedding)
    
    dims = len(embedding)
    if dims == 384:
        dims_384.append(anon_id)
    elif dims == 768:
        dims_768.append(anon_id)
    else:
        print(f"Unexpected dimensions: {anon_id} = {dims}d")

print(f"\n768d embeddings (NEW): {len(dims_768)}")
print(f"384d embeddings (OLD): {len(dims_384)}")
print(f"No embedding: {len(no_embedding)}")

if dims_384:
    print(f"\nCandidates still with 384d embeddings:")
    for cand_id in dims_384[:10]:
        print(f"  - {cand_id}")
    if len(dims_384) > 10:
        print(f"  ... and {len(dims_384) - 10} more")

print("\n" + "=" * 60)
if dims_384:
    print("[WARNING] Some candidates still have 384d embeddings!")
    print("Run: python regenerate_embeddings.py --force")
else:
    print("[SUCCESS] All candidates have 768d embeddings!")
