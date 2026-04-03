"""
Quick sanity check for the Twelve Labs API.
Run: python test_twelvelabs.py
"""

import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs

load_dotenv()
api_key = os.environ.get("TWELVELABS_API_KEY")

print("=== Twelve Labs API Test ===\n")

# 1. Auth check
print("1. Checking API key...")
if not api_key:
    print("   FAIL — TWELVELABS_API_KEY not found in .env")
    exit(1)
print(f"   OK — key found: {api_key[:12]}...")

# 2. Client connection
print("\n2. Connecting to Twelve Labs...")
try:
    client = TwelveLabs(api_key=api_key)
    print("   OK — client created")
except Exception as e:
    print(f"   FAIL — {e}")
    exit(1)

# 3. List indexes
print("\n3. Listing existing indexes...")
try:
    indexes = list(client.indexes.list())
    if indexes:
        for idx in indexes:
            idx_name = getattr(idx, "name", None) or getattr(idx, "index_name", None) or idx.id
            print(f"   - {idx_name} (id: {idx.id})")
    else:
        print("   No indexes yet (this is fine)")
    print("   OK")
except Exception as e:
    print(f"   FAIL — {e}")
    exit(1)

# 4. Create a test index
print("\n4. Creating test index 'pitlane-ai-test'...")
try:
    # Delete if exists
    for idx in client.indexes.list():
        idx_name = getattr(idx, "name", None) or getattr(idx, "index_name", None) or ""
        if idx_name == "pitlane-ai-test":
            client.indexes.delete(idx.id)
            print("   (deleted existing test index)")
            break

    test_index = client.indexes.create(
        index_name="pitlane-ai-test",
        models=[
            {"name": "marengo3.0", "options": ["visual", "audio", "text"]},
            {"name": "pegasus1.2",  "options": ["visual", "audio"]},
        ],
    )
    print(f"   OK — index created: {test_index.id}")
except Exception as e:
    print(f"   FAIL — {e}")
    exit(1)

# 5. Cleanup
print("\n5. Cleaning up test index...")
try:
    client.indexes.delete(test_index.id)
    print("   OK — test index deleted")
except Exception as e:
    print(f"   WARNING — could not delete test index: {e}")

print("\n=== All checks passed! Twelve Labs is ready. ===")
