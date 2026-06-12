"""
mlops/monitor.py
Real-time inference logging, data drift detection placeholders, and system monitoring for the AI Chatbot.
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import config

MONITOR_LOG_DIR = config.DATA_DIR / "monitoring"
MONITOR_LOG_DIR.mkdir(exist_ok=True)
INFERENCE_LOG_FILE = MONITOR_LOG_DIR / "chatbot_inference.jsonl"


def log_inference(query: str, medicine_ids: list[str], response: str, sources: list[str], latency_ms: float, model: str):
    """
    Log a single chatbot inference step to a structured JSONL file for drift detection & auditable logs.
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "query_length": len(query),
        "scoped_medicines": medicine_ids,
        "response_length": len(response),
        "sources_retrieved": sources,
        "num_sources": len(sources),
        "latency_ms": latency_ms,
        "model": model,
        "alerts": []
    }

    # Proactive alerting thresholds
    if latency_ms > 2500: # 2.5 seconds threshold
        log_entry["alerts"].append("HIGH_LATENCY")
    
    # Check if answer indicates a lack of knowledge (retrieval miss/fallback)
    fallback_phrases = ["don't have enough information", "not in my verified database", "consult your doctor"]
    if any(phrase in response.lower() for phrase in fallback_phrases) and not sources:
        log_entry["alerts"].append("RETRIEVAL_MISS")

    # Append to local JSONL log file
    try:
        with open(INFERENCE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to log inference monitoring data: {e}")

    # Track overall summary trends to MLflow if enabled
    try:
        from mlops.tracking import log_rag_evaluation
        log_rag_evaluation(
            query=query,
            retrieved_count=len(sources),
            latency_ms=latency_ms,
            has_sources=len(sources) > 0
        )
    except Exception:
        pass


def get_inference_logs(limit: int = 100) -> list[dict]:
    """Retrieve recent inference logs for the monitoring dashboard."""
    if not INFERENCE_LOG_FILE.exists():
        return []

    logs = []
    try:
        with open(INFERENCE_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
                    if len(logs) > limit * 2: # read a bit more to get tail
                        logs = logs[-limit:]
    except Exception as e:
        print(f"Failed to read inference logs: {e}")

    return logs[::-1][:limit] # Return newest first


def get_drift_metrics() -> dict:
    """
    Placeholder/Simulated Data Drift analysis.
    In production, this would compare query embedding distributions over time.
    For this Intern Project, we calculate:
    - Average latency
    - Fallback rate (RAG miss rate)
    - Total queries logged
    - Average query length
    """
    logs = get_inference_logs(1000)
    if not logs:
        return {
            "total_queries": 0,
            "avg_latency_ms": 0.0,
            "fallback_rate": 0.0,
            "avg_query_length": 0.0,
            "latency_alerts": 0,
            "retrieval_miss_alerts": 0
        }

    total = len(logs)
    sum_latency = sum(l["latency_ms"] for l in logs)
    sum_len = sum(l["query_length"] for l in logs)
    
    miss_count = sum(1 for l in logs if "RETRIEVAL_MISS" in l.get("alerts", []))
    latency_alerts = sum(1 for l in logs if "HIGH_LATENCY" in l.get("alerts", []))

    return {
        "total_queries": total,
        "avg_latency_ms": round(sum_latency / total, 2),
        "fallback_rate": round(miss_count / total, 4) if total > 0 else 0.0,
        "avg_query_length": round(sum_len / total, 1),
        "latency_alerts": latency_alerts,
        "retrieval_miss_alerts": miss_count
    }
