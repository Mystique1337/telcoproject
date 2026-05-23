# InsideNaija MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the InsideNaija product — a dashboard where users create research projects, run a synthetic Nigerian panel, view results, browse history, and export reports.

**Architecture:** Thin FastAPI routers call Service classes which call Repository classes (all extending BaseRepository from the Foundation plan). Frontend features live in `frontend_v2/src/features/insidenaija/`. Supabase Realtime powers live panel run progress.

**Tech Stack:** FastAPI, supabase-py, BaseRepository, React, TanStack Query, Zustand, shadcn/ui, Supabase Realtime

**Prerequisite:** Foundation plan must be complete.

---

## File Map

**Backend:**
- Create: `app/db/repositories/project_repository.py`
- Create: `app/db/repositories/panel_run_repository.py`
- Create: `app/db/repositories/results_repository.py`
- Create: `app/services/project_service.py`
- Create: `app/services/panel_run_service.py`
- Create: `app/api/routers/projects.py`
- Create: `app/api/routers/runs.py`
- Modify: `app/api/main.py` — register new routers

**Frontend:**
- Create: `frontend_v2/src/features/insidenaija/api.ts`
- Create: `frontend_v2/src/features/insidenaija/types.ts`
- Create: `frontend_v2/src/pages/insidenaija/Dashboard.tsx`
- Create: `frontend_v2/src/pages/insidenaija/NewProject.tsx`
- Create: `frontend_v2/src/pages/insidenaija/Results.tsx`
- Create: `frontend_v2/src/pages/insidenaija/History.tsx`
- Modify: `frontend_v2/src/App.tsx` — add InsideNaija routes

**Database:**
- Create: `supabase/migrations/002_insidenaija.sql`

---

### Task 1: InsideNaija DB schema

**Files:**
- Create: `supabase/migrations/002_insidenaija.sql`

- [ ] **Step 1: Run schema SQL in Supabase**

In the Supabase SQL editor, run:
```sql
-- Projects
create table projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  org_id uuid references organizations(id),
  name text not null,
  description text not null,
  category text not null default 'general',
  image_url text,
  created_at timestamptz not null default now()
);

-- Panel runs
create table panel_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  status text not null default 'pending',  -- pending | running | complete | failed
  model_used text,
  personas_used jsonb default '[]',
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

-- Results (one row per persona per run)
create table results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references panel_runs(id) on delete cascade,
  persona_id text not null,
  persona_name text not null,
  review_text text not null,
  rating integer check (rating between 1 and 5),
  register_tier text,
  sentiment text,  -- positive | neutral | negative
  created_at timestamptz not null default now()
);

-- RLS
alter table projects enable row level security;
alter table panel_runs enable row level security;
alter table results enable row level security;

create policy "projects: own only" on projects
  for all using (auth.uid() = user_id);

create policy "panel_runs: own project only" on panel_runs
  for all using (
    project_id in (select id from projects where user_id = auth.uid())
  );

create policy "results: own run only" on results
  for all using (
    run_id in (
      select pr.id from panel_runs pr
      join projects p on p.id = pr.project_id
      where p.user_id = auth.uid()
    )
  );

-- Enable Realtime for live run status
alter publication supabase_realtime add table panel_runs;
```

Save copy to `supabase/migrations/002_insidenaija.sql`.

- [ ] **Step 2: Commit**

```bash
git add supabase/migrations/002_insidenaija.sql
git commit -m "feat(insidenaija): add DB schema with RLS + realtime"
```

---

### Task 2: Repositories

**Files:**
- Create: `app/db/repositories/__init__.py`
- Create: `app/db/repositories/project_repository.py`
- Create: `app/db/repositories/panel_run_repository.py`
- Create: `app/db/repositories/results_repository.py`

- [ ] **Step 1: Create ProjectRepository**

Create `app/db/repositories/__init__.py` (empty).

