"""
mlops/tracking.py
Tracks RAG pipeline parameters, FAISS index builds, and model versioning details using MLflow.
"""

import time
import logging
import config

logger = logging.getLogger("medtrack.mlops")

def log_index_build(num_medicines: int, num_chunks: int, duration_sec: float, index_version: str):
    """
    Log information about a FAISS index build event to MLflow.
    Wrapped in try-except to prevent runtime errors if MLflow is not running.
    """
    try:
        import mlflow
        
        mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(config.MLFLOW_EXPERIMENT_NAME)
        
        with mlflow.start_run(run_name=f"index_build_{index_version}"):
            # Log params
            mlflow.log_param("embedding_model", config.EMBEDDING_MODEL)
            mlflow.log_param("index_version", index_version)
            mlflow.log_param("num_medicines", num_medicines)
            
            # Log metrics
            mlflow.log_metric("num_chunks", num_chunks)
            mlflow.log_metric("build_duration_sec", duration_sec)
            
            # Tag the run
            mlflow.set_tag("stage", "indexing")
            
        logger.info(f"MLflow logged index build: {index_version}")
    except Exception as e:
        logger.warning(f"MLflow tracking failed (index build): {e}")


def log_rag_evaluation(query: str, retrieved_count: int, latency_ms: float, has_sources: bool):
    """
    Log general RAG query evaluation data to MLflow as a run.
    """
    try:
        import mlflow
        
        mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(config.MLFLOW_EXPERIMENT_NAME)
        
        # We start a run for tracking query performance aggregates
        with mlflow.start_run(run_name="rag_query_eval", nested=True):
            mlflow.log_param("rag_top_k", config.RAG_TOP_K)
            mlflow.log_metric("latency_ms", latency_ms)
            mlflow.log_metric("retrieved_count", retrieved_count)
            mlflow.log_metric("has_sources", 1 if has_sources else 0)
            
            mlflow.set_tag("stage", "inference_eval")
    except Exception as e:
        # Silently pass to avoid interrupting patient chatbot experience
        pass
