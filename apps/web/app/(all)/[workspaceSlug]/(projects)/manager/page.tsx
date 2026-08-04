import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import { CalendarDays, CheckCircle2, CircleAlert, Users } from "lucide-react";
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { AppHeader } from "@/components/core/app-header";
import { ContentWrapper } from "@/components/core/content-wrapper";
import { PageHead } from "@/components/core/page-title";
import { MSWSService, type TManagerDashboard } from "@/services/msws.service";
import { useWorkspace } from "@/hooks/store/use-workspace";

const mswsService = new MSWSService();

function ManagerDashboardPage() {
  const { t } = useTranslation();
  const { currentWorkspace } = useWorkspace();
  const [dashboard, setDashboard] = useState<TManagerDashboard>();
  const [calendarUrl, setCalendarUrl] = useState("");
  // Kept separate from `calendarUrl` (the live input value) so the iframe only ever
  // embeds a URL the backend has validated as a Google Calendar shared view — never
  // whatever is mid-edit in the input.
  const [savedCalendarUrl, setSavedCalendarUrl] = useState("");
  const [error, setError] = useState("");
  const workspaceSlug = currentWorkspace?.slug;

  useEffect(() => {
    if (!workspaceSlug) return;
    const loadDashboard = async () => {
      try {
        const data = await mswsService.getManagerDashboard(workspaceSlug);
        setDashboard(data);
        setCalendarUrl(data.google_calendar_embed_url);
        setSavedCalendarUrl(data.google_calendar_embed_url);
      } catch {
        setError(t("msws_dashboard_load_error"));
      }
    };
    void loadDashboard();
  }, [workspaceSlug, t]);

  const saveCalendar = async () => {
    if (!workspaceSlug) return;
    try {
      const data = await mswsService.updateCalendar(workspaceSlug, calendarUrl);
      setCalendarUrl(data.google_calendar_embed_url);
      setSavedCalendarUrl(data.google_calendar_embed_url);
      setError("");
    } catch {
      setError(t("msws_calendar_url_error"));
    }
  };
  const summary = dashboard?.summary;
  const cards = [
    [t("msws_employees"), dashboard?.employees.length ?? 0, Users],
    [t("msws_assigned_work"), summary?.assigned ?? 0, CalendarDays],
    [t("msws_completed"), summary?.completed ?? 0, CheckCircle2],
    [t("msws_overdue"), summary?.overdue ?? 0, CircleAlert],
  ] as const;

  return (
    <>
      <AppHeader header={<div className="text-body-md-medium">{t("sidebar.manager_dashboard")}</div>} />
      <ContentWrapper className="p-5 md:p-8">
        <PageHead title={`${currentWorkspace?.name ?? "Workspace"} - ${t("sidebar.manager_dashboard")}`} />
        <div className="mx-auto max-w-7xl space-y-6">
          <div>
            <h1 className="text-h2-semibold">{t("sidebar.manager_dashboard")}</h1>
            <p className="mt-1 text-body-sm-regular text-secondary">{t("msws_manager_dashboard_subtitle")}</p>
          </div>
          {error && <p className="text-body-sm-regular text-danger-primary">{error}</p>}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {cards.map(([label, value, Icon]) => (
              <div key={label} className="rounded-lg border border-subtle bg-layer-1 p-4 shadow-raised-100">
                <Icon className="mb-4 size-5 text-secondary" />
                <p className="text-body-sm-regular text-secondary">{label}</p>
                <p className="mt-1 text-h3-semibold">{value}</p>
              </div>
            ))}
          </div>
          <div className="grid gap-6 xl:grid-cols-2">
            <section className="rounded-lg border border-subtle bg-layer-1">
              <div className="border-b border-subtle px-5 py-4 text-body-md-medium">{t("msws_employee_progress")}</div>
              <div className="divide-y divide-subtle">
                {dashboard?.employees.map((employee) => (
                  <div key={employee.id} className="px-5 py-4">
                    <div className="flex justify-between gap-4">
                      <div>
                        <p className="text-body-sm-medium">{employee.name}</p>
                        <p className="text-body-xs-regular text-secondary">
                          {t("msws_employee_summary", { assigned: employee.assigned, completed: employee.completed })}
                        </p>
                      </div>
                      <span className="text-body-sm-medium">{employee.progress}%</span>
                    </div>
                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-layer-3">
                      <div
                        className="h-full rounded-full bg-accent-primary"
                        style={{ width: `${employee.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>
            <section className="rounded-lg border border-subtle bg-layer-1">
              <div className="border-b border-subtle px-5 py-4 text-body-md-medium">
                {t("msws_shared_google_calendar")}
              </div>
              <div className="space-y-3 p-5">
                <input
                  value={calendarUrl}
                  onChange={(event) => setCalendarUrl(event.target.value)}
                  placeholder={t("msws_calendar_url_placeholder")}
                  className="w-full rounded-md border border-subtle bg-layer-1 px-3 py-2 text-body-sm-regular"
                />
                <Button variant="secondary" onClick={saveCalendar}>
                  {t("msws_save_calendar")}
                </Button>
                {savedCalendarUrl ? (
                  <iframe
                    title={t("msws_shared_google_calendar")}
                    src={savedCalendarUrl}
                    sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"
                    className="h-[420px] w-full rounded-md border border-subtle"
                  />
                ) : (
                  <p className="py-12 text-center text-body-sm-regular text-secondary">
                    {t("msws_calendar_empty_state")}
                  </p>
                )}
              </div>
            </section>
          </div>
        </div>
      </ContentWrapper>
    </>
  );
}

export default observer(ManagerDashboardPage);
