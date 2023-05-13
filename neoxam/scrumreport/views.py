# -*- coding: utf-8 -*-
import json
import time
from collections import OrderedDict
from itertools import groupby

import requests
from dateutil.parser import parse as prs
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    StreamingHttpResponse,
)
from django.views.generic import View, TemplateView

from .consts import JIRA_REST_URL
from .forms import LoginForm
from .models import Issue, Project, Scrum, Sprint, NxUser


def login_required(view_func):
    def inner(*args, **kwargs):
        self = args[0]
        if not self.request.session.get('nxuser'):
            return HttpResponseRedirect(
                reverse('login'))
        return view_func(*args, **kwargs)

    return inner


class LoginRequiredMixin():
    @login_required
    def dispatch(*args, **kwargs):
        return super(LoginRequiredMixin, args[0]).dispatch(*args[1:], **kwargs)


class Login(TemplateView):
    template_name = "scrumreport/login.html"

    def get_context_data(self, **kwargs):
        context = super(Login, self).get_context_data(**kwargs)
        context['form'] = LoginForm()
        context['next'] = self.request.GET.get(
            'next',
            reverse('index'))
        return context

    def post(self, request):
        username = request.POST.get('ldap_username')
        password = request.POST.get('ldap_password')
        nxuser, created = NxUser.objects.update_or_create(
            ldap_username=username,
            defaults=dict(
                ldap_password=password,
            )
        )

        request.session['nxuser'] = nxuser
        redir = request.POST.get(
            'next',
            request.META.get(
                'HTTP_REFERER',
                '/'))
        return HttpResponseRedirect(
            redir)


class Logout(View):
    def get(self, request):
        request.session.pop('nxuser')
        return HttpResponseRedirect(
            request.GET.get(
                'next',
                request.META.get(
                    'HTTP_REFERER',
                    '/')))


class CurrentScrum(LoginRequiredMixin, View):
    def get(self, request):
        return HttpResponse(request.session['nxuser'].current_scrum)

    def post(self, request):
        current_user = request.session['nxuser']
        try:
            current_user.current_scrum = Scrum.objects.get(
                name=request.POST.get('name', None))
        except Scrum.DoesNotExist:
            current_user.current_scrum = None

        current_user.save()
        request.session['nxuser'] = current_user
        return HttpResponseRedirect(
            reverse('index'))


class Index(LoginRequiredMixin, TemplateView):
    template_name = 'scrumreport/index.html'

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)
        scrum_list = Scrum.objects.order_by('name')
        context.update({
            'scrums': scrum_list})
        if self.request.session['nxuser'].current_scrum:
            sprint_list = self.request.session['nxuser'].current_scrum.sprint_set.all()
        else:
            sprint_list = []
        context.update({'sprints': sprint_list})
        return context


class ShowSprint(LoginRequiredMixin, TemplateView):
    template_name = 'scrumreport/show_sprint.html'

    def get_context_data(self, **kwargs):
        context = super(ShowSprint, self).get_context_data(**kwargs)

        def get_epic(item):
            return item.epic

        scrum_list = Scrum.objects.order_by('name')
        context.update({
            'scrums': scrum_list})

        sprint = Sprint.objects.get(jira_id=self.kwargs['jira_id'])

        epics = {}
        for issue_type in ('completed', 'incompleted', 'punted'):
            epics[issue_type] = []
            for epic, issues in groupby(
                    getattr(sprint, issue_type + '_issues').order_by('epic'),
                    get_epic):
                issue_list = list(issues)
                timespent = sum([i.timespent for i in issue_list])
                epics[issue_type].append((epic, timespent, issue_list))
        context.update({
            'all_issues': [
                {
                    'issue_type': 'completed',
                    'color': '#EEFFEE',
                    'epics': epics['completed'],
                    'total': (
                        sprint.sum_completed_timespent() or 0)},
                {
                    'issue_type': 'incompleted',
                    'color': '#FFEEEE',
                    'epics': epics['incompleted'],
                    'total': (
                        sprint.sum_incompleted_timespent() or 0)},
                {
                    'issue_type': 'punted',
                    'color': '#FFFFEE',
                    'epics': epics['punted'],
                    'total': (
                        sprint.sum_punted_timespent() or 0)}, ],
            'sprint': sprint})
        return context


