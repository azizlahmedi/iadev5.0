# -*- coding: utf-8 -*-
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers
from rest_framework.parsers import JSONParser

from neoxam.webintake.backends import check_connectivity
from neoxam.webintake import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.wUser
        fields = ('user_name', 'ip_address', 'port_number')


@csrf_exempt
def create_update_user(request):
    if request.method == 'POST' or request.method == 'PUT':
        data = JSONParser().parse(request)
        user_name = data['user_name']
        try:
            user = models.wUser.objects.get(user_name=user_name)
        except models.wUser.DoesNotExist:
            serializer = UserSerializer(data=data)
        else:
            if check_connectivity(user.ip_address, user.port_number):
                return HttpResponse(status=403)  # Forbidden when user is still there
            serializer = UserSerializer(user, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)

        return JsonResponse(serializer.errors, status=400)


@csrf_exempt
def retrieve_delete_user(request, user_name):
    try:
        user = models.wUser.objects.get(user_name=user_name)
    except models.wUser.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return JsonResponse(serializer.data)

    elif request.method == 'DELETE':
        user.delete()
        return HttpResponse(status=204)
