"""
test_index.py
==============
Checks if the existing Twelve Labs index is accessible and ready.

Run: python test_index.py
"""

import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs

load_dotenv()

INDEX_ID = "69cfea5921ee25d04843f78e"

client = TwelveLabs(api_key=os.environ["TWELVELABS_API_KEY"])

print(f"Checking index {INDEX_ID}...")

try:
    index = client.indexes.retrieve(INDEX_ID)
    print(f"  ✓ Index found")
    print(f"  Name    : {getattr(index, 'index_name', None) or getattr(index, 'name', 'N/A')}")
    print(f"  ID      : {index.id}")
    print(f"  Models  : {getattr(index, 'models', getattr(index, 'engines', 'N/A'))}")
    videos = list(client.indexes.videos.list(INDEX_ID))
    print(f"  Videos  : {len(videos)} indexed")
    for v in videos:
        print(f"    - {v.id}")
except Exception as e:
    print(f"  ✗ FAIL — {e}")
