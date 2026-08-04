import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export type TManagerDashboard = {
  employees: Array<{ id: string; name: string; email: string; assigned: number; completed: number; progress: number }>;
  summary: { assigned: number; completed: number; overdue: number; due_today: number };
  google_calendar_embed_url: string;
};

export class MSWSService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  getManagerDashboard(workspaceSlug: string): Promise<TManagerDashboard> {
    return this.get(`/api/workspaces/${workspaceSlug}/manager-dashboard/`).then((response) => response.data);
  }

  updateCalendar(workspaceSlug: string, google_calendar_embed_url: string): Promise<{ google_calendar_embed_url: string }> {
    return this.patch(`/api/workspaces/${workspaceSlug}/manager-dashboard/`, { google_calendar_embed_url }).then(
      (response) => response.data
    );
  }
}
