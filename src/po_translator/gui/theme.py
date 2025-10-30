"""Central color palette and styling helpers for the CustomTkinter UI."""

from __future__ import annotations

import customtkinter as ctk


class Theme:
    """Reusable color palette for the PO Translator interface."""

    # Application backgrounds
    BACKGROUND = "#f5f7fb"
    SURFACE = "#ffffff"
    SURFACE_ALT = "#eef2ff"
    SURFACE_RAISED = "#f2f6ff"
    SURFACE_HOVER = "#dbeafe"

    # Sidebar
    SIDEBAR_BG = "#f9fbff"
    SIDEBAR_SCROLLBAR = "#cbd5f5"
    SIDEBAR_SCROLLBAR_HOVER = "#94a3ff"

    # Typography
    TEXT_PRIMARY = "#1f2937"
    TEXT_SECONDARY = "#334155"
    TEXT_MUTED = "#64748b"
    TEXT_PLACEHOLDER = "#94a3b8"

    # Accent colors
    ACCENT_PRIMARY = "#2563eb"
    ACCENT_PRIMARY_HOVER = "#1d4ed8"
    ACCENT_SECONDARY = "#0ea5e9"
    ACCENT_SECONDARY_HOVER = "#0284c7"
    ACCENT_SUCCESS = "#10b981"
    ACCENT_SUCCESS_HOVER = "#059669"
    ACCENT_WARNING = "#f59e0b"
    ACCENT_DANGER = "#ef4444"

    # Table specific colors
    TABLE_HEADER_BG = "#e0e7ff"
    TABLE_ROW_BG = "#ffffff"
    TABLE_ROW_ALT_BG = "#f8fafc"
    TABLE_ROW_SELECTED = "#dbeafe"
    TABLE_SOURCE_MISMATCH = "#fee2e2"
    TABLE_TRANSLATION_MISSING = "#fef3c7"
    TABLE_TRANSLATION_MISMATCH = "#fce7f3"

    # Badges and chips
    BADGE_SOURCE = "#bfdbfe"
    BADGE_SOURCE_MISMATCH = "#facc15"
    BADGE_TRANSLATION = "#bbf7d0"
    BADGE_TRANSLATION_MISMATCH = "#f9a8d4"
    MODULE_CHIP_BG = "#e2e8f0"
    MODULE_CHIP_TEXT = "#2563eb"

    DIVIDER = "#e2e8f0"
    INPUT_BG = "#f1f5f9"
    INPUT_HOVER = "#e2e8f0"

    FONT_FAMILY = "Segoe UI"

    @staticmethod
    def font(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
        """Return a themed font instance for consistent typography."""

        return ctk.CTkFont(family=Theme.FONT_FAMILY, size=size, weight=weight)


THEME = Theme()


def apply_root_theme(root) -> None:
    """Apply the base theme colors to the root window."""

    root.configure(fg_color=Theme.BACKGROUND)

