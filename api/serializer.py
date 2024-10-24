
from typing import Any, Dict
from api.models import *
from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=255)
    answer = serializers.CharField(max_length=255)