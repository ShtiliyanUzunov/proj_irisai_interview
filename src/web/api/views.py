"""
DRF views for the classification task API.

Endpoints:
  GET  /api/ping/           -- health check
  POST /api/tasks/          -- create a new classification task
  GET  /api/tasks/<id>/     -- get task status and results
  GET  /api/queue/          -- get current queue status
"""
import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import TaskCreateSerializer
from services.task_queue import task_queue, task_store

logger = logging.getLogger("api.views")


class PingView(APIView):
    """
    GET /api/ping/

    Returns "pong" if the service is running.
    """

    def get(self, request: Request) -> Response:
        return Response({"message": "pong"}, status=status.HTTP_200_OK)


class TaskCreateView(APIView):
    """
    POST /api/tasks/

    Accepts a list of {title, abstract} objects.
    Creates a task, enqueues it for processing, and returns the task ID.
    """

    def post(self, request: Request) -> Response:
        serializer = TaskCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items = serializer.validated_data["items"]
        task_id = task_store.create_task(items)
        task_queue.enqueue(task_id)

        logger.info("Task %s created with %d items", task_id, len(items))
        return Response(
            {"task_id": task_id},
            status=status.HTTP_201_CREATED,
        )


class TaskResultView(APIView):
    """
    GET /api/tasks/<task_id>/

    Returns the status of the task and, if finished, the prediction results.
    """

    def get(self, request: Request, task_id: str) -> Response:
        task = task_store.get_task(task_id)
        if task is None:
            return Response(
                {"error": f"Task '{task_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        response_data = {
            "task_id": task_id,
            "status": task["status"].value,
        }

        if task["status"].value == "FINISHED":
            response_data["result"] = task["result"]
            response_data["fromCache"] = task["from_cache"]

        return Response(response_data, status=status.HTTP_200_OK)


class QueueStatusView(APIView):
    """
    GET /api/queue/

    Returns the current queue with task IDs and their execution order.
    """

    def get(self, request: Request) -> Response:
        queue_items = task_store.get_queue_status()
        return Response(
            {"queue": queue_items},
            status=status.HTTP_200_OK,
        )