Create `app/db/repositories/project_repository.py`:
```python
from __future__ import annotations
from typing import Any
from app.db.base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    table_name = "projects"

    def find_by_user(self, user_id: str) -> list[dict[str, Any]]:
        res = (
            self.client.table(self.table_name)
            .select("*, panel_runs(id, status, created_at)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
```

- [ ] **Step 2: Create PanelRunRepository**

Create `app/db/repositories/panel_run_repository.py`:
```python
from __future__ import annotations
from typing import Any
from app.db.base_repository import BaseRepository


class PanelRunRepository(BaseRepository):
    table_name = "panel_runs"

    def find_by_project(self, project_id: str) -> list[dict[str, Any]]:
        res = (
            self.client.table(self.table_name)
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []

    def set_status(self, run_id: str, status: str) -> dict[str, Any]:
        return self.update(run_id, {"status": status})

    def mark_complete(self, run_id: str, model_used: str, personas_used: list) -> dict[str, Any]:
        import datetime
        return self.update(run_id, {
            "status": "complete",
            "model_used": model_used,
            "personas_used": personas_used,
            "completed_at": datetime.datetime.utcnow().isoformat(),
        })
```

- [ ] **Step 3: Create ResultsRepository**

Create `app/db/repositories/results_repository.py`:
```python
from __future__ import annotations
from typing import Any
from app.db.base_repository import BaseRepository


class ResultsRepository(BaseRepository):
    table_name = "results"

    def find_by_run(self, run_id: str) -> list[dict[str, Any]]:
        res = (
            self.client.table(self.table_name)
            .select("*")
            .eq("run_id", run_id)
            .order("created_at")
            .execute()
        )
        return res.data or []

    def save_many(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        res = self.client.table(self.table_name).insert(rows).execute()
        return res.data or []
```

- [ ] **Step 4: Write tests**

Create `tests/db/repositories/test_project_repository.py`:
```python
from unittest.mock import MagicMock, patch
from app.db.repositories.project_repository import ProjectRepository


@patch("app.db.base_repository.get_supabase_client")
def test_find_by_user_queries_correct_user(mock_client):
    mock_table = MagicMock()
    mock_client.return_value.table.return_value = mock_table
    mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"id": "proj-1", "user_id": "user-123", "name": "Test"}
    ]

    repo = ProjectRepository()
    result = repo.find_by_user("user-123")

    mock_table.select.assert_called_once()
    assert len(result) == 1
    assert result[0]["user_id"] == "user-123"
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/db/repositories/ -v
```
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add app/db/repositories/ tests/db/repositories/
git commit -m "feat(insidenaija): add Project, PanelRun, Results repositories"
```

---

### Task 3: Services

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/project_service.py`
- Create: `app/services/panel_run_service.py`

- [ ] **Step 1: Create ProjectService**

Create `app/services/__init__.py` (empty).

Create `app/services/project_service.py`:
```python
from __future__ import annotations
from typing import Any
from app.db.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self) -> None:
        self.repo = ProjectRepository()

    def create(self, user_id: str, name: str, description: str,
               category: str, image_url: str | None = None) -> dict[str, Any]:
        return self.repo.save({
            "user_id": user_id,
            "name": name,
            "description": description,
            "category": category,
            "image_url": image_url,
        })

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.repo.find_by_user(user_id)

    def get(self, project_id: str) -> dict[str, Any] | None:
        return self.repo.find(project_id)
```

- [ ] **Step 2: Create PanelRunService**

