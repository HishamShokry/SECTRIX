"""Inline SVG icon registry.

Icons are chosen in the admin by key, never pasted as markup, so an editor
cannot inject arbitrary SVG into a page. Add a new icon here and it becomes
selectable everywhere an icon_key field is used.
"""
from django.utils.safestring import mark_safe


ICONS = {
    "shield": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l8 3v6c0 4.5-3.4 8.4-8 9-4.6-.6-8-4.5-8-9V6l8-3z" stroke-linejoin="round"/></svg>'
    ),
    "cloud": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 18a4 4 0 010-8 6 6 0 0111.5 1.5A4 4 0 0118 18H7z" stroke-linejoin="round"/></svg>'
    ),
    "radar": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 010 18M3 12h18"/></svg>'
    ),
    "siren": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 18h14M7 18v-5a5 5 0 0110 0v5M9 7V4M15 7V4"/></svg>'
    ),
    "lock": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>'
    ),
    "compass": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M14.5 9.5l-1.5 4-4 1.5 1.5-4 4-1.5z" stroke-linejoin="round"/></svg>'
    ),
    "grid": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="4" width="7" height="7"/><rect x="13" y="4" width="7" height="7"/><rect x="4" y="13" width="7" height="7"/><rect x="13" y="13" width="7" height="7"/></svg>'
    ),
    "pulse": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 12h4l2-6 4 12 2-6h6"/></svg>'
    ),
    "cert": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="10" r="5"/><path d="M9 14l-1 7 4-2 4 2-1-7"/></svg>'
    ),
    "nodes": (
        '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 6l4 5M17 6l-4 5M7 18l4-5M17 18l-4-5"/></svg>'
    ),
}

# (value, label) pairs for model field choices.
ICON_CHOICES = [(k, k.replace('_', ' ').title()) for k in ICONS]


def render_icon(key: str) -> str:
    """Return the inline SVG for ``key``, or an empty string if unknown."""
    return mark_safe(ICONS.get(key, ""))

# Brand marks for social links. Kept separate from ICONS so the icon
# dropdown on Services/Features is not cluttered with logos, and so a
# social entry cannot select a shield by mistake.
SOCIAL_ICONS = {
    "linkedin": (
        '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.13 1 2.5 1s2.48 1.12 2.48 2.5zM.22 8h4.56v14H.22V8zm7.4 0h4.37v1.92h.06c.61-1.16 2.1-2.38 4.32-2.38 4.62 0 5.47 3.04 5.47 7v7.46H17.3v-6.61c0-1.58-.03-3.62-2.2-3.62-2.21 0-2.55 1.72-2.55 3.5V22H8.18V8z"/></svg>'
    ),
    "x": (
        '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2H21l-6.52 7.45L22 22h-6.81l-4.78-6.27L4.8 22H2l7-8L1.86 2H8.8l4.32 5.71L18.244 2zm-2.39 18.18h1.6L7.27 3.72H5.55l10.3 16.46z"/></svg>'
    ),
    "github": (
        '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.92.58.1.78-.25.78-.56v-2c-3.2.7-3.87-1.36-3.87-1.36-.52-1.31-1.28-1.66-1.28-1.66-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.69 1.24 3.34.95.1-.74.4-1.24.72-1.52-2.55-.29-5.24-1.27-5.24-5.66 0-1.25.45-2.27 1.18-3.07-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.17a10.94 10.94 0 0 1 5.74 0c2.19-1.48 3.15-1.17 3.15-1.17.63 1.59.24 2.76.12 3.05.74.8 1.18 1.82 1.18 3.07 0 4.4-2.7 5.37-5.26 5.65.42.36.78 1.07.78 2.16v3.2c0 .31.2.66.79.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z"/></svg>'
    ),
}

SOCIAL_ICON_CHOICES = [
    ("linkedin", "LinkedIn"),
    ("x", "X / Twitter"),
    ("github", "GitHub"),
]


def render_social_icon(key: str) -> str:
    """Return the inline SVG for ``key``, or an empty string if unknown."""
    return mark_safe(SOCIAL_ICONS.get(key, ""))
