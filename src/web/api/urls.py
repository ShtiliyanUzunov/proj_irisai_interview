from django.urls import path

from api.views import PingView, QueueStatusView, TaskCreateView, TaskResultView

urlpatterns = [
    path("ping/", PingView.as_view(), name="ping"),
    path("tasks/", TaskCreateView.as_view(), name="task-create"),
    path("tasks/<str:task_id>/", TaskResultView.as_view(), name="task-result"),
    path("queue/", QueueStatusView.as_view(), name="queue-status"),
]