Create `app/services/panel_run_service.py`:
```python
from __future__ import annotations
from typing import Any
from app.db.repositories.panel_run_repository import PanelRunRepository
from app.db.repositories.results_repository import ResultsRepository
from app.db.repositories.project_repository import ProjectRepository


class PanelRunService:
    def __init__(self) -> None:
        self.run_repo = PanelRunRepository()
        self.results_repo = ResultsRepository()
        self.project_repo = ProjectRepository()

    def create_run(self, project_id: str) -> dict[str, Any]:
        return self.run_repo.save({"project_id": project_id, "status": "pending"})

    def get_status(self, run_id: str) -> dict[str, Any] | None:
        return self.run_repo.find(run_id)

    def get_results(self, run_id: str) -> list[dict[str, Any]]:
        return self.results_repo.find_by_run(run_id)

    def list_for_project(self, project_id: str) -> list[dict[str, Any]]:
        return self.run_repo.find_by_project(project_id)

    async def execute_run(self, run_id: str, project_id: str) -> None:
        """Trigger the panel agent and persist results. Called as background task."""
        from app.agents.panel_agent import run_panel
        from app.data.personas import PANEL_PERSONAS

        self.run_repo.set_status(run_id, "running")

        project = self.project_repo.find(project_id)
        if not project:
            self.run_repo.set_status(run_id, "failed")
            return

        try:
            panel_results = await run_panel(
                product_name=project["name"],
                product_description=project["description"],
                category=project["category"],
            )

            rows = [
                {
                    "run_id": run_id,
                    "persona_id": r["persona_id"],
                    "persona_name": r["persona_name"],
                    "review_text": r["review"],
                    "rating": r.get("rating"),
                    "register_tier": r.get("register_tier"),
                    "sentiment": r.get("sentiment"),
                }
                for r in panel_results
            ]
            self.results_repo.save_many(rows)
            self.run_repo.mark_complete(
                run_id,
                model_used=panel_results[0].get("model_used", "unknown") if panel_results else "unknown",
                personas_used=[r["persona_id"] for r in panel_results],
            )
        except Exception:
            self.run_repo.set_status(run_id, "failed")
            raise
```

- [ ] **Step 3: Write service tests**

Create `tests/services/test_project_service.py`:
```python
from unittest.mock import MagicMock, patch
from app.services.project_service import ProjectService


@patch("app.services.project_service.ProjectRepository")
def test_create_project_calls_repo_save(MockRepo):
    mock_repo = MagicMock()
    MockRepo.return_value = mock_repo
    mock_repo.save.return_value = {"id": "proj-1", "name": "Test Product"}

    service = ProjectService()
    result = service.create("user-1", "Test Product", "A test", "electronics")

    mock_repo.save.assert_called_once_with({
        "user_id": "user-1",
        "name": "Test Product",
        "description": "A test",
        "category": "electronics",
        "image_url": None,
    })
    assert result["id"] == "proj-1"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/services/ -v
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add app/services/ tests/services/
git commit -m "feat(insidenaija): add ProjectService + PanelRunService"
```

---

### Task 4: FastAPI routers

**Files:**
- Create: `app/api/routers/projects.py`
- Create: `app/api/routers/runs.py`
- Modify: `app/api/main.py`

- [ ] **Step 1: Create projects router**

Create `app/api/routers/projects.py`:
```python
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from app.middleware.auth import get_current_user
from app.services.project_service import ProjectService
from app.services.panel_run_service import PanelRunService

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectBody(BaseModel):
    name: str
    description: str
    category: str = "general"
    image_url: str | None = None


@router.get("")
async def list_projects(user=Depends(get_current_user)) -> list[dict[str, Any]]:
    return ProjectService().list_for_user(user["user_id"])


@router.post("")
async def create_project(
    body: CreateProjectBody,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
) -> dict[str, Any]:
    svc = ProjectService()
    run_svc = PanelRunService()

    project = svc.create(
        user_id=user["user_id"],
        name=body.name,
        description=body.description,
        category=body.category,
        image_url=body.image_url,
    )

    run = run_svc.create_run(project["id"])
    background_tasks.add_task(run_svc.execute_run, run["id"], project["id"])

    return {"project": project, "run_id": run["id"]}


@router.get("/{project_id}")
async def get_project(project_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    project = ProjectService().get(project_id)
    if not project or project["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Project not found")
    runs = PanelRunService().list_for_project(project_id)
    return {"project": project, "runs": runs}
```

