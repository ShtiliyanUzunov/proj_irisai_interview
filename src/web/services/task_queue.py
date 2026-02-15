"""
In-memory task store, FIFO queue, and background worker thread.

The TaskStore holds all task state (status, items, results) in a thread-safe dict.
The FIFO queue (queue.Queue) ensures ordering across clients.
The worker thread processes tasks sequentially, checking the semantic cache first.
"""
import logging
import queue
import threading
import uuid
from enum import Enum

logger = logging.getLogger("services.task_queue")


class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class TaskStore:
    """Thread-safe in-memory store for tasks."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks = {}
        # Ordered list of task_ids that are still pending or in-progress
        self._queue_order = []

    def create_task(self, items: list) -> str:
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = {
                "status": TaskStatus.NOT_STARTED,
                "items": items,
                "result": None,
                "from_cache": False,
            }
            self._queue_order.append(task_id)
        logger.info("Task %s created with %d items", task_id, len(items))
        return task_id

    def get_task(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return dict(task)

    def set_status(self, task_id: str, status: TaskStatus) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = status
        logger.info("Task %s status -> %s", task_id, status.value)

    def set_result(self, task_id: str, result: list, from_cache: bool = False) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["result"] = result
                self._tasks[task_id]["from_cache"] = from_cache
                self._tasks[task_id]["status"] = TaskStatus.FINISHED
                # Remove from queue order once finished
                if task_id in self._queue_order:
                    self._queue_order.remove(task_id)
        logger.info("Task %s finished with %d results (from_cache=%s)", task_id, len(result), from_cache)

    def get_queue_status(self) -> list:
        with self._lock:
            result = []
            for position, task_id in enumerate(self._queue_order, start=1):
                task = self._tasks.get(task_id)
                status = task["status"] if task else TaskStatus.NOT_STARTED
                result.append({
                    "task_id": task_id,
                    "position": position,
                    "status": status.value,
                })
            return result


class TaskQueue:
    """FIFO queue + background worker that processes tasks sequentially."""

    def __init__(self, store: TaskStore) -> None:
        self.store = store
        self._queue = queue.Queue()
        self._worker_thread = None
        self._semantic_cache = None
        self._predictor_service = None

    def set_dependencies(self, semantic_cache, predictor_service) -> None:
        """Inject the semantic cache and predictor after initialization."""
        self._semantic_cache = semantic_cache
        self._predictor_service = predictor_service

    def enqueue(self, task_id: str) -> None:
        self._queue.put(task_id)
        logger.info("Task %s enqueued", task_id)

    def start_worker(self) -> None:
        if self._worker_thread is not None and self._worker_thread.is_alive():
            logger.warning("Worker thread is already running")
            return

        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="task-worker",
        )
        self._worker_thread.start()
        logger.info("Background worker thread started")

    def _worker_loop(self) -> None:
        """Main loop: blocks on queue.get(), processes tasks one at a time."""
        while True:
            try:
                task_id = self._queue.get(block=True)
                self._process_task(task_id)
                self._queue.task_done()
            except Exception:
                logger.exception("Unhandled error in worker loop")

    def _process_task(self, task_id: str) -> None:
        task = self.store.get_task(task_id)
        if task is None:
            logger.error("Task %s not found in store, skipping", task_id)
            return

        self.store.set_status(task_id, TaskStatus.IN_PROGRESS)
        items = task["items"]
        results = []
        cache_hits = 0

        for item in items:
            pipeline_item = {
                "title": item.get("title", ""),
                "abstract": item.get("abstract", ""),
            }

            # Build a text key for cache lookup
            text_key = f"{pipeline_item['title']} {pipeline_item['abstract']}"

            # Check semantic cache
            cached = None
            if self._semantic_cache is not None:
                cached = self._semantic_cache.lookup(text_key)

            if cached is not None:
                logger.info("Cache HIT for item in task %s", task_id)
                cache_hits += 1
                results.append(cached)
            else:
                logger.info("Cache MISS for item in task %s, running prediction", task_id)
                try:
                    prediction = self._predictor_service.predict([pipeline_item])
                    result = prediction[0] if prediction else {}
                    results.append(result)

                    # Store in cache
                    if self._semantic_cache is not None:
                        self._semantic_cache.store(text_key, result)
                except Exception:
                    logger.exception("Prediction failed for item in task %s", task_id)
                    results.append({"error": "Prediction failed"})

        all_from_cache = cache_hits == len(items) and len(items) > 0
        self.store.set_result(task_id, results, from_cache=all_from_cache)


# Module-level singletons
task_store = TaskStore()
task_queue = TaskQueue(store=task_store)
