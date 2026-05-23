# MVP Design — InsideNaija + ShopEasy
**Date:** 2026-05-22  
**Status:** Approved for implementation

---

## Overview

Two products, one codebase (`frontend_v2`), one Supabase backend, one FastAPI layer.

- **InsideNaija** — B2B synthetic Nigerian consumer research panel
- **ShopEasy** — B2C Nigerian e-commerce storefront with persona-aware recommendations

---

## Shared Architecture

### Frontend (`frontend_v2`)
- React + Vite + TypeScript
- Tailwind CSS + shadcn/ui
- React Router v6
- TanStack Query
- Zustand (auth session + global state)

### Backend
- Existing FastAPI — extend with new routers, do not rewrite
- OOP pattern: thin routers → Service classes → Repository classes → Supabase

### Database
- Supabase (PostgreSQL + Auth + Storage + Realtime)
- All DB access through `BaseRepository` — connection instantiated once, inherited by all repositories

---

## OOP Structure

### Base Repository (Python)
```
BaseRepository
  ├── find(id)
  ├── find_all(filters)
  ├── save(data)
  ├── update(id, data)
  └── delete(id)
```

All repositories inherit from `BaseRepository`. Supabase client lives in the base only.

### Backend Layer Pattern
```
Router (thin) → Service (business logic) → Repository (DB access)
```

---

## Database Schema

### Shared Tables
| Table | Key Fields |
|-------|-----------|
| `organizations` | id, name, plan, created_at |
| `users` | id, org_id, email, role, created_at |

### InsideNaija Tables
| Table | Key Fields |
|-------|-----------|
| `projects` | id, org_id, user_id, name, description, category, image_url, created_at |
| `panel_runs` | id, project_id, status, model_used, personas_used, created_at |
| `results` | id, panel_run_id, persona_id, review_text, rating, register_tier, sentiment |

### ShopEasy Tables
| Table | Key Fields |
|-------|-----------|
| `products` | id, name, description, category, price_naira, image_url, seller |
| `personas` | id, user_id, hedonic_utilitarian, register_tier, aspect_priority, ... |
| `cart_items` | id, user_id, product_id, quantity |
| `orders` | id, user_id, status, total_naira, created_at |
| `order_items` | id, order_id, product_id, quantity, price_naira |

---

## InsideNaija — MVP Screens

1. **Login / Signup** — Supabase auth
2. **Dashboard** — list of projects, last run date, status; "New Project" CTA
3. **New Project** — name, description, category, image upload → triggers panel run
4. **Results View** — live run progress (Supabase realtime) → per-persona reviews, sentiment chart, theme breakdown, register distribution
5. **History** — per-project list of all past runs, click to view any result
6. **Export** — PDF report + CSV download from any result

---

## ShopEasy — MVP Screens

1. **Login / Signup** — same Supabase auth
2. **Onboarding** — quick persona setup (language preference, shopping style)
3. **Home / Catalog** — product grid with search + category filter
4. **Product Detail** — product info + AI-powered persona recommendations
5. **Cart** — add/remove items, quantity
6. **Order History** — past orders with status

---

## Row Level Security
- Users only see their own org's projects and results (InsideNaija)
- Users only see their own cart, orders, persona (ShopEasy)
- Enforced at Supabase RLS level, not app level

---

## FastAPI New Endpoints

### InsideNaija
- `POST /projects` — create project
- `GET /projects` — list user's projects
- `GET /projects/{id}` — get project + runs
- `POST /projects/{id}/runs` — trigger panel run
- `GET /runs/{id}/status` — run status
- `GET /runs/{id}/results` — get results
- `GET /runs/{id}/export` — generate PDF/CSV

### ShopEasy
- `GET /shop/products` — catalog with filters
- `GET /shop/products/{id}` — product detail
- `POST /shop/persona` — save/update persona
- `GET /shop/recommendations` — persona-aware recommendations
- `POST /shop/cart` — add to cart
- `GET /shop/cart` — get cart
- `POST /shop/orders` — place order
- `GET /shop/orders` — order history
