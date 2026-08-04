# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Unit tests for the MSWS automatic-translation pipeline: queueing both
audience languages on write, and the Celery task that resolves them
(same-language skip, missing-API-key failure with a retry).
"""

from unittest.mock import patch
from uuid import uuid4

import pytest

from plane.bgtasks.translation_task import queue_translations, translate_content
from plane.db.models import Translation
from plane.services.translation_service import translation_service
from plane.tests.factories import WorkspaceFactory


@pytest.mark.django_db
class TestQueueTranslations:
    @patch("plane.bgtasks.translation_task.translate_content.delay")
    def test_creates_a_pending_row_per_supported_target_language(self, mock_delay):
        workspace = WorkspaceFactory()
        content_id = uuid4()

        queue_translations(
            workspace_id=workspace.id,
            content_type="issue",
            content_id=content_id,
            field="name",
            text="Please review the deployment plan before Friday",
        )

        rows = Translation.objects.filter(content_id=content_id)
        assert {row.target_language for row in rows} == set(translation_service.SUPPORTED_TARGETS)
        assert all(row.status == Translation.Status.PENDING for row in rows)
        assert mock_delay.call_count == rows.count()

    @patch("plane.bgtasks.translation_task.translate_content.delay")
    def test_skips_empty_or_blank_html(self, mock_delay):
        workspace = WorkspaceFactory()

        for empty in ("", "   ", "<p></p>", "<p></p>\n"):
            queue_translations(
                workspace_id=workspace.id,
                content_type="issue",
                content_id=uuid4(),
                field="description",
                text=empty,
            )

        assert Translation.objects.count() == 0
        mock_delay.assert_not_called()

    @patch("plane.bgtasks.translation_task.translate_content.delay")
    def test_upserts_instead_of_duplicating_on_repeated_edits(self, mock_delay):
        workspace = WorkspaceFactory()
        content_id = uuid4()

        queue_translations(
            workspace_id=workspace.id, content_type="issue", content_id=content_id, field="name", text="First draft"
        )
        queue_translations(
            workspace_id=workspace.id,
            content_type="issue",
            content_id=content_id,
            field="name",
            text="Revised draft",
        )

        rows = Translation.objects.filter(content_id=content_id, field="name")
        assert rows.count() == 2  # one per target language, not four
        assert all(row.original_text == "Revised draft" for row in rows)
        assert all(row.status == Translation.Status.PENDING for row in rows)


@pytest.mark.django_db
class TestTranslateContentTask:
    def _make_translation(self, **overrides):
        workspace = WorkspaceFactory()
        defaults = {
            "workspace": workspace,
            "content_type": Translation.ContentType.ISSUE,
            "content_id": uuid4(),
            "field": "name",
            "original_text": "Please review the deployment plan before Friday",
            "target_language": "ja",
        }
        defaults.update(overrides)
        return Translation.objects.create(**defaults)

    def test_same_language_is_marked_skipped_without_calling_openai(self):
        translation = self._make_translation(target_language="en")

        with patch("plane.services.translation_service.translation_service.translate") as mock_translate:
            translate_content.apply(args=[str(translation.id)])

        mock_translate.assert_not_called()
        translation.refresh_from_db()
        assert translation.status == Translation.Status.SKIPPED
        assert translation.source_language == "en"
        assert translation.translated_text == translation.original_text

    def test_missing_api_key_fails_cleanly_and_schedules_a_retry(self):
        translation = self._make_translation(target_language="ja")

        result = translate_content.apply(args=[str(translation.id)])

        translation.refresh_from_db()
        assert translation.status == Translation.Status.FAILED
        assert "OPENAI_API_KEY" in translation.error_message
        assert result.state in ("RETRY", "FAILURE")

    def test_successful_translation_is_persisted_without_touching_the_original(self):
        translation = self._make_translation(
            original_text="Please review the deployment plan before Friday", target_language="ja"
        )

        with patch(
            "plane.services.translation_service.translation_service.translate",
            return_value="金曜日までに確認してください",
        ):
            translate_content.apply(args=[str(translation.id)])

        translation.refresh_from_db()
        assert translation.status == Translation.Status.COMPLETED
        assert translation.translated_text == "金曜日までに確認してください"
        assert translation.original_text == "Please review the deployment plan before Friday"
