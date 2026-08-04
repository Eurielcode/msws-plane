# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Unit tests for MSWSTranslationsMixin: correct per-object attribution when
serializing a list (and no N+1 query per row), and that a single/nested
serialization still works without a real list-serializer root.
"""

import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection

from plane.app.serializers.issue import IssueCommentSerializer
from plane.db.models import IssueComment, Translation
from plane.tests.factories import IssueFactory, ProjectFactory, UserFactory, WorkspaceFactory


@pytest.mark.django_db
class TestMSWSTranslationsMixin:
    def _make_comment(self, project, issue, actor):
        return IssueComment.objects.create(project=project, issue=issue, actor=actor, comment_html="<p>hi</p>")

    def test_list_serialization_batches_into_a_single_query_and_keeps_rows_distinct(self):
        workspace = WorkspaceFactory()
        project = ProjectFactory(workspace=workspace)
        issue = IssueFactory(project=project, workspace=workspace)
        actor = UserFactory(username="msws-mixin-actor")

        comment_a = self._make_comment(project, issue, actor)
        comment_b = self._make_comment(project, issue, actor)

        Translation.objects.create(
            workspace=workspace,
            content_type=Translation.ContentType.COMMENT,
            content_id=comment_a.id,
            field="comment",
            original_text="hi",
            target_language="ja",
            source_language="en",
            translated_text="こんにちは",
            status=Translation.Status.COMPLETED,
        )
        Translation.objects.create(
            workspace=workspace,
            content_type=Translation.ContentType.COMMENT,
            content_id=comment_b.id,
            field="comment",
            original_text="hi",
            target_language="ja",
            source_language="en",
            translated_text="やあ",
            status=Translation.Status.COMPLETED,
        )

        comments = IssueComment.objects.filter(id__in=[comment_a.id, comment_b.id])
        with CaptureQueriesContext(connection) as ctx:
            data = IssueCommentSerializer(comments, many=True).data
            translation_queries = [q for q in ctx.captured_queries if '"translations"' in q["sql"]]
            assert len(translation_queries) == 1

        by_id = {row["id"]: row for row in data}
        assert by_id[comment_a.id]["translations"][0]["translated_text"] == "こんにちは"
        assert by_id[comment_b.id]["translations"][0]["translated_text"] == "やあ"

    def test_single_object_serialization_still_returns_its_own_translations(self):
        workspace = WorkspaceFactory()
        project = ProjectFactory(workspace=workspace)
        issue = IssueFactory(project=project, workspace=workspace)
        actor = UserFactory(username="msws-mixin-single-actor")
        comment = self._make_comment(project, issue, actor)
        Translation.objects.create(
            workspace=workspace,
            content_type=Translation.ContentType.COMMENT,
            content_id=comment.id,
            field="comment",
            original_text="hi",
            target_language="ja",
            source_language="en",
            translated_text="こんにちは",
            status=Translation.Status.COMPLETED,
        )

        data = IssueCommentSerializer(comment).data

        assert data["translations"][0]["translated_text"] == "こんにちは"
