from datetime import date

from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.db.models import Issue, Workspace, WorkspaceMember, WorkspaceSchedulerSettings

from .base import BaseAPIView


class ManagerDashboardEndpoint(BaseAPIView):
    """Read and update the small manager-facing MSWS dashboard payload."""

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def get(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        today = date.today()
        issues = Issue.issue_objects.filter(workspace=workspace, is_draft=False)
        employees = WorkspaceMember.objects.filter(workspace=workspace, is_active=True).select_related("member")

        # One aggregate query for every member's assigned/completed counts,
        # instead of two queries per employee in a loop.
        stats_by_member = {
            row["assignees"]: row
            for row in issues.values("assignees").annotate(
                total=Count("id", distinct=True),
                completed=Count("id", filter=Q(completed_at__isnull=False), distinct=True),
            )
            if row["assignees"] is not None
        }

        employee_rows = []
        for membership in employees:
            stats = stats_by_member.get(membership.member_id, {"total": 0, "completed": 0})
            total, completed = stats["total"], stats["completed"]
            employee_rows.append(
                {
                    "id": str(membership.member_id),
                    "name": membership.member.display_name or membership.member.email,
                    "email": membership.member.email,
                    "assigned": total,
                    "completed": completed,
                    "progress": round((completed / total) * 100) if total else 0,
                }
            )
        settings, _ = WorkspaceSchedulerSettings.objects.get_or_create(workspace=workspace)
        return Response(
            {
                "employees": employee_rows,
                "summary": {
                    "assigned": issues.count(),
                    "completed": issues.filter(completed_at__isnull=False).count(),
                    "overdue": issues.filter(target_date__lt=today, completed_at__isnull=True).count(),
                    "due_today": issues.filter(target_date=today, completed_at__isnull=True).count(),
                },
                "google_calendar_embed_url": settings.google_calendar_embed_url,
            }
        )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def patch(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        url = request.data.get("google_calendar_embed_url", "")
        is_google_calendar_url = url.startswith("https://calendar.google.com/") or url.startswith(
            "https://www.google.com/calendar/"
        )
        if url and not is_google_calendar_url:
            return Response(
                {"google_calendar_embed_url": "A Google Calendar embed URL is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        settings, _ = WorkspaceSchedulerSettings.objects.get_or_create(workspace=workspace)
        settings.google_calendar_embed_url = url
        settings.save(update_fields=["google_calendar_embed_url", "updated_at"])
        return Response({"google_calendar_embed_url": settings.google_calendar_embed_url})
