import customtkinter as ctk
from tkinter import filedialog, messagebox
from model.i18n import _
from view.ui_components import (
    TableWidget, ScrollableResultsFrame, MetricCard,
    CARD_BG, CARD_BORDER, CONTENT_BG,
    ACCENT_PRIMARY, ACCENT_SECONDARY, ACCENT_WARNING, ACCENT_PURPLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
)
import os
import pandas as pd


class DatasetHomeView(ctk.CTkFrame):
    def __init__(self, master, controller, on_loaded=None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.on_loaded = on_loaded
        self.configure(fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.place(relx=0.5, rely=0.4, anchor="center")

        ctk.CTkLabel(container, text="Auto-Analizador de Encuestas",
                     font=("Segoe UI", 26, "bold"), text_color=TEXT_PRIMARY).pack(pady=(0, 4))
        ctk.CTkLabel(container, text=_("home.subtitle"),
                     font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(pady=(0, 24))

        self.drop_frame = ctk.CTkFrame(container, width=480, height=340,
                                        fg_color=CARD_BG, corner_radius=16,
                                        border_width=2, border_color=ACCENT_PRIMARY)
        self.drop_frame.pack()
        self.drop_frame.pack_propagate(False)

        icon_bg = ctk.CTkFrame(self.drop_frame, width=72, height=72,
                                fg_color=CARD_BORDER, corner_radius=36)
        icon_bg.place(relx=0.5, rely=0.18, anchor="center")
        ctk.CTkLabel(icon_bg, text="\u2B07", font=("Segoe UI", 28),
                     text_color=ACCENT_PRIMARY).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.drop_frame, text="Arrastra tu archivo aqu\u00ED",
                     font=("Segoe UI", 16, "bold"), text_color=TEXT_PRIMARY).place(relx=0.5, rely=0.37, anchor="center")
        ctk.CTkLabel(self.drop_frame, text="o haz clic para examinar",
                     font=("Segoe UI", 12), text_color=TEXT_SECONDARY).place(relx=0.5, rely=0.48, anchor="center")
        ctk.CTkLabel(self.drop_frame, text="Formatos: CSV, XLS, XLSX",
                     font=("Segoe UI", 10), text_color=TEXT_MUTED).place(relx=0.5, rely=0.57, anchor="center")

        browse_btn = ctk.CTkButton(self.drop_frame, text=_("home.browse_btn"),
                                    font=("Segoe UI", 12, "bold"), height=34,
                                    fg_color=ACCENT_PRIMARY, hover_color="#1976d2",
                                    corner_radius=8,
                                    command=self._browse_file)
        browse_btn.place(relx=0.5, rely=0.68, anchor="center")

        btn_frame = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        btn_frame.place(relx=0.5, rely=0.86, anchor="center")

        sheets_btn = ctk.CTkButton(btn_frame, text="Importar de Google Sheets",
                                    font=("Segoe UI", 11, "bold"), height=32,
                                    fg_color="#34a853", hover_color="#2e7d32",
                                    corner_radius=8,
                                    command=self._import_from_google_sheets)
        sheets_btn.pack(side="left", padx=6)

        sql_btn = ctk.CTkButton(btn_frame, text="Conectar a Base de Datos",
                                 font=("Segoe UI", 11, "bold"), height=32,
                                 fg_color="#37474f", hover_color="#455a64",
                                 corner_radius=8,
                                 command=self._import_from_sql)
        sql_btn.pack(side="left", padx=6)

        self._bind_click_all(self.drop_frame)
        self._setup_drag_drop()

        self.progress_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400,
                                                mode="indeterminate",
                                                fg_color=CARD_BORDER,
                                                progress_color=ACCENT_PRIMARY)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="",
                                            font=("Segoe UI", 11), text_color=TEXT_SECONDARY)

        self.error_label = ctk.CTkLabel(container, text="", font=("Segoe UI", 11),
                                         text_color=ACCENT_WARNING)

    def _bind_click_all(self, widget):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", lambda e: self._browse_file(), add="+")
        for child in widget.winfo_children():
            self._bind_click_all(child)

    def _setup_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)
            self.drop_frame.dnd_bind('<<DragEnter>>', lambda e: self.drop_frame.configure(border_color="#00e676"))
            self.drop_frame.dnd_bind('<<DragLeave>>', lambda e: self.drop_frame.configure(border_color=ACCENT_PRIMARY))
            self.drop_frame.dnd_bind('<<DragEnd>>', lambda e: self.drop_frame.configure(border_color=ACCENT_PRIMARY))
        except Exception:
            pass

    def _on_drop(self, event):
        self.drop_frame.configure(border_color=ACCENT_PRIMARY)
        raw = event.data.strip()
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        elif raw.startswith("\"") and raw.endswith("\""):
            raw = raw[1:-1]
        if os.path.isfile(raw):
            self._load_file(raw)

    def _browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de datos",
            filetypes=[("Archivos CSV", "*.csv"), ("Archivos Excel", "*.xls;*.xlsx"),
                       ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return
        self._load_file(filepath)

    def _load_file(self, filepath):
        self._show_progress("Cargando archivo...")
        self.update()

        result = self.controller.load_file(filepath)
        if not result["success"]:
            self._hide_progress()
            self.error_label.configure(text=result["error"])
            self.error_label.pack(pady=(8, 0))
            return

        self._show_progress("Clasificando variables...")
        self.update()

        data = result["data"]
        for col in data["columns"]:
            self.controller.analyze_variable(col)

        self._show_progress("Aplicando regla de Sturges...")
        self.update()
        import time
        time.sleep(0.3)

        self._hide_progress()
        self.error_label.pack_forget()

        if self.on_loaded:
            self.on_loaded()

    def _show_progress(self, text):
        self.progress_frame.pack(pady=(20, 0))
        self.progress_label.configure(text=text)
        self.progress_label.pack(pady=(0, 6))
        self.progress_bar.pack()
        self.progress_bar.start()

    def _hide_progress(self):
        self.progress_bar.stop()
        self.progress_frame.pack_forget()

    def _import_from_google_sheets(self):
        import tkinter.simpledialog as sd
        url = sd.askstring("Google Sheets", "Ingresa la URL o ID de Google Sheets:", parent=self)
        if not url:
            return
        self._show_progress("Importando desde Google Sheets...")
        self.update()
        result = self.controller.load_from_google_sheets(url)
        self._hide_progress()
        if not result["success"]:
            self.error_label.configure(text=result["error"])
            self.error_label.pack(pady=(8, 0))
            return
        self.error_label.pack_forget()
        if self.on_loaded:
            self.on_loaded()

    def _import_from_sql(self):
        import tkinter.simpledialog as sd
        conn_str = sd.askstring("Base de Datos", "Ingresa la cadena de conexión (ej: mysql+pymysql://user:pass@host/db):", parent=self)
        if not conn_str:
            return
        query = sd.askstring("Base de Datos", "Ingresa la consulta SQL:", parent=self, initialvalue="SELECT * FROM ...")
        if not query:
            return
        self._show_progress("Conectando a base de datos...")
        self.update()
        result = self.controller.load_from_sql(conn_str, query)
        self._hide_progress()
        if not result["success"]:
            self.error_label.configure(text=result["error"])
            self.error_label.pack(pady=(8, 0))
            return
        self.error_label.pack_forget()
        if self.on_loaded:
            self.on_loaded()


class DatasetAnalysisView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.current_var = None
        self.showing_summary = False
        self.configure(fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.grid(row=0, column=0, sticky="ew", pady=(12, 4), padx=12)
        topbar.columnconfigure(0, weight=1)

        topbar_inner = ctk.CTkFrame(topbar, fg_color=CARD_BG, corner_radius=10)
        topbar_inner.pack(fill="x")

        ctk.CTkLabel(topbar_inner, text=_("dataset.analysis_panel"),
                     font=("Segoe UI", 15, "bold"), text_color=TEXT_PRIMARY).pack(side="left", padx=16, pady=10)

        self.summary_btn = ctk.CTkButton(topbar_inner, text=_("dataset.summary_btn"),
                                          command=self.show_full_summary,
                                          font=("Segoe UI", 11, "bold"), height=30,
                                          fg_color="#37474f", hover_color="#455a64",
                                          state="disabled")
        self.summary_btn.pack(side="right", padx=(4, 12), pady=8)

        self.export_btn = ctk.CTkButton(topbar_inner, text=_("dataset.export_btn"),
                                         command=self.export_report,
                                         font=("Segoe UI", 11, "bold"), height=30,
                                         fg_color=ACCENT_PRIMARY, hover_color="#1976d2",
                                         state="disabled")
        self.export_btn.pack(side="right", padx=4, pady=8)

        self.pay_block_frame = ctk.CTkFrame(topbar_inner, fg_color="#bf360c", corner_radius=6)
        self.pay_btn = ctk.CTkButton(self.pay_block_frame, text=_("export.pay_blocked"),
                                      command=self._show_payment_dialog,
                                      font=("Segoe UI", 10, "bold"), height=26,
                                      fg_color="#bf360c", hover_color="#e65100",
                                      text_color="#ffffff")
        self.pay_btn.pack(padx=8, pady=3)
        self.pay_block_frame.pack(side="right", padx=4, pady=8)
        self.pay_block_frame.pack_forget()

        status_bar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=6, height=28)
        status_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 8))
        self.status_label = ctk.CTkLabel(status_bar, text=_("dataset.status_loaded"),
                                          font=("Segoe UI", 10), anchor="w",
                                          text_color=TEXT_SECONDARY)
        self.status_label.pack(side="left", padx=12, pady=2)

        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=1, column=0, sticky="nsew", padx=12)
        main_area.columnconfigure(0, weight=0)
        main_area.columnconfigure(1, weight=1)
        main_area.rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(main_area, width=240, corner_radius=10, fg_color=CARD_BG)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        sidebar.grid_propagate(False)

        sidebar_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        sidebar_header.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(sidebar_header, text=_("dataset.variables_title"),
                     font=("Segoe UI", 12, "bold"), text_color=ACCENT_PRIMARY).pack(side="left")

        self.var_listbox = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", height=400)
        self.var_listbox.pack(fill="both", expand=True, padx=6, pady=2)

        info_panel = ctk.CTkFrame(sidebar, corner_radius=8, fg_color="transparent")
        info_panel.pack(fill="x", padx=8, pady=(4, 10))
        info_inner = ctk.CTkFrame(info_panel, fg_color=CARD_BG, corner_radius=8,
                                   border_width=1, border_color=CARD_BORDER)
        info_inner.pack(fill="x")
        self.info_rows_label = ctk.CTkLabel(info_inner, text=f"{_('dataset.rows')}: \u2014",
                                              font=("Segoe UI", 10), text_color=TEXT_PRIMARY)
        self.info_rows_label.pack(anchor="w", padx=12, pady=2)
        self.info_cols_label = ctk.CTkLabel(info_inner, text=f"{_('dataset.columns')}: \u2014",
                                              font=("Segoe UI", 10), text_color=TEXT_PRIMARY)
        self.info_cols_label.pack(anchor="w", padx=12, pady=2)
        self.info_status_label = ctk.CTkLabel(info_inner, text=f"{_('app.status_ready')}: \u2014",
                                                font=("Segoe UI", 10), text_color=TEXT_PRIMARY)
        self.info_status_label.pack(anchor="w", padx=12, pady=2)

        self.results_area = ScrollableResultsFrame(main_area, fg_color="transparent")
        self.results_area.grid(row=0, column=1, sticky="nsew")

        if self.controller.df is not None:
            self._rebuild_variable_list()

    def _rebuild_variable_list(self):
        data = {
            "rows": len(self.controller.df),
            "cols": len(self.controller.df.columns),
            "columns": list(self.controller.df.columns),
            "classification": self.controller.classification,
            "has_empty_cells": self.controller.df.isnull().any().any(),
        }
        filename = getattr(self.controller, '_filename', 'Dataset')

        self.status_label.configure(text=f"Estado: {os.path.basename(filename) if isinstance(filename, str) and os.path.exists(filename) else 'Dataset'}  \u2014  {data['rows']} filas, {data['cols']} columnas")
        self.info_rows_label.configure(text=f"Filas: {data['rows']}")
        self.info_cols_label.configure(text=f"Columnas: {data['cols']}")

        if data.get("has_empty_cells"):
            self.info_status_label.configure(text=_("dataset.status_empty"), text_color=ACCENT_WARNING)
        else:
            self.info_status_label.configure(text=_("dataset.status_complete"), text_color=ACCENT_SECONDARY)

        for widget in self.var_listbox.winfo_children():
            widget.destroy()

        type_styles = {
            "cualitativa_nominal": ("Cual. Nominal", ACCENT_PURPLE),
            "cualitativa_ordinal": ("Cual. Ordinal", "#b388ff"),
            "cuantitativa_discreta": ("Cuan. Discreta", ACCENT_SECONDARY),
            "cuantitativa_continua": ("Cuan. Continua", ACCENT_PRIMARY),
        }

        summary_btn = ctk.CTkButton(self.var_listbox, text=_("dataset.summary_btn"),
                                     anchor="w", font=("Segoe UI", 11, "bold"), height=32,
                                     fg_color="#263238", hover_color="#37474f",
                                     command=self.show_full_summary)
        summary_btn.pack(fill="x", padx=2, pady=3)

        sep = ctk.CTkFrame(self.var_listbox, height=1, fg_color=CARD_BORDER)
        sep.pack(fill="x", padx=8, pady=4)

        for col in data["columns"]:
            var_type = data["classification"].get(col, "desconocido")
            label, color = type_styles.get(var_type, ("?", TEXT_MUTED))

            frm = ctk.CTkFrame(self.var_listbox, fg_color="transparent")
            frm.pack(fill="x", padx=2, pady=1)

            btn = ctk.CTkButton(frm, text=f"  {col}", anchor="w",
                                 font=("Segoe UI", 11), height=28,
                                 fg_color="transparent", hover_color="#1e2a3a",
                                 command=lambda v=col: self.analyze_variable(v))
            btn.pack(side="left", fill="x", expand=True)

            badge = ctk.CTkLabel(frm, text=label, font=("Segoe UI", 8, "bold"),
                                  text_color=color, fg_color="#1a2332",
                                  corner_radius=4, padx=5, pady=2)
            badge.pack(side="right", padx=(0, 4))

        self.summary_btn.configure(state="normal")
        self.export_btn.configure(state="disabled")
        self.current_var = None
        self.showing_summary = False

        self.results_area.clear()
        self.results_area.add_section_title(_("dataset.loaded_ok"))
        self.results_area.add_text(_("dataset.select_var"))

    def show_full_summary(self):
        if self.controller.df is None:
            return
        self.showing_summary = True
        self.current_var = None
        self.export_btn.configure(state="normal")

        self.results_area.clear()
        self.results_area.add_section_title(_("dataset.summary_title"))

        n_quant = sum(1 for t in self.controller.classification.values()
                      if t.startswith("cuantitativa"))
        n_qual = sum(1 for t in self.controller.classification.values()
                     if t.startswith("cualitativa"))
        n_total = len(self.controller.df.columns)

        self.results_area.add_metrics_row([
            {"title": _("dataset.total_vars"), "value": str(n_total),
             "gradient_from": "#1a237e", "gradient_to": "#283593"},
            {"title": _("dataset.quant_vars"), "value": str(n_quant),
             "gradient_from": "#00695c", "gradient_to": "#00897b"},
            {"title": _("dataset.qual_vars"), "value": str(n_qual),
             "gradient_from": "#4a148c", "gradient_to": "#6a1b9a"},
            {"title": _("dataset.records"), "value": str(len(self.controller.df)),
             "gradient_from": "#e65100", "gradient_to": "#ef6c00"},
        ])

        result = self.controller.analyze_all()
        if result["success"] and result["data"]["summary"] is not None:
            self.results_area.add_separator()
            self.results_area.add_subtitle(_("dataset.descriptive_stats"))
            summary = result["data"]["summary"]
            cols = list(summary.columns)
            rows = []
            for _, r in summary.iterrows():
                rows.append([f"{v:.4f}" if isinstance(v, float) else str(v) for v in r])
            self.results_area.add_table(cols, rows)

    def analyze_variable(self, var_name: str):
        self.current_var = var_name
        self.showing_summary = False
        self.results_area.clear()
        self.results_area.add_section_title(f"Analizando variable: {var_name}")
        self.results_area.add_text("Procesando...")
        self.update()

        result = self.controller.analyze_variable(var_name)
        if not result["success"]:
            self.results_area.clear()
            self.results_area.add_section_title(f"Error al analizar {var_name}")
            self.results_area.add_text(result["error"])
            return

        data = result["data"]
        freq_result = data["freq_result"]
        measures = data["measures"]
        charts = data["charts"]
        var_type = data["var_type"]
        n_null = data["n_null"]

        self.export_btn.configure(state="normal")
        self.results_area.clear()

        type_labels = {
            "cualitativa_nominal": "Cualitativa Nominal",
            "cualitativa_ordinal": "Cualitativa Ordinal",
            "cuantitativa_discreta": "Cuantitativa Discreta",
            "cuantitativa_continua": "Cuantitativa Continua",
        }
        type_badge = type_labels.get(var_type, var_type.replace("_", " ").title())

        n = freq_result["n"]
        self.results_area.add_metrics_row([
            {"title": "Variable", "value": var_name,
             "gradient_from": "#1a237e", "gradient_to": "#283593"},
            {"title": "Tipo", "value": type_badge,
             "gradient_from": "#4a148c", "gradient_to": "#6a1b9a"},
            {"title": "n (v\u00E1lidos)", "value": str(n),
             "gradient_from": "#00695c", "gradient_to": "#00897b"},
            {"title": "Nulos", "value": str(n_null),
             "gradient_from": "#bf360c", "gradient_to": "#e65100"},
        ])

        if measures and measures.get("type") == "cualitativa":
            self.results_area.add_text(f"Moda (Mo): {measures['mode']}")

        self.results_area.add_separator()
        self.results_area.add_subtitle(_("dataset.freq_table"))
        table = freq_result["table"]

        if freq_result["is_grouped"]:
            display_cols = ["Intervalo", "Xi", "fi", "Fi", "hi", "hi%", "Hi%"]
        else:
            display_cols = [table.columns[0], "fi", "Fi", "hi", "hi%", "Hi%"]

        rows = []
        for _, row in table[display_cols].iterrows():
            rows.append([f"{v:.4f}" if isinstance(v, float) else str(v) for v in row])

        self.results_area.add_table(display_cols, rows)

        if freq_result["is_grouped"]:
            info = (f"Rango (R) = {freq_result.get('R', 0):.2f}  |  "
                    f"Intervalos (m) = {freq_result.get('m', 0)}  |  "
                    f"Amplitud (C) = {freq_result.get('C', 0):.2f}")
            self.results_area.add_text(info)

        if measures and measures.get("type") != "cualitativa":
            self.results_area.add_separator()
            self.results_area.add_section_title("Medidas Estad\u00EDsticas")

            self.results_area.add_subtitle(_("dataset.central_tendency"))
            self.results_area.add_table(["Medida", "Valor"], [
                ["Media (X\u0304)", f"{measures['mean']:.4f}"],
                ["Mediana (Me)", f"{measures['median']:.4f}"],
                ["Moda (Mo)", f"{measures['mode']:.4f}"],
                ["Media Geom\u00E9trica (X\u0304g)", f"{measures['geometric_mean']:.4f}"],
                ["Media Arm\u00F3nica (Mh)", f"{measures['harmonic_mean']:.4f}"],
            ])

            self.results_area.add_subtitle(_("dataset.dispersion"))
            self.results_area.add_table(["Medida", "Valor"], [
                ["Rango", f"{measures['range']:.4f}"],
                ["Varianza (S\u00B2)", f"{measures['variance']:.4f}"],
                ["Desviaci\u00F3n Est\u00E1ndar (S)", f"{measures['std_dev']:.4f}"],
                ["Coef. Variaci\u00F3n (CV%)", f"{measures['cv']:.2f}%"],
            ])

            self.results_area.add_subtitle(_("dataset.position"))
            self.results_area.add_table(
                ["Medida", "Valor", "Medida", "Valor", "Medida", "Valor"],
                [
                    ["Q\u2081", f"{measures['Q1']:.4f}", "D\u2081", f"{measures['D1']:.4f}",
                     "P\u2081\u2080", f"{measures['P10']:.4f}"],
                    ["Q\u2082 (Mediana)", f"{measures['Q2']:.4f}", "D\u2085", f"{measures['D5']:.4f}",
                     "P\u2082\u2085", f"{measures['P25']:.4f}"],
                    ["Q\u2083", f"{measures['Q3']:.4f}", "D\u2089", f"{measures['D9']:.4f}",
                     "P\u2085\u2080", f"{measures['P50']:.4f}"],
                    ["\u2014", "\u2014", "\u2014", "\u2014", "P\u2087\u2085", f"{measures['P75']:.4f}"],
                    ["\u2014", "\u2014", "\u2014", "\u2014", "P\u2089\u2080", f"{measures['P90']:.4f}"],
                ])

            self.results_area.add_subtitle(_("dataset.shape"))
            self.results_area.add_table(["Medida", "Valor"], [
                ["Coef. Asimetr\u00EDa (g\u2081)", f"{measures['skewness']:.4f}"],
                ["Coef. Curtosis (g\u2082)", f"{measures['kurtosis']:.4f}"],
            ])

            skew = measures["skewness"]
            if skew > 0.5:
                interp_skew = "Asimetr\u00EDa positiva (cola a la derecha)"
            elif skew < -0.5:
                interp_skew = "Asimetr\u00EDa negativa (cola a la izquierda)"
            else:
                interp_skew = "Distribuci\u00F3n aproximadamente sim\u00E9trica"

            kurt = measures["kurtosis"]
            if kurt > 0:
                interp_kurt = "Leptoc\u00FArtica (mayor apuntamiento que la normal)"
            elif kurt < 0:
                interp_kurt = "Platic\u00FArtica (menor apuntamiento que la normal)"
            else:
                interp_kurt = "Mesoc\u00FArtica (similar a la normal)"

            self.results_area.add_text(f"Asimetr\u00EDa: {interp_skew}  |  Curtosis: {interp_kurt}")

            self.results_area.add_separator()
            self.results_area.add_subtitle(_("dataset.interpretation"))
            all_r = self.controller.analyze_all()
            if all_r["success"]:
                from model.statistics import DatasetSummary
                interp_text = DatasetSummary.generate_interpretation(measures, var_name)
                if interp_text:
                    frame = ctk.CTkFrame(self.results_area, fg_color=CARD_BG, corner_radius=8)
                    frame.pack(fill="x", padx=8, pady=4)
                    ctk.CTkLabel(frame, text=interp_text, font=("Segoe UI", 11),
                                  anchor="w", justify="left", wraplength=650,
                                  text_color=TEXT_PRIMARY).pack(padx=14, pady=10)

        if charts:
            self.results_area.add_separator()
            self.results_area.add_section_title(_("dataset.charts"))
            for chart_key, chart_bytes in charts.items():
                titles = {
                    "bar": _("charts.bar"),
                    "pie": _("charts.pie"),
                    "bar_ogive": _("charts.bar_ogive"),
                    "histogram": _("charts.histogram"),
                }
                self.results_area.add_subtitle(titles.get(chart_key, chart_key))
                self.results_area.add_chart(chart_bytes, width=540, height=330)

    def export_report(self):
        if self.controller.df is None:
            messagebox.showwarning(_("warning"), _("export.no_data"))
            return

        filepath = filedialog.asksaveasfilename(
            title=_("export.save_title"),
            defaultextension=".docx",
            filetypes=[("Documento Word", "*.docx")],
            initialfile=_("export.save_filename"),
        )
        if not filepath:
            return

        result = self.controller.export_report(
            sampling_result=None,
            var_name=None,
            output_path=filepath,
        )

        if result["success"]:
            messagebox.showinfo(
                "\u2705 Exportaci\u00F3n exitosa",
                f"Reporte guardado en:\n{result['path']}"
            )
            if result.get("show_payment"):
                self.export_btn.configure(state="disabled")
                self.pay_block_frame.pack(before=self.export_btn, side="right", padx=4)
                self._show_payment_dialog()
        else:
            messagebox.showerror("Error", result["error"])

    def _show_payment_dialog(self):
        import datetime
        from PIL import Image

        win = ctk.CTkToplevel(self)
        win.title(_("export.pay_title"))
        win.geometry("460x640")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        win.attributes("-toolwindow", True)

        frame = ctk.CTkFrame(win, fg_color=CARD_BG, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text=_("export.pay_subtitle"),
                     font=("Segoe UI", 18, "bold"), text_color="#ff4081").pack(pady=(16, 4))
        ctk.CTkLabel(frame, text=_("export.pay_desc"),
                     font=("Segoe UI", 11), text_color=TEXT_SECONDARY, wraplength=380).pack(pady=(4, 8))

        ctk.CTkLabel(frame, text=_("export.pay_step1"), font=("Segoe UI", 12),
                     text_color=TEXT_PRIMARY).pack(pady=(4, 2))
        ctk.CTkLabel(frame, text=_("export.pay_account"), font=("Segoe UI", 22, "bold"),
                     text_color=ACCENT_PRIMARY).pack(pady=(0, 2))
        ctk.CTkLabel(frame, text=_("export.pay_instructions"),
                     font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(pady=(0, 6))

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qr_path = None
        for ext in [".png", ".jpg", ".jpeg", ".bmp"]:
            test_path = os.path.join(base_dir, f"codigo_qr{ext}")
            if os.path.exists(test_path):
                qr_path = test_path
                break
        if qr_path:
            img = Image.open(qr_path)
            img = img.resize((160, 160))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(160, 160))
            ctk.CTkLabel(frame, image=ctk_img, text="").pack(pady=4)

        ctk.CTkLabel(frame, text=_("export.pay_step2"),
                     font=("Segoe UI", 12), text_color=TEXT_PRIMARY).pack(pady=(8, 2))
        ctk.CTkLabel(frame, text=_("export.pay_hint"),
                     font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(pady=(0, 4))

        codigo_entry = ctk.CTkEntry(frame, placeholder_text=_("export.pay_placeholder"), width=250,
                                      font=("Segoe UI", 14), justify="center")
        codigo_entry.pack(pady=4)

        error_label = ctk.CTkLabel(frame, text="", font=("Segoe UI", 10), text_color=ACCENT_WARNING)
        error_label.pack()

        used_codes_path = os.path.join(base_dir, "codigos_usados.txt")

        def validar_codigo():
            codigo = codigo_entry.get().strip()
            if not codigo.isdigit() or len(codigo) < 6:
                error_label.configure(text=_("export.pay_invalid"))
                return False
            if os.path.exists(used_codes_path):
                with open(used_codes_path, "r", encoding="utf-8") as f:
                    used = f.read()
                if codigo in used:
                    error_label.configure(text=_("export.pay_used"))
                    return False
            return True

        continuar_btn = ctk.CTkButton(frame, text=_("export.pay_verify"),
                                       fg_color="#1b5e20", hover_color="#2e7d32",
                                       font=("Segoe UI", 13, "bold"), height=38)

        def confirmar_pago():
            if not validar_codigo():
                return
            codigo = codigo_entry.get().strip()
            with open(used_codes_path, "a", encoding="utf-8") as f:
                f.write(f"{codigo} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            from controller.controllers import _reset_export_counter
            _reset_export_counter()
            self.export_btn.configure(state="normal")
            self.pay_block_frame.pack_forget()
            win.grab_release()
            win.destroy()

        continuar_btn.configure(command=confirmar_pago)
        continuar_btn.pack(pady=(10, 6))

        ctk.CTkLabel(frame, text=_("export.pay_thanks"),
                     font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(pady=(0, 8))
