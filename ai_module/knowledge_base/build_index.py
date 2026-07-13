"""
Build (or rebuild) the FAISS vector index from the medicine knowledge base.

Usage:
    python -m knowledge_base.build_index
"""

import json
import pickle
import sys
import time
from pathlib import Path

# Add parent dir to path so config is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from services.rag_engine import build_knowledge_chunks, embed_texts


def main():
    print("=" * 50)
    print("  MedTrack — FAISS Index Builder")
    print("=" * 50)

    # Load knowledge base
    kb_path = config.KNOWLEDGE_BASE_PATH
    if not kb_path.exists():
        print(f"[ERROR] Knowledge base not found: {kb_path}")
        sys.exit(1)

    with open(kb_path, "r", encoding="utf-8") as f:
        medicines = json.load(f)

    print(f"[OK] Loaded {len(medicines)} medicines from knowledge base")

    # Build chunks
    print("[...] Building knowledge chunks...")
    chunks = build_knowledge_chunks(medicines)
    print(f"[OK] Created {len(chunks)} text chunks ({len(chunks) // len(medicines)} per medicine)")

    # Embed
    print(f"[...] Embedding with model: {config.EMBEDDING_MODEL}")
    print("      (This may take a minute on first run as the model downloads...)")
    start = time.time()
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    elapsed = time.time() - start
    print(f"[OK] Embedded {len(texts)} chunks in {elapsed:.1f}s")
    print(f"     Embedding dimension: {embeddings.shape[1]}")

    # Build FAISS index
    print("[...] Building FAISS index...")
    import faiss

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product (cosine sim since vectors are normalized)
    index.add(embeddings)

    # Save index
    index_path = config.FAISS_DIR / "index.faiss"
    meta_path = config.FAISS_DIR / "metadata.pkl"

    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump(chunks, f)

    print(f"[OK] Saved FAISS index to {index_path}")
    print(f"[OK] Saved metadata to {meta_path}")
    print(f"\n[DONE] Index contains {index.ntotal} vectors")
    print(f"       Ready for RAG queries!")


if __name__ == "__main__":
    main()
