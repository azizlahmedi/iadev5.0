# -*- coding: utf-8 -*-
from django.db import models

from neoxam.scrumreport import consts


class Project(models.Model):
    jira_id = models.IntegerField(unique=True)
    key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Scrum(models.Model):
    jira_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name


class Sprint(models.Model):
    scrum = models.ForeignKey('Scrum',on_delete=models.CASCADE)
    jira_id = models.IntegerField(unique=True)
    key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    closed = models.BooleanField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    complete_date = models.DateTimeField(blank=True, null=True)
    completed_issues = models.ManyToManyField('Issue', related_name='completed_in_sprint')
    incompleted_issues = models.ManyToManyField('Issue', related_name='incompleted_in_sprint')
    punted_issues = models.ManyToManyField('Issue', related_name='punted_from_sprint',
                                           verbose_name="Issues that are no longer in the sprint")

    def sum_completed_timespent(self):
        return self.completed_issues.aggregate(t=models.Sum('timespent'))['t']

    def sum_incompleted_timespent(self):
        return self.incompleted_issues.aggregate(t=models.Sum('timespent'))['t']

    def sum_punted_timespent(self):
        return self.punted_issues.aggregate(t=models.Sum('timespent'))['t']

    def __str__(self):
        return self.name


class Issue(models.Model):
    jira_id = models.IntegerField(unique=True)
    key = models.CharField(max_length=255)
    summary = models.CharField(max_length=1023)
    timespent = models.DecimalField(max_digits=10, decimal_places=2)  # Man days
    epic = models.ForeignKey('self',on_delete=models.CASCADE, blank=True, null=True)
    epic_color = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.summary

    def url(self):
        return consts.JIRA_URL + 'browse/' + self.key


class NxUser(models.Model):
    ldap_username = models.CharField(max_length=255, unique=True)
    ldap_password = models.CharField(max_length=255)
    current_scrum = models.ForeignKey('Scrum', blank=True, null=True, on_delete=models.SET_NULL)

    REQUIRED_FIELDS = []

    def is_active(self):
        return True

    def get_full_name(self):
        return self.ldap_username

    def get_short_name(self):
        return self.ldap_username

    def __str__(self):
        return self.ldap_username
