/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";

import { useTranslation } from "@plane/i18n";
import { CloseIcon, TrashIcon } from "@plane/propel/icons";
import { Tooltip } from "@plane/propel/tooltip";
import type { TIssueServiceType } from "@plane/types";
import { EIssueServiceType } from "@plane/types";
// ui
import { CustomMenu } from "@plane/ui";
import { convertBytesToSize, getFileExtension, getFileName, getFileURL, renderFormattedDate } from "@plane/utils";
// components
//
import { ButtonAvatars } from "@/components/dropdowns/member/avatar";
import { getFileIcon } from "@/components/icons";
// helpers
// hooks
import { useIssueDetail } from "@/hooks/store/use-issue-detail";
import { useMember } from "@/hooks/store/use-member";
import { usePlatformOS } from "@/hooks/use-platform-os";

type TIssueAttachmentsListItem = {
  attachmentId: string;
  disabled?: boolean;
  issueServiceType?: TIssueServiceType;
};

const IMAGE_EXTENSIONS = new Set(["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "svg"]);
const VIDEO_EXTENSIONS = new Set(["mp4", "mpeg", "mpg", "ogv", "webm", "mov", "avi", "wmv"]);

export const IssueAttachmentsListItem = observer(function IssueAttachmentsListItem(props: TIssueAttachmentsListItem) {
  const { t } = useTranslation();
  // props
  const { attachmentId, disabled, issueServiceType = EIssueServiceType.ISSUES } = props;
  // store hooks
  const { getUserDetails } = useMember();
  const {
    attachment: { getAttachmentById },
    toggleDeleteAttachmentModal,
  } = useIssueDetail(issueServiceType);
  // derived values
  const attachment = attachmentId ? getAttachmentById(attachmentId) : undefined;
  const fileName = getFileName(attachment?.attributes.name ?? "");
  const fileExtension = getFileExtension(attachment?.attributes.name ?? "");
  const fileIcon = getFileIcon(fileExtension, 18);
  const fileURL = getFileURL(attachment?.asset_url ?? "");
  const lowerExtension = fileExtension.toLowerCase();
  const isImage = IMAGE_EXTENSIONS.has(lowerExtension);
  const isVideo = VIDEO_EXTENSIONS.has(lowerExtension);
  // hooks
  const { isMobile } = usePlatformOS();
  // state
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);

  if (!attachment) return <></>;

  const deleteMenu = (
    <CustomMenu ellipsis closeOnSelect placement="bottom-end" disabled={disabled}>
      <CustomMenu.MenuItem
        onClick={() => {
          toggleDeleteAttachmentModal(attachmentId);
        }}
      >
        <div className="flex items-center gap-2">
          <TrashIcon className="h-3.5 w-3.5" strokeWidth={2} />
          <span>{t("common.actions.delete")}</span>
        </div>
      </CustomMenu.MenuItem>
    </CustomMenu>
  );

  // Feed-style inline preview for image/video attachments, so photos and
  // videos show up directly in the panel instead of requiring a click-through
  // (and, for video, a download) per file.
  if (isImage || isVideo) {
    return (
      <div className="group flex flex-col gap-2 py-2">
        {isLightboxOpen && (
          <div
            role="dialog"
            aria-modal="true"
            aria-label={`${fileName}.${fileExtension}`}
            tabIndex={-1}
            className="fixed inset-0 z-30 flex items-center justify-center bg-backdrop p-4"
            onClick={() => setIsLightboxOpen(false)}
            onKeyDown={(e) => {
              if (e.key === "Escape") setIsLightboxOpen(false);
            }}
          >
            <button
              type="button"
              className="absolute top-4 right-4 flex size-9 items-center justify-center rounded-full bg-surface-1/80 text-primary"
              aria-label={t("common.actions.close")}
              onClick={() => setIsLightboxOpen(false)}
            >
              <CloseIcon className="size-5" />
            </button>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={fileURL}
              alt={`${fileName}.${fileExtension}`}
              className="max-h-full max-w-full rounded-md object-contain"
            />
          </div>
        )}
        {isVideo ? (
          // eslint-disable-next-line jsx-a11y/media-has-caption
          <video src={fileURL} controls preload="metadata" className="aspect-square w-full object-cover" />
        ) : (
          <button type="button" className="block w-full" onClick={() => setIsLightboxOpen(true)}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={fileURL} alt={`${fileName}.${fileExtension}`} className="aspect-square w-full object-cover" />
          </button>
        )}
        <div className="flex items-center justify-between gap-3 pr-2 pl-9 text-13">
          <div className="flex min-w-0 items-center gap-3">
            <Tooltip tooltipContent={`${fileName}.${fileExtension}`} isMobile={isMobile}>
              <p className="truncate font-medium text-secondary">{`${fileName}.${fileExtension}`}</p>
            </Tooltip>
            <span className="flex size-1.5 flex-shrink-0 rounded-full bg-layer-1" />
            <span className="flex-shrink-0 text-placeholder">{convertBytesToSize(attachment.attributes.size)}</span>
          </div>
          <div className="flex flex-shrink-0 items-center gap-3">
            {attachment?.created_by && (
              <Tooltip
                isMobile={isMobile}
                tooltipContent={`${
                  getUserDetails(attachment?.created_by)?.display_name ?? ""
                } uploaded on ${renderFormattedDate(attachment.updated_at)}`}
              >
                <div className="flex items-center justify-center">
                  <ButtonAvatars showTooltip userIds={attachment?.created_by} />
                </div>
              </Tooltip>
            )}
            {deleteMenu}
          </div>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        window.open(fileURL, "_blank");
      }}
    >
      <div className="group flex h-11 items-center justify-between gap-3 pr-2 pl-9 hover:bg-surface-2">
        <div className="flex items-center gap-3 truncate text-13">
          <div className="flex items-center gap-3">{fileIcon}</div>
          <Tooltip tooltipContent={`${fileName}.${fileExtension}`} isMobile={isMobile}>
            <p className="truncate font-medium text-secondary">{`${fileName}.${fileExtension}`}</p>
          </Tooltip>
          <span className="flex size-1.5 rounded-full bg-layer-1" />
          <span className="flex-shrink-0 text-placeholder">{convertBytesToSize(attachment.attributes.size)}</span>
        </div>

        <div className="flex items-center gap-3">
          {attachment?.created_by && (
            <Tooltip
              isMobile={isMobile}
              tooltipContent={`${
                getUserDetails(attachment?.created_by)?.display_name ?? ""
              } uploaded on ${renderFormattedDate(attachment.updated_at)}`}
            >
              <div className="flex items-center justify-center">
                <ButtonAvatars showTooltip userIds={attachment?.created_by} />
              </div>
            </Tooltip>
          )}

          {deleteMenu}
        </div>
      </div>
    </button>
  );
});
