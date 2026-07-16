import customtkinter as ctk
import tkinterdnd2
import os as _os
from PIL import Image
from view.sampling_view import SamplingView
from view.dataset_view import DatasetHomeView, DatasetAnalysisView
from view.credits_view import CreditsView
from controller.controllers import SamplingController, DatasetController
from view.ui_components import (
    SIDEBAR_BG, CONTENT_BG, CARD_BG, CARD_BORDER,
    ACCENT_PRIMARY, ACCENT_SECONDARY, ACCENT_WARNING,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
)
from model.i18n import _, set_language, current_lang


def _init_dnd(root):
    try:
        td = _os.path.join(_os.path.dirname(tkinterdnd2.__file__), 'tkdnd', 'win-x64')
        root.tk.eval(f'lappend auto_path {{{td}}}')
        root.tk.eval('package require tkdnd')
    except Exception:
        pass


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        _init_dnd(self)

        self.title(_("app.title"))
        self.geometry("1360x820")
        self.minsize(1100, 720)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.sampling_controller = SamplingController()
        self.dataset_controller = DatasetController()

        self.active_nav = None
        self.home_view = None
        self.analysis_view = None
        self.credits_view = None
        self.lang_menu = None
        self.sidebar_status_label = None

        self.setup_ui()
        self.show_home()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=260, fg_color=SIDEBAR_BG, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(24, 4))

        self.logo_container = ctk.CTkFrame(logo_frame, width=100, height=100,
                                            fg_color="transparent", corner_radius=0)
        self.logo_container.pack(anchor="center")
        self.logo_container.pack_propagate(False)
        try:
            base_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            logo_path = _os.path.join(base_dir, "escudo_unas.png")
            if _os.path.exists(logo_path):
                pil_image = Image.open(logo_path)
                self.logo_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(100, 100))
                self.logo_label = ctk.CTkLabel(self.logo_container, image=self.logo_image, text="")
            else:
                self.logo_label = ctk.CTkLabel(self.logo_container, text="UNAS",
                                                font=("Segoe UI", 16, "bold"),
                                                text_color=ACCENT_PRIMARY)
        except Exception:
            self.logo_label = ctk.CTkLabel(self.logo_container, text="UNAS",
                                            font=("Segoe UI", 16, "bold"),
                                            text_color=ACCENT_PRIMARY)
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(logo_frame, text=_("app.full_title"),
                     font=("Segoe UI", 15, "bold"), text_color=TEXT_PRIMARY).pack(anchor="center", pady=(8, 0))

        accent_line = ctk.CTkFrame(sidebar, height=1, fg_color=CARD_BORDER, corner_radius=0)
        accent_line.pack(fill="x", padx=20, pady=(16, 8))

        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=4)

        self.nav_btns = {}
        nav_items = [
            ("home", "\uF0C1  " + _("nav.home"), _("nav.home_desc")),
            ("dataset", "\uF0CA  " + _("nav.dataset"), _("nav.dataset_desc")),
            ("sampling", "\uF0E8  " + _("nav.sampling"), _("nav.sampling_desc")),
            ("credits", "\uF05A  " + _("nav.credits"), _("nav.credits_desc")),
        ]

        for key, icon_text, desc in nav_items:
            frm = ctk.CTkFrame(nav_frame, fg_color="transparent")
            frm.pack(fill="x", pady=2)

            btn = ctk.CTkButton(frm, text=icon_text, anchor="w",
                                font=("Segoe UI", 13), height=38,
                                fg_color="transparent", hover_color="#162030",
                                text_color=TEXT_SECONDARY,
                                corner_radius=8)
            btn.pack(fill="x", padx=2)
            btn._desc = desc
            self.nav_btns[key] = btn

        self.nav_btns["home"].configure(command=lambda: self._nav_click("home"))
        self.nav_btns["dataset"].configure(command=lambda: self._nav_click("dataset"))
        self.nav_btns["sampling"].configure(command=lambda: self._nav_click("sampling"))
        self.nav_btns["credits"].configure(command=lambda: self._nav_click("credits"))

        ctk.CTkLabel(sidebar, text=_("nav.export_hint"),
                     font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(fill="x", padx=24, pady=(6, 0))

        tutorial_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        tutorial_frame.pack(side="bottom", fill="x", padx=16, pady=(0, 2))
        tutorial_btn = ctk.CTkButton(tutorial_frame, text="\u2753 Tutorial",
                                      font=("Segoe UI", 10, "bold"), height=28,
                                      fg_color="transparent", hover_color="#162030",
                                      text_color=TEXT_SECONDARY, corner_radius=8,
                                      command=self._start_tutorial)
        tutorial_btn.pack(anchor="center")

        self.sidebar_status = ctk.CTkLabel(sidebar, text=_("app.status_no_data"),
                                             font=("Segoe UI", 10),
                                             text_color=TEXT_MUTED)
        self.sidebar_status.pack(side="bottom", pady=(0, 8))

    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color=CONTENT_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _nav_click(self, key):
        self.active_nav = key
        if key == "home":
            self.show_home()
        elif key == "dataset":
            if self.dataset_controller.df is not None:
                self._show_view("dataset")
            else:
                self.show_home()
        elif key == "sampling":
            self._show_view("sampling")
        elif key == "credits":
            self._show_view("credits")

    def _highlight_nav(self, key):
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(fg_color="#162030", text_color=ACCENT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_home(self):
        self._highlight_nav("home")
        self._clear_content()
        from view.dataset_view import DatasetHomeView
        self.home_view = DatasetHomeView(
            self.content,
            self.dataset_controller,
            on_loaded=self._on_dataset_loaded,
        )
        self.home_view.pack(fill="both", expand=True)

    def _change_lang(self, lang):
        set_language(lang)
        self.title(_("app.title"))
        self.sidebar_status.configure(text=_("app.status_no_data") if self.dataset_controller.df is None else _("app.status_loaded"))
        nav_labels = {
            "home": "\uF0C1  " + _("nav.home"),
            "dataset": "\uF0CA  " + _("nav.dataset"),
            "sampling": "\uF0E8  " + _("nav.sampling"),
            "credits": "\uF05A  " + _("nav.credits"),
        }
        for k, btn in self.nav_btns.items():
            btn.configure(text=nav_labels.get(k, btn._text))
        ctk.CTkLabel(master=self, text="")  # trigger layout refresh
        if self.active_nav == "home":
            self.show_home()
        elif self.active_nav:
            self._show_view(self.active_nav)

    def _start_tutorial(self):
        from view.tutorial import TutorialOverlay
        steps = [
            {
                "title": "Bienvenido",
                "text": "Esta aplicación te permite analizar datos estadísticamente. "
                        "Carga un archivo CSV o Excel para comenzar.",
            },
            {
                "title": "Navegación",
                "text": "Usa el menú lateral para cambiar entre las secciones: "
                        "Inicio, Procesar Dataset, M.A.S. y Créditos.",
            },
            {
                "title": "Carga de datos",
                "text": "Arrastra un archivo CSV o Excel al área punteada, o haz clic "
                        "en 'Seleccionar archivo'. También puedes importar desde Google Sheets "
                        "o conectar a una base de datos SQL.",
            },
            {
                "title": "Análisis de variables",
                "text": "Una vez cargado el dataset, verás la lista de variables en el panel "
                        "izquierdo. Haz clic en cualquier variable para ver su tabla de frecuencias, "
                        "medidas estadísticas y gráficos.",
            },
            {
                "title": "Exportar APA 7",
                "text": "Usa el botón 'Exportar APA 7' para generar un reporte profesional "
                        "en formato Word siguiendo las normas APA 7ª edición.",
            },
        ]
        TutorialOverlay(self, steps)

    def _on_dataset_loaded(self):
        self.sidebar_status.configure(text=_("app.status_loaded"))
        self.nav_btns["dataset"].configure(text="\uF0CA  " + _("nav.dataset"))
        self._show_view("dataset")

    def _show_view(self, view_name):
        self._clear_content()
        self._highlight_nav(view_name)

        if view_name == "dataset":
            from view.dataset_view import DatasetAnalysisView
            self.analysis_view = DatasetAnalysisView(
                self.content,
                self.dataset_controller,
            )
            self.analysis_view.pack(fill="both", expand=True)
            if hasattr(self, 'home_view') and self.home_view:
                self.home_view = None

        elif view_name == "sampling":
            sv = SamplingView(self.content, self.sampling_controller)
            sv.pack(fill="both", expand=True)

        elif view_name == "credits":
            cv = CreditsView(self.content)
            cv.pack(fill="both", expand=True)

    def run(self):
        self.mainloop()
