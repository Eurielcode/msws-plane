# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Shared serializer logic for exposing MSWS translations on Issues and comments."""

from rest_framework import serializers

from plane.db.models import Translation


class MSWSTranslationsMixin(serializers.Serializer):
    """Adds a read-only `translations` field backed by the Translation model.

    Batches the lookup for list responses (one query for the whole page)
    instead of issuing a query per object, by reading the full instance list
    off the list serializer (`self.root`) the first time any child is
    rendered and caching the result on the shared `context`.
    """

    translation_content_type = None
    translations = serializers.SerializerMethodField()

    def get_translations(self, obj):
        cache_key = f"_msws_translations_{self.translation_content_type}"
        cache = self.context.setdefault(cache_key, {})
        if obj.id not in cache:
            root = self.root
            if isinstance(root, serializers.ListSerializer) and root.instance:
                ids = [instance.id for instance in root.instance]
            else:
                ids = [obj.id]
            rows = Translation.objects.filter(
                content_type=self.translation_content_type,
                content_id__in=ids,
                status__in=[Translation.Status.COMPLETED, Translation.Status.SKIPPED],
            ).values("content_id", "field", "source_language", "target_language", "translated_text", "status")
            cache.update({content_id: [] for content_id in ids})
            for row in rows:
                cache.setdefault(row["content_id"], []).append(row)
        return cache.get(obj.id, [])