- [ ] **Step 2: Create runs router**

Create `app/api/routers/runs.py`:
```python
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.middleware.auth import get_current_user
from app.services.panel_run_service import PanelRunService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}/status")
async def get_run_status(run_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    run = PanelRunService().get_status(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/results")
async def get_run_results(run_id: str, user=Depends(get_current_user)) -> list[dict[str, Any]]:
    return PanelRunService().get_results(run_id)


@router.get("/{run_id}/export/csv")
async def export_csv(run_id: str, user=Depends(get_current_user)):
    import csv
    import io
    results = PanelRunService().get_results(run_id)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["persona_name", "rating", "register_tier", "sentiment", "review_text"])
    writer.writeheader()
    writer.writerows(results)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=run_{run_id}.csv"},
    )
```

- [ ] **Step 3: Register routers in main.py**

Open `app/api/main.py` and add:
```python
from app.api.routers import projects as projects_router
from app.api.routers import runs as runs_router

# inside the app setup, after existing routers:
app.include_router(projects_router.router)
app.include_router(runs_router.router)
```

- [ ] **Step 4: Test endpoints with curl**

Start the backend:
```bash
uvicorn app.api.main:app --reload
```

Check routes exist:
```bash
curl http://localhost:8000/docs
```
Expected: `/projects` and `/runs/{run_id}/status` visible in Swagger UI.

- [ ] **Step 5: Commit**

```bash
git add app/api/routers/projects.py app/api/routers/runs.py app/api/main.py
git commit -m "feat(insidenaija): add projects + runs FastAPI routers"
```

---

### Task 5: Frontend types + API client

**Files:**
- Create: `frontend_v2/src/features/insidenaija/types.ts`
- Create: `frontend_v2/src/features/insidenaija/api.ts`

- [ ] **Step 1: Define TypeScript types**

Create `frontend_v2/src/features/insidenaija/types.ts`:
```typescript
export interface Project {
  id: string
  user_id: string
  name: string
  description: string
  category: string
  image_url: string | null
  created_at: string
  panel_runs?: PanelRun[]
}

export interface PanelRun {
  id: string
  project_id: string
  status: 'pending' | 'running' | 'complete' | 'failed'
  model_used: string | null
  personas_used: string[]
  created_at: string
  completed_at: string | null
}

export interface Result {
  id: string
  run_id: string
  persona_id: string
  persona_name: string
  review_text: string
  rating: number | null
  register_tier: string | null
  sentiment: 'positive' | 'neutral' | 'negative' | null
  created_at: string
}

export interface CreateProjectPayload {
  name: string
  description: string
  category: string
  image_url?: string
}
```

- [ ] **Step 2: Create API client**

Create `frontend_v2/src/features/insidenaija/api.ts`:
```typescript
import { supabase } from '@/lib/supabase'
import type { Project, PanelRun, Result, CreateProjectPayload } from './types'

const BASE = import.meta.env.VITE_API_BASE_URL

async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession()
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.session?.access_token ?? ''}`,
  }
}

export async function listProjects(): Promise<Project[]> {
  const res = await fetch(`${BASE}/projects`, { headers: await authHeaders() })
  if (!res.ok) throw new Error('Failed to fetch projects')
  return res.json()
}

