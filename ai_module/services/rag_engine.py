"""
RAG (Retrieval-Augmented Generation) Engine
Handles embedding, retrieval from FAISS, and guardrailed LLM generation.
"""

import json
import os
import pickle
import time
from pathlib import Path

import numpy as np

import config

try:
    from database.neo4j_db import get_neo4j_driver
except ImportError:
    _fallback_driver = None
    def get_neo4j_driver():
        global _fallback_driver
        if _fallback_driver is None:
            try:
                from neo4j import GraphDatabase
                uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                user = os.getenv("NEO4J_USER", "neo4j")
                password = os.getenv("NEO4J_PASSWORD", "mediqr_pass_2026")
                _fallback_driver = GraphDatabase.driver(uri, auth=(user, password))
            except Exception as e:
                print(f"Fallback Neo4j connection failed: {e}")
                _fallback_driver = None
        return _fallback_driver

# Config variables with safe fallbacks
EMBEDDING_MODEL = getattr(config, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RAG_TOP_K = getattr(config, "RAG_TOP_K", 5)

if hasattr(config, "FAISS_DIR"):
    FAISS_DIR = config.FAISS_DIR
else:
    # Resolve FAISS_DIR relative to project root
    _project_root = Path(__file__).resolve().parent.parent.parent
    FAISS_DIR = _project_root / "data" / "faiss_index"

# Lazy-loaded globals
_embedder = None
_faiss_index = None
_doc_metadata = None


def _get_embedder():
    """Lazy-load the sentence-transformers model."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def _load_faiss_index():
    """Load the pre-built FAISS index and metadata."""
    global _faiss_index, _doc_metadata

    index_path = FAISS_DIR / "index.faiss"
    meta_path = FAISS_DIR / "metadata.pkl"

    if not index_path.exists() or not meta_path.exists():
        return False

    import faiss
    _faiss_index = faiss.read_index(str(index_path))

    with open(meta_path, "rb") as f:
        _doc_metadata = pickle.load(f)

    return True


def ensure_index_loaded():
    """Make sure the FAISS index is loaded. Returns True if ready."""
    global _faiss_index
    if _faiss_index is None:
        return _load_faiss_index()
    return True


def build_knowledge_chunks(medicines_data: list) -> list[dict]:
    """
    Convert medicine records into text chunks suitable for embedding.
    Each medicine produces multiple focused chunks for better retrieval.
    """
    chunks = []

    for med in medicines_data:
        med_id = med["medicine_id"]
        name = med["name"]
        generic = med.get("generic_name", "")

        # Chunk 1: Overview
        chunks.append({
            "medicine_id": med_id,
            "chunk_type": "overview",
            "text": (
                f"Medicine: {name} ({generic}). "
                f"Category: {med.get('category', 'N/A')}. "
                f"Form: {med.get('dosage_form', 'N/A')} {med.get('strength', '')}. "
                f"Manufacturer: {med.get('manufacturer', 'N/A')}. "
                f"Description: {med.get('description', 'N/A')}"
            ),
        })

        # Chunk 2: Dosage & Schedule
        chunks.append({
            "medicine_id": med_id,
            "chunk_type": "dosage",
            "text": (
                f"Dosage information for {name} ({generic}): "
                f"{med.get('dosage_schedule', 'Consult your doctor for dosage.')} "
                f"Missed dose: {med.get('missed_dose_guidance', 'Consult your doctor.')}"
            ),
        })

        # Chunk 3: Side Effects
        chunks.append({
            "medicine_id": med_id,
            "chunk_type": "side_effects",
            "text": (
                f"Side effects of {name} ({generic}): "
                f"{med.get('side_effects', 'No specific side effects documented.')}"
            ),
        })

        # Chunk 4: Interactions (drug-drug + food-drug)
        chunks.append({
            "medicine_id": med_id,
            "chunk_type": "interactions",
            "text": (
                f"Drug and food interactions for {name} ({generic}): "
                f"{med.get('interactions', 'No specific interactions documented.')}"
            ),
        })

        # Chunk 5: Contraindications & Storage
        chunks.append({
            "medicine_id": med_id,
            "chunk_type": "safety",
            "text": (
                f"Safety information for {name} ({generic}): "
                f"Contraindications: {med.get('contraindications', 'N/A')}. "
                f"Storage: {med.get('storage_instructions', 'N/A')}."
            ),
        })

    return chunks


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of texts using the sentence-transformers model."""
    embedder = _get_embedder()
    embeddings = embedder.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    return np.array(embeddings, dtype="float32")


def retrieve(query: str, medicine_ids: list[str] = None, top_k: int = None) -> list[dict]:
    """
    Retrieve the most relevant knowledge chunks for a query.
    
    Args:
        query: Natural language question from the patient
        medicine_ids: Optional list of Medicine_IDs to scope retrieval to
        top_k: Number of results to return
        
    Returns:
        List of dicts with 'text', 'medicine_id', 'chunk_type', 'score'
    """
    if not ensure_index_loaded():
        return []

    if top_k is None:
        top_k = RAG_TOP_K

    embedder = _get_embedder()
    query_vec = embedder.encode([query], normalize_embeddings=True).astype("float32")

    # Search broader if we'll filter by medicine_ids
    search_k = top_k * 10 if medicine_ids else top_k

    distances, indices = _faiss_index.search(query_vec, min(search_k, len(_doc_metadata)))

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(_doc_metadata):
            continue

        doc = _doc_metadata[idx]

        # Filter by medicine IDs if specified (scope to patient's medicines)
        if medicine_ids and doc["medicine_id"] not in medicine_ids:
            continue

        results.append({
            "text": doc["text"],
            "medicine_id": doc["medicine_id"],
            "chunk_type": doc["chunk_type"],
            "score": float(dist),
        })

        if len(results) >= top_k:
            break

    return results


def retrieve_graph_context(query: str, medicine_ids: list[str] = None) -> str:
    """
    Retrieve structured medical metadata, drug-drug interactions, and warning
    relationships from the Neo4j graph database to ground chatbot responses.
    """
    if not medicine_ids:
        return ""
    
    driver = get_neo4j_driver()
    if not driver:
        return ""
        
    context_lines = []
    
    try:
        with driver.session() as session:
            # 1. Fetch Cabinet Medicine Info and Categories
            res1 = session.run(
                """
                MATCH (m:Medicine)
                WHERE m.medicine_id IN $medicine_ids
                OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH (m)-[:MADE_BY]->(man:Manufacturer)
                RETURN m.medicine_id as id, m.name as name, m.generic_name as generic, collect(c.name) as categories, man.name as manufacturer
                """,
                medicine_ids=medicine_ids
            )
            med_details = []
            for r in res1:
                cats = ", ".join(r["categories"]) if r["categories"] else "N/A"
                med_details.append(f"- {r['name']} ({r['generic']}) | Categories: {cats} | Manufacturer: {r['manufacturer'] or 'N/A'}")
            if med_details:
                context_lines.append("Patient's Active Medicines (Graph Metadata):")
                context_lines.extend(med_details)
                context_lines.append("")

            # 2. Fetch Drug-Drug Interactions amongst cabinet medicines
            res2 = session.run(
                """
                MATCH (m1:Medicine)-[r:INTERACTS_WITH {type: 'drug-drug'}]->(m2:Medicine)
                WHERE m1.medicine_id IN $medicine_ids AND m2.medicine_id IN $medicine_ids
                RETURN m1.name as med1, m2.name as med2, r.description as desc
                """,
                medicine_ids=medicine_ids
            )
            interactions = []
            for r in res2:
                interactions.append(f"- Warning: Potential interaction between {r['med1']} and {r['med2']}: {r['desc']}")
            if interactions:
                context_lines.append("Detected Drug-Drug Interactions:")
                context_lines.extend(interactions)
                context_lines.append("")

            # 3. Fetch Food/Substance Warnings
            res3 = session.run(
                """
                MATCH (m:Medicine)-[r:INTERACTS_WITH {type: 'food-substance'}]->(s:Substance)
                WHERE m.medicine_id IN $medicine_ids
                RETURN m.name as med, s.name as substance, r.description as desc
                """,
                medicine_ids=medicine_ids
            )
            sub_interactions = []
            query_lower = query.lower()
            for r in res3:
                sub_name = r['substance'].lower()
                # Include warning if substance is in query, or general warning search query triggers
                if sub_name in query_lower or any(w in query_lower for w in ["food", "milk", "alcohol", "drink", "grapefruit", "eat", "warning", "restriction"]):
                    sub_interactions.append(f"- Food/Substance warning for {r['med']} with {r['substance']}: {r['desc']}")
            if sub_interactions:
                context_lines.append("Detected Substance/Food Warnings:")
                context_lines.extend(sub_interactions)
                context_lines.append("")

            # 4. Fetch Category Alternatives (if substitute/alternative is asked)
            if any(kwd in query_lower for kwd in ["alternative", "substitute", "instead", "replace", "other"]):
                res4 = session.run(
                    """
                    MATCH (m1:Medicine)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(m2:Medicine)
                    WHERE m1.medicine_id IN $medicine_ids AND m1.medicine_id <> m2.medicine_id
                    RETURN DISTINCT c.name as category, m2.name as alternative, m2.generic_name as alt_generic, m2.description as alt_desc
                    """,
                    medicine_ids=medicine_ids
                )
                alternatives = []
                for r in res4:
                    alternatives.append(f"- Alternative in category '{r['category']}': {r['alternative']} (Generic: {r['alt_generic']}) - {r['alt_desc']}")
                if alternatives:
                    context_lines.append("Graph Alternatives & Category-mates:")
                    context_lines.extend(alternatives)
                    context_lines.append("")

    except Exception as e:
        print(f"Error querying Neo4j for Graph RAG context: {e}")
        
    return "\n".join(context_lines).strip()


def build_rag_prompt(query: str, context_chunks: list[dict], patient_medicines: list[dict] = None, graph_context: str = "") -> str:
    """
    Build a guardrailed prompt for the LLM combining vector search chunks and graph relationships.
    """
    # Build text context string
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(f"[Source {i} — {chunk['medicine_id']}]\n{chunk['text']}")

    context_str = "\n\n".join(context_parts)

    # Build graph context block
    graph_context_str = ""
    if graph_context:
        graph_context_str = f"VERIFIED GRAPH DATABASE RELATIONSHIPS:\n{graph_context}\n\n"

    # Build medicine list if available
    med_list_str = ""
    if patient_medicines:
        med_names = [f"- {m.get('name', m.get('medicine_id', 'Unknown'))}" for m in patient_medicines]
        med_list_str = f"\nThe patient's current medicines are:\n" + "\n".join(med_names)

    prompt = f"""You are MedTrack AI, a helpful and cautious medical information assistant. You help patients understand their prescribed medications.

STRICT RULES — You MUST follow these:
1. ONLY answer based on the provided medical knowledge context below. Do NOT use any external knowledge.
2. If the answer is NOT in the context, say: "I don't have enough information about that in my verified database. Please consult your doctor or pharmacist."
3. NEVER diagnose conditions, prescribe medications, or recommend dosage changes.
4. NEVER suggest stopping or changing a prescribed medication.
5. Always remind the patient to consult their healthcare provider for medical decisions.
6. Be empathetic, clear, and use simple language.
7. When citing information, reference the source medicine name.
{med_list_str}

VERIFIED MEDICAL KNOWLEDGE CONTEXT:
{graph_context_str}{context_str}

PATIENT QUESTION: {query}

Provide a helpful, accurate answer based ONLY on the above context. If you cite information, mention which medicine it relates to. End with a brief reminder to consult their doctor for personalised advice."""

    return prompt


def generate_response(query: str, medicine_ids: list[str] = None, patient_medicines: list[dict] = None) -> dict:
    """
    Full Hybrid RAG pipeline: retrieve vector chunks + retrieve graph context → build prompt → generate response.
    
    Returns:
        dict with 'answer', 'sources', 'latency_ms'
    """
    start_time = time.time()

    # Step 1: Retrieve relevant FAISS context
    context_chunks = retrieve(query, medicine_ids=medicine_ids)

    # Step 2: Retrieve Graph Context from Neo4j
    graph_context = ""
    if medicine_ids:
        try:
            graph_context = retrieve_graph_context(query, medicine_ids=medicine_ids)
        except Exception as e:
            print(f"Failed to fetch Neo4j graph context: {e}")

    if not context_chunks and not graph_context:
        return {
            "answer": (
                "I don't have enough information in my verified database to answer that question. "
                "Please consult your doctor or pharmacist for guidance."
            ),
            "sources": [],
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "model": "none (no context found)",
        }

    # Step 3: Build guardrailed prompt
    prompt = build_rag_prompt(query, context_chunks, patient_medicines, graph_context)

    # Step 4: Generate response via Gemini
    answer = _call_gemini(prompt)

    latency = round((time.time() - start_time) * 1000, 2)

    # Step 5: Build source citations
    sources = list({c["medicine_id"] for c in context_chunks})

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(context_chunks),
        "has_graph_context": bool(graph_context),
        "latency_ms": latency,
        "model": config.GEMINI_MODEL,
    }


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API for text generation."""
    if not config.GEMINI_API_KEY:
        return (
            "⚠️ The AI chatbot is not configured yet. Please set the GEMINI_API_KEY "
            "environment variable to enable AI responses. For now, please consult "
            "your pharmacist or doctor for medication questions."
        )

    try:
        import google.generativeai as genai

        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,       # Low temperature for factual accuracy
                max_output_tokens=800,
                top_p=0.8,
            ),
        )

        return response.text.strip()

    except Exception as e:
        return (
            f"I encountered an error generating a response. Please try again later. "
            f"In the meantime, consult your pharmacist or doctor. (Error: {str(e)[:100]})"
        )
