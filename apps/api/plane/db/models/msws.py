# Copyright (c) 2026 Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Persistent data for the Multilingual Smart Work Scheduler extension."""

from django.db import models

from .base import BaseModel


class WorkspaceSchedulerSettings(BaseModel):
    """Workspace-level configuration kept separate from Plane's core Workspace model."""

    workspace = models.OneToOneField("db.Workspace", on_delete=models.CASCADE, related_name="scheduler_settings")
    google_calendar_embed_url = models.URLField(blank=True, default="")

    class Meta:
        db_table = "workspace_scheduler_settings"


class Translation(BaseModel):
    class ContentType(models.TextChoices):
        ISSUE = "issue", "Issue"
        COMMENT = "comment", "Comment"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="translations")
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    content_id = models.UUIDField(db_index=True)
    field = models.CharField(max_length=30, default="body")
    original_text = models.TextField()
    source_language = models.CharField(max_length=12, blank=True, default="")
    translated_text = models.TextField(blank=True, default="")
    target_language = models.CharField(max_length=12)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "translations"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "content_id", "field", "target_language"],
                name="translation_content_field_language_unique",
            )
        ]
        indexes = [models.Index(fields=["workspace", "content_type", "content_id"])]
