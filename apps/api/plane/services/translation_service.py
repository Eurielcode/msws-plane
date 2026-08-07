"""Single replaceable boundary for MSWS automatic translations."""

import os
import re


class TranslationService:
    SUPPORTED_TARGETS = ("en", "ja")

    def detect_language(self, text: str) -> str:
        # Japanese scripts are unambiguous for the MVP; Claude does the final detection otherwise.
        return "ja" if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text) else "en"

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if not text.strip() or source_language == target_language:
            return text

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")

        # Import here so local development remains usable before a key is configured.
        from anthropic import Anthropic

        response = Anthropic(api_key=api_key, timeout=30, max_retries=0).messages.create(
            model=os.environ.get("MSWS_TRANSLATION_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=4096,
            temperature=0,
            system=(
                "Translate the supplied Plane work item content. Preserve HTML tags, mentions, URLs, "
                "identifiers, and formatting. Return only the translated content."
            ),
            messages=[{"role": "user", "content": f"Translate from {source_language} to {target_language}:\n{text}"}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()


translation_service = TranslationService()
