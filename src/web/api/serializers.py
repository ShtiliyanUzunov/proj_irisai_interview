"""
DRF serializers for request validation.
"""
from rest_framework import serializers


class ClassificationItemSerializer(serializers.Serializer):
    title = serializers.CharField(
        help_text="Title of the research article.",
    )
    abstract = serializers.CharField(
        help_text="Abstract text of the research article.",
    )


class TaskCreateSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=ClassificationItemSerializer(),
        allow_empty=False,
        help_text="List of articles to classify.",
    )
