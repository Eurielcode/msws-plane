# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Contract tests for the MSWS manager dashboard endpoint: role gating,
employee/progress/overdue aggregation, and the Google Calendar embed URL
validation (shared-view iframe only, no OAuth, no event writes).
"""

from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from plane.db.models import IssueAssignee, State, WorkspaceMember, WorkspaceSchedulerSettings
from plane.tests.factories import IssueFactory, ProjectFactory, ProjectMemberFactory, UserFactory


@pytest.mark.contract
@pytest.mark.django_db
class TestManagerDashboardEndpoint:
    def test_requires_workspace_admin_role(self, api_client, workspace, create_user):
        member = UserFactory(username="msws-non-admin-member")
        WorkspaceMember.objects.create(workspace=workspace, member=member, role=15)  # MEMBER, not ADMIN
        api_client.force_authenticate(user=member)

        response = api_client.get(reverse("manager-dashboard", kwargs={"slug": workspace.slug}))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_sees_employees_progress_and_overdue_counts(self, session_client, workspace, create_user):
        project = ProjectFactory(workspace=workspace, created_by=create_user)
        ProjectMemberFactory(project=project, member=create_user, workspace=workspace, role=20)
        todo_state = State.objects.create(
            project=project, workspace=workspace, name="Todo", color="#000", group="backlog"
        )
        done_state = State.objects.create(
            project=project, workspace=workspace, name="Done", color="#0f0", group="completed"
        )

        overdue_issue = IssueFactory(
            project=project, workspace=workspace, state=todo_state, target_date=date.today() - timedelta(days=2)
        )
        IssueAssignee.objects.create(issue=overdue_issue, assignee=create_user, project=project, workspace=workspace)

        done_issue = IssueFactory(project=project, workspace=workspace, state=todo_state)
        IssueAssignee.objects.create(issue=done_issue, assignee=create_user, project=project, workspace=workspace)
        done_issue.state = done_state
        done_issue.save()

        response = session_client.get(reverse("manager-dashboard", kwargs={"slug": workspace.slug}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["summary"]["assigned"] == 2
        assert response.data["summary"]["completed"] == 1
        assert response.data["summary"]["overdue"] == 1
        employee = next(row for row in response.data["employees"] if row["id"] == str(create_user.id))
        assert employee["assigned"] == 2
        assert employee["completed"] == 1
        assert employee["progress"] == 50

    def test_patch_accepts_a_google_calendar_embed_url(self, session_client, workspace):
        url = reverse("manager-dashboard", kwargs={"slug": workspace.slug})
        embed_url = "https://calendar.google.com/calendar/embed?src=team%40example.com"

        response = session_client.patch(url, {"google_calendar_embed_url": embed_url}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["google_calendar_embed_url"] == embed_url
        settings = WorkspaceSchedulerSettings.objects.get(workspace=workspace)
        assert settings.google_calendar_embed_url == embed_url

    def test_patch_rejects_a_non_google_calendar_url(self, session_client, workspace):
        url = reverse("manager-dashboard", kwargs={"slug": workspace.slug})

        response = session_client.patch(url, {"google_calendar_embed_url": "https://evil.example.com/x"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not WorkspaceSchedulerSettings.objects.filter(
            workspace=workspace, google_calendar_embed_url="https://evil.example.com/x"
        ).exists()
