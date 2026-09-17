# Frontend

The frontend is server-rendered HTML with a thin layer of Alpine.js for stateful UI. There is **no bundler, no transpiler, no node_modules**. CSS comes from the Tailwind Play CDN with brand tokens configured inline.

## Template inheritance

```
templates/base.html
├── {% include "partials/head_meta.html" %}      ← title, OG, Twitter, favicon, JSON-LD
├── {% include "partials/navbar.html" %}         ← sticky, scroll-aware, mobile menu
├── {% block content %}                          ← page body
├── {% include "partials/footer.html" %}         ← 4-col + social + SOC status indicator
└── {% block extra_scripts %}

Per-page templates extend base:
templates/core/home.html
templates/core/about.html
templates/services/list.html
templates/case_studies/list.html
templates/careers/list.html
templates/contact/contact.html
templates/contact/thanks.html
templates/404.html
templates/500.html
```

Three partials are includable from any page:

- `partials/cta.html` — the "Request a Briefing" call-to-action block. Every page ends with this.
- `partials/logo.html` — inline SVG. Inherits `currentColor` so the navbar (white), footer (white), and OG image (also white) all reuse the same code.
- `partials/head_meta.html` — wraps `<head>` SEO/social/structured-data fragments. Block tags inside (`title`, `description`, `og_title`, `og_description`, `twitter_*`) can be overridden per page; defaults come from `meta_title` and `meta_description` in the view context.

## Tailwind configuration

The Play CDN script in `base.html` is followed by an inline `tailwind.config` that defines all brand tokens. **This is the canonical brand palette** — any other place is downstream.

### Color tokens

| Token | Hex | Where it's used |
|---|---|---|
| `navy-950` | `#060F22` | Page background |
| `navy-900` | `#0A1830` | Card surfaces (slightly lifted) |
| `navy-800` | `#0E1F3A` | Brand navy — logo fill on light, dark-mode background |
| `navy-700` | `#142243` | Borders, leadership card backgrounds |
| `graphite-100…400` | `#E2E5EB → #6C7589` | Body text on dark (200 = primary, 300/400 = secondary) |
| `accent` (`DEFAULT`) | `#00B4F0` | Electric blue brand accent |
| `accent.soft` | `#34C7F4` | Hover state |
| `accent.deep` | `#0096C7` | Pressed / deep state (unused currently) |

### Fonts

- `font-sans` / `font-display` — Inter (loaded from Google Fonts in `base.html`)
- `font-mono` — JetBrains Mono (loaded same)

Inter handles both body and display. Use `font-display` semantically; if a separate display face is added later, only that token needs to change.

### Custom utilities

| Utility | What it does |
|---|---|
| `tracking-tightest` (`-0.04em`) | Display headings |
| `tracking-wider-2` (`0.16em`) | Wordmark and section labels |
| `tracking-wider-3` (`0.24em`) | Tiny uppercase labels ("CYBERSECURITY", "01") |
| `shadow-glow-accent` | Glow under primary CTAs |
| `bg-grid-faint` + `bg-grid-32` | Background grid pattern (with `mask-image` for fadeout) |
| `bg-radial-fade` | Subtle accent radial gradient |
| `animate-fade-up`, `animate-fade-in`, `animate-pulse-slow` | Defined via `keyframes` in config; used sparingly |

### Switching to a real Tailwind build

When traffic justifies removing the CDN dependency:

1. `pip install django-tailwind` and run `python manage.py tailwind init`.
2. Copy the entire `theme.extend` block from `base.html` into the generated `tailwind.config.js`.
3. Replace the two `<script>` tags in `base.html` (`cdn.tailwindcss.com` + the inline config) with `{% load tailwind_tags %}` and `{% tailwind_css %}` in `<head>`.
4. Add the `tailwind` app to `INSTALLED_APPS`.
5. Run `python manage.py tailwind start` in dev, `python manage.py tailwind build` in CI.

The rest of the templates — including all `class=""` attributes — work unchanged.

## Alpine.js usage map

Alpine is used in exactly three places. Search for `x-data` to find all of them.

| Location | State | Behavior |
|---|---|---|
| `partials/navbar.html` | `{ open, scrolled }` | Mobile menu toggle; navbar gains a backdrop + border when scrolled past 8px |
| `templates/case_studies/list.html` | `{ active }` | Sector filter pill active state (decorative; full filtering is via querystring once URL params are wired) |
| `templates/contact/contact.html` | (none — form state is server-side) | — |

Alpine's only requirement is `defer`-loading the CDN script in `base.html`, which is already done.

## Reveal-on-scroll

A small IntersectionObserver at the bottom of `base.html` watches every element with `data-reveal` and applies `.in-view` when it enters the viewport. The CSS transition lives in the inline `<style>` block in `base.html`:

