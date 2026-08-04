"""Single replaceable boundary for MSWS automatic translations."""

import os
import re


class TranslationService:
    SUPPORTED_TARGETS = ("en", "ja")

    def detect_language(self, text: str) -> str:
        # Japanese scripts are unambiguous for the MVP; OpenAI does the final detection otherwise.
        return "ja" if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text) else "en"

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if not text.strip() or source_language == target_language:
            return text

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        # Import here so local development remains usable before a key is configured.
        from openai import OpenAI

        response = OpenAI(api_key=api_key, timeout=30, max_retries=0).chat.completions.create(
            model=os.environ.get("MSWS_TRANSLATION_MODEL", "gpt-4o-mini"),
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the supplied Plane work item content. Preserve HTML tags, mentions, URLs, "
                        "identifiers, and formatting. Return only the translated content."
                    ),
                },
                {"role": "user", "content": f"Translate from {source_language} to {target_language}:\n{text}"},
            ],
        )
        return (response.choices[0].message.content or "").strip()


translation_service = TranslationService()
