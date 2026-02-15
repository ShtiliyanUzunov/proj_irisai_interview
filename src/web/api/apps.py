"""
Django AppConfig for the API app.

The ready() hook wires up the semantic cache and predictor service
as dependencies of the task queue, then starts the background worker thread.
"""
import logging
import os

from django.apps import AppConfig

logger = logging.getLogger("api.apps")


class ApiConfig(AppConfig):
    name = "api"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        # Guard against double execution during Django's autoreload
        run_main = os.environ.get("RUN_MAIN")
        if run_main == "true" or run_main is None:
            self._start_worker()

    def _start_worker(self) -> None:
        from django.conf import settings

        from services.predictor_service import predictor_service
        from services.task_queue import task_queue

        cache = None
        if settings.CACHE_ENABLED:
            from services.semantic_cache import SemanticCache

            cache = SemanticCache(
                model_name=settings.CACHE_EMBEDDING_MODEL,
                threshold=settings.CACHE_THRESHOLD,
            )
            logger.info("Semantic cache ENABLED (threshold=%.2f)", settings.CACHE_THRESHOLD)
        else:
            logger.info("Semantic cache DISABLED (CACHE_ENABLED=False)")

        task_queue.set_dependencies(
            semantic_cache=cache,
            predictor_service=predictor_service,
        )
        task_queue.start_worker()
        logger.info("Background worker started")

        if not settings.LAZY_INIT:
            logger.info("LAZY_INIT=False — loading models eagerly at startup")
            if cache is not None:
                cache.eager_load()
            predictor_service.eager_load()
            logger.info("All models loaded")
