"""
Monitoring routes — Prometheus metrics, health check, system status.
"""

import time
import psutil
from fastapi import APIRouter, Depends
from database.base import get_db
from utils.security import require_role

router = APIRouter(tags=["Monitoring"])

# In-memory metrics for Prometheus
REQUEST_COUNT = 0
REQUEST_LATENCY_SUM = 0.0
ERROR_COUNT = 0


def increment_request():
    global REQUEST_COUNT
    REQUEST_COUNT += 1


def increment_error():
    global ERROR_COUNT
    ERROR_COUNT += 1


def add_latency(duration: float):
    global REQUEST_LATENCY_SUM
    REQUEST_LATENCY_SUM += duration


@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "mediqr-backend",
        "timestamp": time.time(),
    }


@router.get("/metrics")
def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    metrics = []
    metrics.append(f"# HELP mediqr_requests_total Total HTTP requests")
    metrics.append(f"# TYPE mediqr_requests_total counter")
    metrics.append(f"mediqr_requests_total {REQUEST_COUNT}")

    metrics.append(f"# HELP mediqr_errors_total Total HTTP errors")
    metrics.append(f"# TYPE mediqr_errors_total counter")
    metrics.append(f"mediqr_errors_total {ERROR_COUNT}")

    metrics.append(f"# HELP mediqr_request_latency_seconds_sum Total request latency")
    metrics.append(f"# TYPE mediqr_request_latency_seconds_sum counter")
    metrics.append(f"mediqr_request_latency_seconds_sum {REQUEST_LATENCY_SUM:.4f}")

    metrics.append(f"# HELP mediqr_cpu_usage_percent CPU usage percentage")
    metrics.append(f"# TYPE mediqr_cpu_usage_percent gauge")
    metrics.append(f"mediqr_cpu_usage_percent {cpu_percent}")

    metrics.append(f"# HELP mediqr_memory_usage_percent Memory usage percentage")
    metrics.append(f"# TYPE mediqr_memory_usage_percent gauge")
    metrics.append(f"mediqr_memory_usage_percent {memory.percent}")

    metrics.append(f"# HELP mediqr_memory_used_bytes Memory used in bytes")
    metrics.append(f"# TYPE mediqr_memory_used_bytes gauge")
    metrics.append(f"mediqr_memory_used_bytes {memory.used}")

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(metrics) + "\n", media_type="text/plain")


@router.get("/api/monitoring/system")
def system_status(
    current_user=Depends(require_role("admin")),
):
    """System health dashboard data. Admin only."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "success": True,
        "data": {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": round(disk.percent, 1),
            },
            "requests": {
                "total": REQUEST_COUNT,
                "errors": ERROR_COUNT,
                "avg_latency_ms": round((REQUEST_LATENCY_SUM / max(REQUEST_COUNT, 1)) * 1000, 2),
            },
        },
    }
