# Sectrex — Technical Documentation

Technical reference for engineers extending, operating, or auditing the Sectrex corporate website.

The top-level [`README.md`](../README.md) is the install/quickstart guide. The documents in this directory go deeper: why the system is shaped the way it is, where to make changes, and what guarantees the runtime gives you.

## Reading order

| When you need to… | Read |
|---|---|
| Understand how the system is wired end-to-end | [`architecture.md`](architecture.md) |
| Add a new model, field, or change an existing one | [`data-model.md`](data-model.md) |
| Add a page, change styling, or work with templates | [`frontend.md`](frontend.md) |
| Configure, deploy, or troubleshoot a running instance | [`operations.md`](operations.md) |
| Understand what the runtime defends against (and what it doesn't) | [`security.md`](security.md) |

## What's where (top-level)

| Path | Purpose |
|---|---|
| `sectrix/` | Django project package — settings, root URLs, WSGI/ASGI entrypoints |
| `apps/core/` | Home, About, shared marketing copy (`content.py`), sitemap, context processor |
| `apps/services/` | `Service` model + admin (page renders statically from `core.content`) |
| `apps/case_studies/` | `CaseStudy` model + admin + paginated list view |
| `apps/careers/` | `JobOpening` model + admin + culture content |
| `apps/contact/` | `ContactInquiry` model + form (honeypot, free-email block) + admin |
| `templates/` | All HTML — `base.html`, `partials/`, per-app folders, `404`, `500`, `robots.txt` |
| `static/` | Brand SVGs, favicon, OG image, web manifest |
| `docker/` | `entrypoint.sh` — migrate / seed / collectstatic / exec gunicorn |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Containerization |
| `requirements.txt`, `.env.example`, `.gitignore` | Project config |

## Conventions used in these docs

- **`apps/core/content.py:NAME`** — refers to a name in that file. Open and grep.
- **Code blocks** are the canonical commands. If a doc and the code disagree, the code wins; please open a PR fixing the doc.
- Decisions explained with **"why"** are load-bearing — changing the underlying behavior usually means revising the rationale.

## Updating these docs

Update the doc in the **same change** that alters the behavior it describes. The doc lives in-repo on purpose: stale docs cost more than missing docs.