class LoadData(LoginRequiredMixin, View):
    def get_from_jira(self, url, resource_name):
        r = requests.get(
            JIRA_REST_URL + url,
            verify=False,
            auth=(
                self.jira_username,
                self.jira_password))
        if r.status_code != 200:
            raise Exception("<br/>\n".join((
                "Error getting resource '{}' from JIRA.".format(
                    resource_name),
                "Status code: {}".format(
                    r.status_code),
                "")))
        time.sleep(1.0)  # JIRA now limits rate, and 2s is not enough
        return json.loads(
            r.content.decode('utf-8')
        )

    def generate_data(self, request):
        # This wart is here because grasshopper needs a rapidview (also
        # known as scrum) ID to get the sprints (so, no, there is no fucking
        # way to just get all the sprints).
        # See:
        # https://support.neoxam.com/rest/greenhopper/1.0/application.wadl

        # Also this. Just so the user don't click the big X while the objs load

        scrum_id = int(request.POST.get('scrum_id', 0))
        scrum = Scrum.objects.filter(jira_id=scrum_id).first()

        sprint_id = int(request.POST.get('sprint_id', 0))
        sprint = Sprint.objects.filter(jira_id=sprint_id).first()

        self.jira_username = request.session['nxuser'].ldap_username
        self.jira_password = request.session['nxuser'].ldap_password

        resource_to_url = OrderedDict((
            ('projects', 'api/2/project'),
            ('scrums', 'greenhopper/latest/rapidview'),
            ('sprints', 'greenhopper/latest/sprintquery/{}'.format(scrum_id)),
            ('issues', 'greenhopper/latest/rapid/charts/sprintreport' +
             '?rapidViewId={}&sprintId={}'.format(
                 scrum_id, sprint_id, ))))

        resources = request.POST.getlist(
            'resources',
            resource_to_url.keys())

        for resource in resources:
            url = resource_to_url[resource]
            try:
                nb_created = 0
                nb_updated = 0

                json_data = self.get_from_jira(url, resource)

                if resource == 'projects':
                    for item in json_data:
                        p, created = Project.objects.update_or_create(
                            jira_id=item['id'],
                            defaults=dict(
                                key=item['key'],
                                name=item['name'],
                            )
                        )
                        if created:
                            nb_created += 1
                        else:
                            nb_updated += 1

                if resource == 'scrums':
                    for item in json_data['views']:
                        p, created = Scrum.objects.update_or_create(
                            jira_id=item['id'],
                            defaults=dict(
                                name=item['name'],
                            )
                        )
                        if created:
                            nb_created += 1
                        else:
                            nb_updated += 1

                if resource == 'sprints':
                    for item in json_data['sprints']:
                        sprint_url = (
                            "greenhopper/latest/rapid/charts/" +
                            "sprintreport?rapidViewId={scrum_jira_id}" +
                            "&sprintId={sprint_jira_id}").format(
                            scrum_jira_id=scrum_id,
                            sprint_jira_id=item['id'], )

                        sprint_item = self.get_from_jira(
                            sprint_url, 'sprints')['sprint']

                        if sprint_item['completeDate'] == "None":
                            complete_date = None
                        elif not isinstance(sprint_item['completeDate'], str):
                            complete_date = None
                        else:
                            complete_date = prs(sprint_item['completeDate']),
                        if isinstance(complete_date, tuple):
                            # Why the fuck?
                            complete_date = complete_date[0]
                        p, created = Sprint.objects.update_or_create(
                            jira_id=sprint_item['id'],
                            defaults=dict(
                                scrum=scrum,
                                name=sprint_item['name'],
                                closed=(sprint_item['state'] == 'CLOSED'),
                                start_date=prs(sprint_item['startDate']),
                                end_date=prs(sprint_item['endDate']),
                                complete_date=complete_date,
                            )
                        )
                        if created:
                            nb_created += 1
                            yield "Created sprint {}<br/>\n".format(
                                sprint_item['name'])
                        else:
                            nb_updated += 1
                            yield "Updated sprint {}<br/>".format(
                                sprint_item['name'])

                if resource == 'issues':
                    for issue_type in (
                            'completedIssues',
                            'issuesNotCompletedInCurrentSprint',
                            'puntedIssues'):  # issuesCompletedInAnotherSprint ?
                        if issue_type == 'completedIssues':
                            sprint.completed_issues.clear()
                            yield "Cleared completed issues.<br/>"
                        elif issue_type == 'issuesNotCompletedInCurrentSprint':
                            sprint.incompleted_issues.clear()
                            yield "Cleared incompleted issues.<br/>"
                        elif issue_type == 'puntedIssues':
                            sprint.punted_issues.clear()
                            yield "Cleared punted issues.<br/>"
                        else:
                            raise Exception(
                                "Unexpected issue type when clearing: " + issue_type)
                        for item in json_data['contents'][issue_type]:
                            epic_custom_field = 'customfield_10553'
                            issue_url = (
                                'api/2/issue/{issue_jira_id}?' +
                                'fields=summary,timespent,subtasks,' + epic_custom_field).format(
                                issue_jira_id=item['id'], )
                            issue_item = self.get_from_jira(
                                issue_url, 'issue')
                            issue_fields = issue_item['fields']

                            # If issue is linked to an epic issue:
                            epic_key = issue_fields.get(epic_custom_field)
                            if epic_key:
                                # Get epic
                                color_custom_field = 'customfield_10556'
                                summary_custom_field = 'customfield_10554'
                                epic_url = (
                                    'api/2/issue/{epic_key}?' +
                                    'fields=timespent,' + color_custom_field + ',' + summary_custom_field).format(
                                    epic_key=epic_key, )
                                epic_item = self.get_from_jira(
                                    epic_url, 'epic')
                                epic_fields = epic_item['fields']
                                epic, created = Issue.objects.update_or_create(
                                    jira_id=epic_item['id'],
                                    defaults=dict(
                                        key=epic_item['key'],
                                        summary=epic_fields[summary_custom_field],
                                        timespent=(epic_fields['timespent'] or 0) / (60 * 60 * 8),
                                        epic_color=epic_fields.get(color_custom_field) or ''
                                    )
                                )
                            else:
                                epic = None

                            issue, created = Issue.objects.update_or_create(
                                jira_id=issue_item['id'],
                                defaults=dict(
                                    key=issue_item['key'],
                                    summary=issue_fields['summary'],
                                    timespent=(issue_fields['timespent'] or 0) / (60 * 60 * 8),
                                    epic=epic
                                )
                            )
                            if issue_type == 'completedIssues':
                                sprint.completed_issues.add(issue)
                            elif issue_type == 'issuesNotCompletedInCurrentSprint':
                                sprint.incompleted_issues.add(issue)
                            elif issue_type == 'puntedIssues':
                                sprint.punted_issues.add(issue)
                            else:
                                raise Exception(
                                    "Unexpected issue typewhen adding: " + issue_type)

                            # Add timespent from subtasks
                            additional_timespent = 0
                            for subtask_summary in issue_fields.get('subtasks', []):
                                # Get epic
                                subtask_url = (
                                    'api/2/issue/{subtask_key}?' +
                                    'fields=timespent').format(
                                    subtask_key=subtask_summary['key'], )
                                subtask_item = self.get_from_jira(
                                    subtask_url, 'subtask')
                                subtask_fields = subtask_item['fields']
                                additional_timespent += ((subtask_fields['timespent'] or 0) / (60 * 60 * 8))
                                yield "&nbsp;Visited subtask {}<br/>\n".format(
                                    subtask_summary['key'])
                            issue.timespent += additional_timespent
                            issue.save()
                            if created:
                                nb_created += 1
                                yield "Created issue {}<br/>\n".format(
                                    issue_item['key'])
                            else:
                                nb_updated += 1
                                yield "Updated issue {}<br/>".format(
                                    issue_item['key'])
            except BaseException as e:
                yield ("An exception occured when fetching {resource}:" + \
                       " {e}<br/>\n").format(
                    resource=resource,
                    e=e)
                error = e
            else:
                yield """Resource <em>{resource}</em> loaded OK.<br/>
                {nb_created} created.<br/>
                {nb_updated} updated.<br/><br/>\n""".format(
                    resource=resource,
                    nb_created=nb_created,
                    nb_updated=nb_updated)
                error = None
        yield """<br/>
<a href="{next}"><input type="submit" value="OK"/></a>
        """.format(
            next=request.GET.get(
                'next',
                request.META.get(
                    'HTTP_REFERER',
                    '/')))
        if error:
            raise error

    def post(self, request):
        return StreamingHttpResponse(self.generate_data(request))
