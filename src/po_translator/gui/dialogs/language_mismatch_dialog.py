"""Dialog presenting options when language mismatches are detected."""

from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, Optional

import customtkinter as ctk

from ..theme import THEME


class LanguageMismatchDialog(ctk.CTkToplevel):
    """Modal dialog that gives users options for mismatched languages."""

    def __init__(
        self,
        parent,
        statuses: Iterable,
        expected_source: str,
        expected_target: str,
        language_names: Dict[str, str],
    ) -> None:
        super().__init__(parent)
        self.title("Review Language Mismatch")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=THEME.SURFACE)

        self.result: Optional[str] = None

        self._language_names = language_names
        self._expected_source = expected_source
        self._expected_target = expected_target
        self._statuses = list(statuses)

        self._build_ui()
        self.bind("<Escape>", lambda _event: self._close("cancel"))

        # Center on parent window
        self.update_idletasks()
        if parent:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            width = self.winfo_width()
            height = self.winfo_height()
            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2
            self.geometry(f"{width}x{height}+{x}+{y}")

        self.wait_visibility()
        self.focus_force()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, padx=28, pady=24, sticky="nsew")

        heading = ctk.CTkLabel(
            container,
            text="We found language mismatches",
            font=THEME.font(size=20, weight="bold"),
            text_color=THEME.TEXT_PRIMARY,
        )
        heading.pack(anchor="w")

        description = (
            "Some source entries or translations don't align with the languages "
            "you selected. Choose how you want to handle them before continuing."
        )
        ctk.CTkLabel(
            container,
            text=description,
            font=THEME.font(size=12),
            text_color=THEME.TEXT_MUTED,
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(8, 18))

        summary_frame = ctk.CTkFrame(
            container,
            fg_color=THEME.SURFACE_ALT,
            corner_radius=10,
        )
        summary_frame.pack(fill="x", pady=(0, 18))

        self._build_summary(summary_frame)

        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.pack(fill="x")

        # Buttons
        ctk.CTkButton(
            action_frame,
            text="✨ Normalize & Translate",
            fg_color=THEME.ACCENT_PRIMARY,
            hover_color=THEME.ACCENT_PRIMARY_HOVER,
            command=lambda: self._close("normalize"),
            height=44,
            font=THEME.font(size=13, weight="bold"),
            text_color="#ffffff",
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            action_frame,
            text="🛟 Keep Source Texts Intact",
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            command=lambda: self._close("keep"),
            height=44,
            font=THEME.font(size=13),
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            action_frame,
            text="Cancel",
            fg_color=THEME.INPUT_BG,
            hover_color=THEME.INPUT_HOVER,
            text_color=THEME.TEXT_SECONDARY,
            command=lambda: self._close("cancel"),
            height=38,
            font=THEME.font(size=12),
        ).pack(fill="x")

    def _build_summary(self, frame) -> None:
        frame.grid_columnconfigure(1, weight=1)

        source_counts = Counter()
        target_counts = Counter()
        unknown_sources = 0
        unknown_targets = 0

        for status in self._statuses:
            if status.source_matches is False and status.source_lang:
                source_counts[status.source_lang] += 1
            elif status.source_lang is None:
                unknown_sources += 1

            if status.translation_matches is False and status.translation_lang:
                target_counts[status.translation_lang] += 1
            elif status.translation_lang is None and not status.missing_translation:
                unknown_targets += 1

        expected_source = self._format_lang(self._expected_source)
        expected_target = self._format_lang(self._expected_target)

        lines = []
        if source_counts or unknown_sources:
            mismatch = self._format_counts(source_counts, unknown_sources)
            lines.append(f"Source should be {expected_source} → detected {mismatch}")

        if target_counts or unknown_targets:
            mismatch = self._format_counts(target_counts, unknown_targets)
            lines.append(
                f"Translation should be {expected_target} → detected {mismatch}"
            )

        if not lines:
            lines.append("All mismatched entries will be rechecked during translation.")

        for line in lines:
            ctk.CTkLabel(
                frame,
                text=f"• {line}",
                justify="left",
                anchor="w",
                font=THEME.font(size=12),
                text_color=THEME.TEXT_PRIMARY,
                wraplength=460,
            ).pack(anchor="w", padx=18, pady=(12, 0))

        ctk.CTkLabel(
            frame,
            text=(
                "Choosing “Normalize & Translate” will reprocess flagged entries "
                "so they respect the selected languages."
            ),
            font=THEME.font(size=11),
            text_color=THEME.TEXT_MUTED,
            wraplength=460,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(16, 16))

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _format_lang(self, code: Optional[str]) -> str:
        if not code:
            return "Unknown"
        return self._language_names.get(code, code.upper())

    def _format_counts(self, counts: Counter, unknown: int) -> str:
        parts = [
            f"{self._format_lang(code)} × {count}"
            for code, count in counts.most_common()
        ]
        if unknown:
            parts.append(f"Unknown × {unknown}")
        return ", ".join(parts) if parts else "Unknown"

    def _close(self, result: str) -> None:
        self.result = result
        self.grab_release()
        self.destroy()
