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
