# -*- coding: utf-8 -*-
import django_filters
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ReadOnlyModelViewSet

from django.db.models import Q

from neoxam.adltrack import models


class CommitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Commit
        fields = ('revision', 'path', )


class CommitViewSet(ReadOnlyModelViewSet):
    serializer_class = CommitSerializer
    lookup_field = 'revision'
    queryset = models.Commit.objects.all().order_by('-revision')


class ProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Procedure
        fields = ('version', 'name',)


class ProcedureViewSet(ReadOnlyModelViewSet):
    serializer_class = ProcedureSerializer
    queryset = models.Procedure.objects.all().order_by('-version', 'name')

    # def get_object(self):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     obj = get_object_or_404(queryset, **self.kwargs)
    #     self.check_object_permissions(self.request, obj)
    #     return obj



class ProcedureVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProcedureVersion
        fields = ('procedure', 'commit', 'data',)
    procedure = ProcedureSerializer()
    commit = CommitSerializer()

class ProcedureVersionViewSet(ReadOnlyModelViewSet):
    serializer_class = ProcedureVersionSerializer

    def get_queryset(self):
        qs = models.ProcedureVersion.objects.all()
        if 'revision' in self.kwargs:
            qs = qs.filter(commit__revision=self.kwargs['revision']).order_by('-procedure__version', 'procedure__name')
        elif 'version' in self.kwargs and 'name' in self.kwargs:
            qs = qs.filter(procedure__version=self.kwargs['version'], procedure__name=self.kwargs['name']).order_by('-commit__revision')
        return qs

class CompilationLastRevisionSerializer(serializers.ModelSerializer):
    revision = serializers.SlugRelatedField(read_only=True, slug_field="revision", source="commit")
    class Meta:
        model = models.ProcedureVersion
        fields = ("revision",)

class RevisionFilter(filters.FilterSet):
    min_revision = django_filters.NumberFilter(name='commit__revision', lookup_type='gt')
    max_revision = django_filters.NumberFilter(name='commit__revision', lookup_type='lte')
    class Meta:
        model = models.ProcedureVersion
        fields = ['min_revision', 'max_revision']

class CompilationLastRevisionViewSet(ReadOnlyModelViewSet):
    serializer_class = CompilationLastRevisionSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = RevisionFilter

    def get_queryset(self):
        qs = models.ProcedureVersion.objects.filter(Q(procedure__name=self.kwargs['name'], procedure__version=self.kwargs['version']) &
                                                    Q(magnum_compiled=True))\
                                            .order_by('-commit__revision')
        return qs

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())[:1]
        obj = get_object_or_404(queryset)
        self.check_object_permissions(self.request, obj)
        return obj