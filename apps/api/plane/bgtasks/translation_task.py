from celery import shared_task

from plane.db.models import Translation
from plane.services.translation_service import translation_service


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def translate_content(self, translation_id: str):
    translation = Translation.objects.get(pk=translation_id)
    translation.status = Translation.Status.PENDING
    translation.save(update_fields=["status", "updated_at"])
    try:
        source_language = translation.source_language or translation_service.detect_language(translation.original_text)
        translation.source_language = source_language
        if source_language == translation.target_language:
            translation.translated_text = translation.original_text
            translation.status = Translation.Status.SKIPPED
        else:
            translation.translated_text = translation_service.translate(
                translation.original_text, source_language, translation.target_language
            )
            translation.status = Translation.Status.COMPLETED
        translation.error_message = ""
        translation.save(
            update_fields=["source_language", "translated_text", "status", "error_message", "updated_at"]
        )
    except Exception as exc:
        translation.status = Translation.Status.FAILED
        translation.error_message = str(exc)[:1000]
        translation.save(update_fields=["status", "error_message", "updated_at"])
        raise self.retry(exc=exc)


def queue_translations(*, workspace_id, content_type: str, content_id, field: str, text: str):
    """Upsert both audience languages and queue the non-blocking work after persistence."""
    if not text or not text.strip() or text in ("<p></p>", "<p></p>\n"):
        return
    for target_language in translation_service.SUPPORTED_TARGETS:
        translation, _ = Translation.objects.update_or_create(
            content_type=content_type,
            content_id=content_id,
            field=field,
            target_language=target_language,
            defaults={
                "workspace_id": workspace_id,
                "original_text": text,
                "source_language": "",
                "translated_text": "",
                "status": Translation.Status.PENDING,
                "error_message": "",
            },
        )
        translate_content.delay(str(translation.id))
