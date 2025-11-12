"""
Custom middleware for performance monitoring and logging.
"""
from __future__ import annotations

import logging
import time
from typing import Iterable

from django.conf import settings
from django.db import connections

logger = logging.getLogger("performance")


class SlowRequestLoggingMiddleware:
    """
    Logs requests that are slower than the configured threshold and includes
    database query metrics when enabled.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_request_threshold_ms = getattr(
            settings, "SLOW_REQUEST_THRESHOLD_MS", 1000
        )
        self.slow_query_threshold_ms = getattr(
            settings, "SLOW_QUERY_THRESHOLD_MS", 500
        )
        self.enable_query_profiling = getattr(
            settings, "ENABLE_QUERY_PROFILING", False
        )

    def __call__(self, request):
        start_time = time.perf_counter()

        if self.enable_query_profiling:
            self._enable_query_logging()

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        query_metrics = self._collect_query_metrics()

        if duration_ms >= self.slow_request_threshold_ms or query_metrics["slow"]:
            logger.warning(
                "Slow request detected",
                extra={
                    "path": request.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "status_code": getattr(response, "status_code", "unknown"),
                    "query_count": query_metrics["count"],
                    "query_time_ms": round(query_metrics["time_ms"], 2),
                    "slow_queries": query_metrics["slow"],
                },
            )

        return response

    def _enable_query_logging(self):
        """Enable query logging on all database connections."""
        for connection in connections.all():
            connection.force_debug_cursor = True

    def _collect_query_metrics(self):
        """
        Gather query metrics (count, total time, slow queries) if profiling is enabled.
        """
        if not self.enable_query_profiling:
            return {"count": 0, "time_ms": 0.0, "slow": []}

        total_queries = 0
        total_time_ms = 0.0
        slow_queries: list[dict] = []

        for connection in connections.all():
            queries = getattr(connection, "queries", [])
            total_queries += len(queries)
            for query in queries:
                try:
                    exec_time = float(query.get("time", 0)) * 1000
                except (TypeError, ValueError):
                    exec_time = 0.0

                total_time_ms += exec_time
                if exec_time >= self.slow_query_threshold_ms:
                    slow_queries.append(
                        {
                            "sql": query.get("sql", "")[:500],
                            "time_ms": round(exec_time, 2),
                        }
                    )

            # Reset query log to avoid memory leaks
            queries_log = getattr(connection, "queries_log", None)
            if hasattr(queries_log, "clear"):
                queries_log.clear()

        # Disable debug cursor once metrics are collected
        for connection in connections.all():
            connection.force_debug_cursor = False

        return {"count": total_queries, "time_ms": total_time_ms, "slow": slow_queries}

