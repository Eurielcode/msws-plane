import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import { CalendarDays, CheckCircle2, CircleAlert, Users } from "lucide-react";
import { Button } from "@plane/propel/button";
import { AppHeader } from "@/components/core/app-header";
import { ContentWrapper } from "@/components/core/content-wrapper";
import { PageHead } from "@/components/core/page-title";
import { MSWSService, type TManagerDashboard } from "@/services/msws.service";
import { useWorkspace } from "@/hooks/store/use-workspace";

const mswsService = new MSWSService();

function ManagerDashboardPage() {
  const { currentWorkspace } = useWorkspace();
  const [dashboard, setDashboard] = useState<TManagerDashboard>();
  const [calendarUrl, setCalendarUrl] = useState("");
  const [error, setError] = useState("");
  const workspaceSlug = currentWorkspace?.slug;

  useEffect(() => {
    if (!workspaceSlug) return;
    mswsService.getManagerDashboard(workspaceSlug).then((data) => {
      setDashboard(data);
      setCalendarUrl(data.google_calendar_embed_url);
    }).catch(() => setError("Unable to load the manager dashboard."));
  }, [workspaceSlug]);

  const saveCalendar = async () => {
    if (!workspaceSlug) return;
    try {
      const data = await mswsService.updateCalendar(workspaceSlug, calendarUrl);
      setCalendarUrl(data.google_calendar_embed_url);
      setError("");
    } catch {
      setError("Use a Google Calendar embed URL.");
    }
  };
  const summary = dashboard?.summary;
  const cards = [
    ["Employees", dashboard?.employees.length ?? 0, Users],
    ["Assigned work", summary?.assigned ?? 0, CalendarDays],
    ["Completed", summary?.completed ?? 0, CheckCircle2],
    ["Overdue", summary?.overdue ?? 0, CircleAlert],
  ] as const;

  return (
    <>
      <AppHeader header={<div className="text-body-md-medium">Manager dashboard</div>} />
      <ContentWrapper className="p-5 md:p-8">
        <PageHead title={`${currentWorkspace?.name ?? "Workspace"} - Manager dashboard`} />
        <div className="mx-auto max-w-7xl space-y-6">
          <div><h1 className="text-heading-xlg-semibold">Manager dashboard</h1><p className="mt-1 text-body-sm-regular text-secondary">Today’s team workload and shared schedule.</p></div>
          {error && <p className="text-body-sm-regular text-danger">{error}</p>}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {cards.map(([label, value, Icon]) => <div key={label} className="rounded-lg border border-subtle bg-layer-1 p-4 shadow-raised-100"><Icon className="mb-4 size-5 text-secondary" /><p className="text-body-sm-regular text-secondary">{label}</p><p className="mt-1 text-heading-lg-semibold">{value}</p></div>)}
          </div>
          <div className="grid gap-6 xl:grid-cols-2">
            <section className="rounded-lg border border-subtle bg-layer-1"><div className="border-b border-subtle px-5 py-4 text-body-md-medium">Employee progress</div><div className="divide-y divide-subtle">{dashboard?.employees.map((employee) => <div key={employee.id} className="px-5 py-4"><div className="flex justify-between gap-4"><div><p className="text-body-sm-medium">{employee.name}</p><p className="text-body-xs-regular text-secondary">{employee.assigned} assigned · {employee.completed} completed</p></div><span className="text-body-sm-medium">{employee.progress}%</span></div><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-layer-3"><div className="h-full rounded-full bg-accent-primary" style={{ width: `${employee.progress}%` }} /></div></div>)}</div></section>
            <section className="rounded-lg border border-subtle bg-layer-1"><div className="border-b border-subtle px-5 py-4 text-body-md-medium">Shared Google Calendar</div><div className="space-y-3 p-5"><input value={calendarUrl} onChange={(event) => setCalendarUrl(event.target.value)} placeholder="Paste Google Calendar embed URL" className="w-full rounded-md border border-subtle bg-layer-1 px-3 py-2 text-body-sm-regular" /><Button variant="secondary" onClick={saveCalendar}>Save calendar</Button>{calendarUrl ? <iframe title="Shared Google Calendar" src={calendarUrl} className="h-[420px] w-full rounded-md border border-subtle" /> : <p className="py-12 text-center text-body-sm-regular text-secondary">Add a shared calendar embed URL to show the team schedule.</p>}</div></section>
          </div>
        </div>
      </ContentWrapper>
    </>
  );
}

export default observer(ManagerDashboardPage);
