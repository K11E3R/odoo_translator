"""Central color palette and styling helpers for the CustomTkinter UI."""

from __future__ import annotations


class Theme:
    """Reusable color palette for the PO Translator interface."""

    # Application backgrounds
    BACKGROUND = "#0b1220"
    SURFACE = "#111b2f"
    SURFACE_ALT = "#16243d"
    SURFACE_RAISED = "#1d2d4c"
    SURFACE_HOVER = "#24375f"

    # Sidebar
    SIDEBAR_BG = "#0f172a"
    SIDEBAR_SCROLLBAR = "#1a2742"
    SIDEBAR_SCROLLBAR_HOVER = "#213354"

    # Typography
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#cbd5f5"
    TEXT_MUTED = "#94a3b8"
    TEXT_PLACEHOLDER = "#64748b"

    # Accent colors
    ACCENT_PRIMARY = "#8b5cf6"
    ACCENT_PRIMARY_HOVER = "#7c3aed"
    ACCENT_SECONDARY = "#38bdf8"
    ACCENT_SECONDARY_HOVER = "#0ea5e9"
    ACCENT_SUCCESS = "#34d399"
    ACCENT_SUCCESS_HOVER = "#059669"
    ACCENT_WARNING = "#fbbf24"
    ACCENT_DANGER = "#f87171"

    # Table specific colors
    TABLE_HEADER_BG = "#15213a"
    TABLE_ROW_BG = "#111c30"
    TABLE_ROW_ALT_BG = "#0d1626"
    TABLE_ROW_SELECTED = "#1f2d4f"
    TABLE_SOURCE_MISMATCH = "#1b2b4a"
    TABLE_TRANSLATION_MISSING = "#3b1a2f"
    TABLE_TRANSLATION_MISMATCH = "#332612"

    # Badges and chips
    BADGE_SOURCE = "#7dd3fc"
    BADGE_SOURCE_MISMATCH = "#fde047"
    BADGE_TRANSLATION = "#6ee7b7"
    BADGE_TRANSLATION_MISMATCH = "#fcd34d"
    MODULE_CHIP_BG = "#1f2b46"
    MODULE_CHIP_TEXT = "#7dd3fc"

    DIVIDER = "#1f2937"
    INPUT_BG = "#1a2540"
    INPUT_HOVER = "#223156"


THEME = Theme()


def apply_root_theme(root) -> None:
    """Apply the base theme colors to the root window."""

    root.configure(fg_color=Theme.BACKGROUND)

