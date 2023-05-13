# -*- coding: utf-8 -*-
from rest_framework import serializers, generics
from rest_framework.parsers import MultiPartParser

from neoxam.harry import models


class PushSerializer(serializers.ModelSerializer):
    procedure = serializers.CharField(source='procedure_name')
    file = serializers.FileField(write_only=True)

    class Meta:
        model = models.Push
        fields = ('procedure', 'hostname', 'session_id', 'version', 'file')

    def validate_procedure(self, value):
        return value.lower().replace('_', '.')


class PushAPIView(generics.CreateAPIView):
    parser_classes = (MultiPartParser,)
    serializer_class = PushSerializer
