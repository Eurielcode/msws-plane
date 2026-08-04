import { useMemo } from "react";
import { Languages } from "lucide-react";
import { LiteTextEditor } from "@/components/editor/lite-text";

type Translation = {
  field: string;
  target_language: string;
  translated_text: string;
};

type Props = {
  translations?: Translation[];
  field: string;
  workspaceId: string;
  workspaceSlug: string;
  projectId?: string;
};

export function TranslatedContent({ translations, field, workspaceId, workspaceSlug, projectId }: Props) {
  const targetLanguage = typeof navigator !== "undefined" && navigator.language.toLowerCase().startsWith("ja") ? "ja" : "en";
  const translation = useMemo(
    () => translations?.find((item) => item.field === field && item.target_language === targetLanguage),
    [field, targetLanguage, translations]
  );

  if (!translation?.translated_text) return null;
  return (
    <div className="mt-3 border-t border-subtle pt-3">
      <div className="mb-1 flex items-center gap-1.5 text-body-xs-medium text-secondary">
        <Languages className="size-3.5" /> Translated automatically
      </div>
      <LiteTextEditor
        editable={false}
        id={`translation-${field}`}
        initialValue={translation.translated_text}
        workspaceId={workspaceId}
        workspaceSlug={workspaceSlug}
        projectId={projectId}
        parentClassName="border-none"
        containerClassName="!py-1"
        displayConfig={{ fontSize: "small-font" }}
      />
    </div>
  );
}

export function TranslatedText({ translations, field }: Pick<Props, "translations" | "field">) {
  const targetLanguage = typeof navigator !== "undefined" && navigator.language.toLowerCase().startsWith("ja") ? "ja" : "en";
  const translation = useMemo(
    () => translations?.find((item) => item.field === field && item.target_language === targetLanguage),
    [field, targetLanguage, translations]
  );

  if (!translation?.translated_text) return null;
  return (
    <div className="-mt-2 mb-2 flex items-center gap-1.5 text-body-sm-regular text-secondary">
      <Languages className="size-3.5" />
      <span>{translation.translated_text}</span>
    </div>
  );
}