```css
[data-reveal] { opacity: 0; transform: translateY(18px); transition: opacity .7s ..., transform .7s ...; }
[data-reveal].in-view { opacity: 1; transform: none; }
```

To opt in: add `data-reveal` to any element. To opt out of a child element: just don't add the attribute.

**Why not Alpine for this?** A single IntersectionObserver is more efficient than one per element and avoids touching Alpine's reactivity for what is fundamentally a one-shot animation.

## Icon system

All icons are **inline SVG** — there is no icon font, no sprite sheet, no separate icon component. The reasons:

1. Inline SVG inherits `currentColor`, so the same icon paints differently in different contexts without duplication.
2. Inline icons cost zero HTTP requests and are critical-path renderable.
3. Most icons are used once or twice; an icon library would be 50× the size needed.

Reusable icons (used in `home.html`, `about.html`, `services/list.html`) are defined as string constants in `apps/core/content.py`:

```python
ICON_SHIELD   = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6">…</svg>'
ICON_CLOUD    = '…'
ICON_RADAR    = '…'
…
```

They are then rendered with `{{ s.icon|safe }}` (the `|safe` is required because Django escapes by default). The `safe` filter is acceptable here because the strings are **never derived from user input** — they live in a Python module under source control.

If you need a one-off icon in a single template, just inline it directly in HTML; don't bother adding it to `content.py`.

## Logo

`partials/logo.html` renders the four-blade X icon (200×200 viewBox) at a parameter-controlled size:

```django
{% include "partials/logo.html" with size=32 %}
```

The four blade polygons paint via `fill="currentColor"`, so the surrounding element's text color drives the logo color. The center accent diamond is hard-coded to `#00B4F0` so the brand accent persists across both light and dark contexts.

The full lockup logos (with the SECTREX wordmark) live under `static/img/`:

- `logo.svg` — primary on light background
- `logo-dark.svg` — primary on dark background
- `logo-mono.svg` — single-ink print variant
- `logo-icon.svg` — square icon, no wordmark
- `favicon.svg` — same icon with a navy rounded-square plate behind it

These are referenced from OG metadata and JSON-LD; the navbar and footer use the inline partial.

## Adding a new page

1. Add a view in the relevant app's `views.py` (`TemplateView` is enough for static pages).
2. Add the URL in `<app>/urls.py`.
3. Create `templates/<app>/<page>.html` that extends `base.html`.
4. If it should appear in nav, add a `nav_items` entry in `apps.core.context_processors.site_meta`.
5. If it should appear in `sitemap.xml`, add the URL name to `apps/core/sitemaps.py:StaticViewSitemap.items()`.
6. Set `meta_title` and `meta_description` in `get_context_data` so the partial picks them up.

## Accessibility checklist (current state)

- Skip-to-content link present in `base.html`.
- All interactive elements are real `<button>` or `<a>` (no clickable divs).
- Focus styles preserved via Tailwind's default ring on form inputs.
- `aria-label` on icon-only buttons (menu toggle, social links).
- `data-reveal` animations respect that an element starts hidden — if JS is disabled, all `[data-reveal]` elements remain at opacity 0. **TODO**: add a `<noscript>` rule to force `.in-view` in that case.

## Tailwind build

Tailwind is **compiled at build time**. It used to load from the Play CDN
(`cdn.tailwindcss.com`), which is a development tool: it ships a compiler to
every visitor, re-generates the CSS on each page load, and leaves the site
completely unstyled whenever the CDN is blocked or unreachable.

```bash
npm install          # once
npm run build:css    # static/src/input.css -> static/css/tailwind.css (minified)
npm run watch:css    # rebuild on change while developing
```

| File | Purpose |
|---|---|
| `tailwind.config.js` | Brand palette, fonts, shadows, keyframes — ported verbatim from the old inline config |
| `static/src/input.css` | Tailwind directives plus the base/utility rules that were inline in `base.html` |
| `static/css/tailwind.css` | Build output, linked by `base.html` |

`content` globs cover `templates/**/*.html` **and `apps/**/*.py`** — the contact
form declares its widget classes in Python (`apps/contact/forms.py`), so
excluding it would purge the form styling.

### Rebuilding after template edits

Tailwind only emits classes it finds in the `content` globs, so a class used for
the first time needs a rebuild. Production does this automatically: the
`css` stage in the `Dockerfile` runs the build with Node and copies the result
into the Python image, so `docker compose up --build` is always current.

`static/css/tailwind.css` is committed so a fresh clone renders correctly with
`runserver` and no Node installed. It is regenerated during the image build, so
a stale committed copy never reaches production.

### Still on a CDN

Alpine.js and the Inter/JetBrains Mono webfonts still load from jsdelivr and
Google Fonts. They are versioned, cacheable files rather than a compiler, so the
cost is lower — but vendoring them would remove the last third-party runtime
dependencies.
