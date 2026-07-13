import customtkinter as ctk
from model.i18n import _
from view.ui_components import (
    CARD_BG, CARD_BORDER, CONTENT_BG,
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
)
import os


class CreditsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
        scroll.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=16,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=60, pady=10)
        card.grid_columnconfigure(0, weight=1)

        logo_container = ctk.CTkFrame(card, width=90, height=90,
                                       fg_color=CARD_BORDER, corner_radius=45)
        logo_container.pack(anchor="center", pady=(28, 8))
        logo_container.pack_propagate(False)
        ctk.CTkLabel(logo_container, text="UNAS",
                     font=("Segoe UI", 18, "bold"),
                     text_color=ACCENT_PRIMARY).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=_("app.full_title"),
                     font=("Segoe UI", 20, "bold"), text_color=TEXT_PRIMARY).pack(anchor="center", pady=(4, 2))
        ctk.CTkLabel(card, text=_("app.version"),
                     font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="center", pady=(0, 20))

        sep = ctk.CTkFrame(card, height=1, fg_color=CARD_BORDER, corner_radius=0)
        sep.pack(fill="x", padx=40, pady=(0, 20))

        sections = [
            ("\uD83C\uDF93  " + _("credits.institution"), [
                (_("credits.unas"), _("credits.unas_sub")),
            ]),
            ("\uD83D\uDCBB  " + _("credits.career"), [
                (_("credits.career_name"), ""),
            ]),
            ("\uD83D\uDCDA  " + _("credits.course"), [
                (_("credits.course_name"), ""),
            ]),
            ("\uD83D\uDC68\u200D\uD83C\uDF93  " + _("credits.teacher"), [
                (_("credits.teacher_name"), ""),
            ]),
        ]

        for icon_title, items in sections:
            self._add_section(card, icon_title, items)

        sep2 = ctk.CTkFrame(card, height=1, fg_color=CARD_BORDER, corner_radius=0)
        sep2.pack(fill="x", padx=40, pady=(8, 16))

        self._add_section(card, "\uD83D\uDC65  " + _("credits.developers"), [
            (_("credits.dev1"), ""),
            (_("credits.dev2"), ""),
        ])

        ctk.CTkLabel(card, text=_("credits.rights"),
                     font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(anchor="center", pady=(20, 24))

    def _add_section(self, parent, icon_title, items):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=40, pady=(4, 2))

        ctk.CTkLabel(frame, text=icon_title,
                     font=("Segoe UI", 13, "bold"),
                     text_color=ACCENT_PRIMARY).pack(anchor="center", pady=(8, 4))

        for line, sub in items:
            ctk.CTkLabel(frame, text=line,
                         font=("Segoe UI", 13),
                         text_color=TEXT_PRIMARY).pack(anchor="center")
            if sub:
                ctk.CTkLabel(frame, text=sub,
                             font=("Segoe UI", 10),
                             text_color=TEXT_SECONDARY).pack(anchor="center", pady=(0, 2))
