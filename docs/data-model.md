# Data Model

Four DB-backed models live across four apps. There are **no foreign keys** between them — each model represents an independent editorial surface in the admin.

## Overview

| Model | App | Admin-managed | Public surface |
|---|---|---|---|
| `Service` | `apps.services` | Yes | (Page actually renders from `core.content.SERVICE_DETAIL` — see note below) |
| `CaseStudy` | `apps.case_studies` | Yes | `/case-studies/` (paginated list) |
| `JobOpening` | `apps.careers` | Yes | `/careers/` (list) |
| `ContactInquiry` | `apps.contact` | Read in admin; written by public form | None (admin-only) |

All models use Django's default `BigAutoField` PK and inherit no abstract base.

---

## `Service` — `apps/services/models.py`

```
title              CharField(120)
slug               SlugField(140, unique=True)         ← auto-derived from title on save()
short_description  CharField(240)
description        TextField
icon_key           CharField(40)                       ← matched to inline SVG in templates
capabilities       JSONField (list of strings)
display_order      PositiveIntegerField (default 0)
is_published       BooleanField (default True)
created_at, updated_at
```

**`Meta.ordering = ["display_order", "title"]`** — admin can reorder by editing `display_order` inline.

**Note on rendering**: the services *page* (`/services/`) currently renders the canonical six offerings statically from `apps.core.content.SERVICE_DETAIL`. The `Service` model exists for two reasons:

1. The home page pulls a count via `Service.objects.filter(is_published=True)[:6]` (visible in `HomeView.get_context_data`).
2. Future feature work — per-service detail pages — will read from this model.

If you want admin-managed services *to show on the services page*, swap the view to use the queryset and remove the static path. See `apps/services/views.py` for the comment marker.

---

## `CaseStudy` — `apps/case_studies/models.py`

```
title                    CharField(160)
slug                     SlugField(180, unique=True)      ← auto from client + title
client_name              CharField(120)                   ← "Confidential — Tier-1 Bank" when under NDA
sector                   CharField(40, choices=SECTOR_CHOICES)
region                   CharField(80, default="GCC")
summary                  CharField(280)                   ← card body
challenge / approach / outcome   TextField                ← narrative; not yet surfaced on list page
headline_metric          CharField(40)                    ← e.g. "−72%", "99.97%"
headline_metric_label    CharField(80)                    ← e.g. "Mean time to detect"
cover_image              ImageField (optional)
tags                     JSONField (list of strings)
is_published, published_at, display_order
```

**`SECTOR_CHOICES`** — banking · government · energy · healthcare · telecom · retail · logistics.

**`Meta.ordering = ["display_order", "-published_at"]`** — display order wins; ties break on most-recent.

**Lifecycle**:
1. Editor creates row in admin, leaves `is_published=False` while drafting.
2. Editor adds `display_order` (10, 20, 30… leaves gaps for future inserts).
3. Editor sets `published_at` and flips `is_published=True`.
4. List view picks it up automatically (no cache to invalidate).

`challenge`, `approach`, and `outcome` are currently captured but only rendered when a detail page is added.

---

## `JobOpening` — `apps/careers/models.py`

```
title              CharField(140)
slug               SlugField(160, unique=True)
department         CharField(40, choices=DEPARTMENT_CHOICES)   ← soc, threat_intel, cloud, offensive, engineering, grc, sales, operations
employment_type    CharField(20, choices=EMPLOYMENT_TYPES)
level              CharField(20, choices=LEVEL_CHOICES)
location           CharField(120, default="Dubai, UAE")
is_remote_friendly BooleanField
summary            CharField(240)
description        TextField
requirements       JSONField (list of strings)
nice_to_have       JSONField (list of strings)
is_published, posted_at (auto), closes_at, apply_email
```

`posted_at` is `auto_now_add=True` — set once on creation. `closes_at` is optional and currently unused by the list view (add a filter when needed).

Applications today go through `mailto:` directly to `apply_email` (default `careers@sectrix.com`). If you need a proper applications model, add `JobApplication` here with an FK to `JobOpening`.

---

## `ContactInquiry` — `apps/contact/models.py`

This is the only model written by anonymous public traffic. Treat it as an attack surface.

```
full_name          CharField(120)
work_email         EmailField                    ← free providers rejected at form level
phone              CharField(40, blank)
company            CharField(160)
job_title          CharField(120, blank)
country            CharField(80, blank)
organization_size  CharField(20, choices, blank)
interest           CharField(40, choices)        ← which service track they care about
message            TextField

# Lifecycle
created_at         DateTimeField (auto)
is_handled         BooleanField
handled_by         CharField(120, blank)
internal_notes     TextField (blank)

# Diagnostics
user_agent         CharField(400, blank)         ← truncated on save
ip_hash            CharField(64, blank)          ← SHA-256 of REMOTE_ADDR; not the IP itself
```

**Why hash the IP?** Three reasons:

1. We don't want raw PII in the DB if the box is ever exfiltrated.
2. Storing a hash still lets us correlate repeat submissions from the same source.
3. GDPR-ish defensibility — there is no realistic way to recover the IP from the hash without a known candidate set.

**Lifecycle on submit** (`apps/contact/views.py:ContactView.form_valid`):

1. Form validates: required fields, valid email, **non-free-email domain**, **honeypot empty**.
2. `ContactInquiry.save()` with `user_agent` (truncated) and `ip_hash` populated.
3. `send_mail()` to `settings.CONTACT_INBOX` (best-effort, `fail_silently=True`).
4. Success flash message → redirect to `/contact/thanks/` (PRG pattern).

---

## Adding a new model

1. Create the model in the relevant app's `models.py`. Inherit nothing; default PK is fine.
2. `python manage.py makemigrations <app>` — review the generated SQL with `manage.py sqlmigrate`.
3. Register in the app's `admin.py` — copy an existing `ModelAdmin` as a starting point (they all set `list_display`, `list_filter`, `search_fields`, `list_editable`).
4. If the model has user-facing content, add a row in `apps.core.management.commands.seed_demo` so the container's first boot has data to render.
5. If it surfaces on a new page, add a URL pattern, view, and template; if it changes nav, edit `apps.core.context_processors.site_meta.nav_items`.
6. Update [`data-model.md`](data-model.md) (this file) in the same commit.

## JSONField — when to use vs. a related table

The models above use `JSONField` for `capabilities`, `tags`, `requirements`, `nice_to_have`. The rule:

- **List of strings, write-once-by-editor, read-only by visitors** → `JSONField`. Fewer joins, simpler admin, fewer migrations as schema evolves.
- **You need to filter, count, or relate to other rows** → real foreign-key table.

If `tags` ever needs to become a filterable taxonomy with its own admin (color, description, slug), promote to a `Tag` model with a `ManyToManyField`. The current shape is the right call for the current scale.