export async function createProject(payload: CreateProjectPayload): Promise<{ project: Project; run_id: string }> {
  const res = await fetch(`${BASE}/projects`, {
    method: 'POST',
    headers: await authHeaders(),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to create project')
  return res.json()
}

export async function getProject(projectId: string): Promise<{ project: Project; runs: PanelRun[] }> {
  const res = await fetch(`${BASE}/projects/${projectId}`, { headers: await authHeaders() })
  if (!res.ok) throw new Error('Failed to fetch project')
  return res.json()
}

export async function getRunStatus(runId: string): Promise<PanelRun> {
  const res = await fetch(`${BASE}/runs/${runId}/status`, { headers: await authHeaders() })
  if (!res.ok) throw new Error('Failed to fetch run status')
  return res.json()
}

export async function getRunResults(runId: string): Promise<Result[]> {
  const res = await fetch(`${BASE}/runs/${runId}/results`, { headers: await authHeaders() })
  if (!res.ok) throw new Error('Failed to fetch results')
  return res.json()
}

export function exportCsvUrl(runId: string): string {
  return `${BASE}/runs/${runId}/export/csv`
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend_v2/src/features/insidenaija/
git commit -m "feat(insidenaija): add frontend types + API client"
```

---

### Task 6: Dashboard page

**Files:**
- Create: `frontend_v2/src/pages/insidenaija/Dashboard.tsx`

- [ ] **Step 1: Create Dashboard**

Create `frontend_v2/src/pages/insidenaija/Dashboard.tsx`:
```typescript
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listProjects } from '@/features/insidenaija/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Project } from '@/features/insidenaija/types'

const STATUS_COLOUR: Record<string, string> = {
  complete: 'bg-green-100 text-green-800',
  running: 'bg-blue-100 text-blue-800',
  pending: 'bg-yellow-100 text-yellow-800',
  failed: 'bg-red-100 text-red-800',
}

function ProjectCard({ project }: { project: Project }) {
  const navigate = useNavigate()
  const lastRun = project.panel_runs?.[0]

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => navigate(`/projects/${project.id}`)}
    >
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <CardTitle className="text-base font-semibold">{project.name}</CardTitle>
        {lastRun && (
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOUR[lastRun.status]}`}>
            {lastRun.status}
          </span>
        )}
      </CardHeader>
      <CardContent>
        <p className="text-sm text-slate-500 line-clamp-2">{project.description}</p>
        <p className="text-xs text-slate-400 mt-2">
          {new Date(project.created_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">InsideNaija</h1>
        <Button onClick={() => navigate('/projects/new')}>New Project</Button>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {isLoading && <p className="text-slate-500">Loading…</p>}

        {!isLoading && projects.length === 0 && (
          <div className="text-center py-20 space-y-3">
            <p className="text-slate-600 font-medium">No projects yet</p>
            <p className="text-slate-400 text-sm">Create your first project to run a panel</p>
            <Button onClick={() => navigate('/projects/new')}>Create project</Button>
          </div>
        )}

        {projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => <ProjectCard key={p.id} project={p} />)}
          </div>
        )}
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Add route in App.tsx**

Open `frontend_v2/src/App.tsx` and add:
```typescript
import Dashboard from '@/pages/insidenaija/Dashboard'

// inside <Routes>:
<Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
```

- [ ] **Step 3: Start dev server and verify**

```bash
npm run dev
```
- Log in → should land on Dashboard
- Empty state shows "No projects yet"

- [ ] **Step 4: Commit**

```bash
git add frontend_v2/src/pages/insidenaija/Dashboard.tsx frontend_v2/src/App.tsx
git commit -m "feat(insidenaija): add Dashboard page"
```

---

### Task 7: New Project page

**Files:**
- Create: `frontend_v2/src/pages/insidenaija/NewProject.tsx`

- [ ] **Step 1: Create NewProject page**

Create `frontend_v2/src/pages/insidenaija/NewProject.tsx`:
```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createProject } from '@/features/insidenaija/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const CATEGORIES = ['electronics', 'fashion', 'food & beverage', 'beauty', 'home', 'health', 'general']

export default function NewProject() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('general')

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: ({ run_id }) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate(`/runs/${run_id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({ name, description, category })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/dashboard')} className="text-slate-400 hover:text-slate-700">←</button>
        <h1 className="text-xl font-bold">New Project</h1>
      </header>

      <main className="max-w-xl mx-auto px-6 py-8">
        <Card>
          <CardHeader>
            <CardTitle>Tell us about your product</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="name">Product name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required
                  placeholder="e.g. Bigi Cola 50cl" />
              </div>

              <div className="space-y-1">
                <Label htmlFor="description">Description</Label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  rows={4}
                  placeholder="Describe the product — features, price point, target market…"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="category">Category</Label>
                <select
                  id="category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              {mutation.isError && (
                <p className="text-sm text-red-600">Failed to create project. Try again.</p>
              )}

              <Button type="submit" className="w-full" disabled={mutation.isPending}>
                {mutation.isPending ? 'Starting panel run…' : 'Run panel →'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Add route**

In `frontend_v2/src/App.tsx` add:
```typescript
import NewProject from '@/pages/insidenaija/NewProject'

// inside <Routes>:
<Route path="/projects/new" element={<ProtectedRoute><NewProject /></ProtectedRoute>} />
```

- [ ] **Step 3: Verify — click "New Project" from Dashboard**

Fill in the form, submit → should navigate to `/runs/{run_id}` (placeholder for now).

- [ ] **Step 4: Commit**

```bash
git add frontend_v2/src/pages/insidenaija/NewProject.tsx frontend_v2/src/App.tsx
git commit -m "feat(insidenaija): add New Project form"
```

---

### Task 8: Results page

**Files:**
- Create: `frontend_v2/src/pages/insidenaija/Results.tsx`

- [ ] **Step 1: Create Results page**

Create `frontend_v2/src/pages/insidenaija/Results.tsx`:
```typescript
import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { getRunStatus, getRunResults, exportCsvUrl } from '@/features/insidenaija/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { Result } from '@/features/insidenaija/types'

const SENTIMENT_COLOUR = {
  positive: 'text-green-600',
  neutral: 'text-slate-500',
  negative: 'text-red-600',
}

const STARS = (n: number | null) => n ? '★'.repeat(n) + '☆'.repeat(5 - n) : '—'

function AggregateBar({ results }: { results: Result[] }) {
  const total = results.length
  if (!total) return null
  const pos = results.filter((r) => r.sentiment === 'positive').length
  const neg = results.filter((r) => r.sentiment === 'negative').length
  const neu = total - pos - neg
  const avgRating = results.reduce((s, r) => s + (r.rating ?? 0), 0) / total

  return (
    <Card className="mb-6">
      <CardContent className="pt-4 flex flex-wrap gap-6">
        <div>
          <p className="text-xs text-slate-500">Average rating</p>
          <p className="text-2xl font-bold">{avgRating.toFixed(1)} <span className="text-yellow-500">★</span></p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Sentiment</p>
          <p className="text-sm">
            <span className="text-green-600 font-medium">{pos} positive</span>
            {' · '}
            <span className="text-slate-500">{neu} neutral</span>
            {' · '}
            <span className="text-red-600 font-medium">{neg} negative</span>
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Personas</p>
          <p className="text-sm font-medium">{total}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export default function Results() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: run } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => getRunStatus(runId!),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'pending' || status === 'running' ? 2000 : false
    },
  })

  const { data: results = [] } = useQuery({
    queryKey: ['results', runId],
    queryFn: () => getRunResults(runId!),
    enabled: run?.status === 'complete',
  })

  // Supabase Realtime — invalidate query when run status changes
  useEffect(() => {
    if (!runId) return
    const channel = supabase
      .channel(`run-${runId}`)
      .on('postgres_changes', {
        event: 'UPDATE', schema: 'public', table: 'panel_runs',
        filter: `id=eq.${runId}`,
      }, () => {
        queryClient.invalidateQueries({ queryKey: ['run', runId] })
        queryClient.invalidateQueries({ queryKey: ['results', runId] })
      })
      .subscribe()
    return () => { supabase.removeChannel(channel) }
  }, [runId, queryClient])

  const isRunning = run?.status === 'pending' || run?.status === 'running'

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')} className="text-slate-400 hover:text-slate-700">←</button>
          <h1 className="text-xl font-bold">Panel Results</h1>
        </div>
        {run?.status === 'complete' && (
          <a href={exportCsvUrl(runId!)} download>
            <Button variant="outline" size="sm">Export CSV</Button>
          </a>
        )}
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        {isRunning && (
          <div className="text-center py-16 space-y-3">
            <div className="inline-block w-8 h-8 border-4 border-slate-300 border-t-slate-700 rounded-full animate-spin" />
            <p className="text-slate-600">Panel is running…</p>
            <p className="text-slate-400 text-sm">This usually takes 1–2 minutes</p>
          </div>
        )}

        {run?.status === 'failed' && (
          <p className="text-red-600 text-center py-16">Panel run failed. Please try again.</p>
        )}

        {run?.status === 'complete' && (
          <>
            <AggregateBar results={results} />
            <div className="space-y-4">
              {results.map((r) => (
                <Card key={r.id}>
                  <CardHeader className="pb-2 flex flex-row items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">{r.persona_name}</p>
                      <p className="text-xs text-slate-400">{r.register_tier?.replace('_', ' ')}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-yellow-500 text-sm">{STARS(r.rating)}</p>
                      {r.sentiment && (
                        <p className={`text-xs font-medium ${SENTIMENT_COLOUR[r.sentiment]}`}>
                          {r.sentiment}
                        </p>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-700 leading-relaxed">{r.review_text}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Add route**

In `frontend_v2/src/App.tsx`:
```typescript
import Results from '@/pages/insidenaija/Results'

<Route path="/runs/:runId" element={<ProtectedRoute><Results /></ProtectedRoute>} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend_v2/src/pages/insidenaija/Results.tsx frontend_v2/src/App.tsx
git commit -m "feat(insidenaija): add Results page with realtime run progress"
```

---

### Task 9: History page

**Files:**
- Create: `frontend_v2/src/pages/insidenaija/History.tsx`

- [ ] **Step 1: Create History page**

Create `frontend_v2/src/pages/insidenaija/History.tsx`:
```typescript
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getProject } from '@/features/insidenaija/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const STATUS_COLOUR: Record<string, string> = {
  complete: 'text-green-600',
  running: 'text-blue-600',
  pending: 'text-yellow-600',
  failed: 'text-red-600',
}

export default function History() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
  })

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/dashboard')} className="text-slate-400 hover:text-slate-700">←</button>
        <h1 className="text-xl font-bold">{data?.project.name ?? 'Project'}</h1>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        {isLoading && <p className="text-slate-500">Loading…</p>}
        {!isLoading && (!data?.runs || data.runs.length === 0) && (
          <p className="text-slate-400 text-center py-12">No runs yet.</p>
        )}
        <div className="space-y-3">
          {data?.runs.map((run) => (
            <Card
              key={run.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/runs/${run.id}`)}
            >
              <CardContent className="pt-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    Run {new Date(run.created_at).toLocaleString()}
                  </p>
                  {run.model_used && (
                    <p className="text-xs text-slate-400">{run.model_used}</p>
                  )}
                </div>
                <span className={`text-sm font-medium ${STATUS_COLOUR[run.status]}`}>
                  {run.status}
                </span>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Add route**

In `frontend_v2/src/App.tsx`:
```typescript
import History from '@/pages/insidenaija/History'

<Route path="/projects/:projectId" element={<ProtectedRoute><History /></ProtectedRoute>} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend_v2/src/pages/insidenaija/History.tsx frontend_v2/src/App.tsx
git commit -m "feat(insidenaija): add History page (per-project run list)"
```

---

**InsideNaija MVP complete.**  
User flow: Sign up → Dashboard → New Project → Live Results → Export CSV → History.
