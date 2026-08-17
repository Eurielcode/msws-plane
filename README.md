# MSWS — Multilingual Smart Work Scheduler

MSWS is a project management tool built for teams that work across languages. It was designed around a simple, recurring problem: an employee writes a task update in their own language, and their manager — who reads and writes in a different one — has to wait for someone to translate it, or misses the context entirely.

MSWS solves that automatically. Whatever language a task, comment, or update is written in, the person reading it sees an automatic translation into their own language, shown right below the original text — never replacing it, always alongside it.

It was built as a focused extension on top of [Plane](https://plane.so), an open-source project management platform, rather than from scratch. Plane already provides a solid, well-tested foundation for issue tracking, projects, and workspaces — MSWS adds the multilingual and management-visibility layer on top of it.

## Core features

**1. Automatic bidirectional translation**
Every work item title, description, and comment is automatically translated between the languages in use on a team. The translation appears directly underneath the original text, generated in the background via the Claude API and cached so it only needs to be produced once per piece of content.

**2. Manager dashboard**
A dedicated view for managers to see, at a glance: who's on the team, what's assigned to each person, how much work is completed versus overdue, and overall team progress — without digging through individual projects.

**3. Shared calendar view**
A shared Google Calendar can be embedded directly into the workspace, so managers can see team availability and scheduling without switching tools or requiring calendar API access.

## How it's built

MSWS is a Django (Python) + React (TypeScript) monorepo, following the same architecture as the underlying Plane platform:

- **`apps/api`** — Django REST API, including the translation pipeline (Celery background tasks calling the Claude API) and the manager dashboard endpoints
- **`apps/web`** — the main React application (React Router, MobX), including the translation UI and manager dashboard page
- **`apps/admin`** — first-run instance setup and admin console
- **`packages/*`** — shared UI components, i18n, and type definitions used across the apps

Background translation jobs run through Celery, backed by Redis. Files and static assets are served from S3-compatible object storage. The whole stack is deployable as a set of containers (see the `Dockerfile.*` files in each app).

## Getting started

The fastest way to run MSWS locally is with Docker Compose:

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
docker compose up
```

Once the containers are healthy, the web app is available at `http://localhost:3000`.

To enable automatic translation, set `ANTHROPIC_API_KEY` in `apps/api/.env` (get one at [console.anthropic.com](https://console.anthropic.com)) — without it, translations fail gracefully and can be retried once a key is configured.

## License

MSWS inherits Plane's license: [GNU AGPL v3.0](./LICENSE.txt).
