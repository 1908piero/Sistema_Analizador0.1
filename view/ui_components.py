import customtkinter as ctk
from tkinter import ttk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SIDEBAR_BG = "#0b0e14"
CONTENT_BG = "#0b0e14"
CARD_BG = "#161b22"
CARD_BORDER = "#1e2030"
ACCENT_PRIMARY = "#6366f1"
ACCENT_SECONDARY = "#10b981"
ACCENT_WARNING = "#f59e0b"
ACCENT_PURPLE = "#a855f7"
TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
SUCCESS_GREEN = "#10b981"
ERROR_RED = "#ef4444"


class TableWidget(ctk.CTkFrame):
    def __init__(self, master, columns: list, rows: list = None, title: str = "", **kwargs):
        super().__init__(master, **kwargs)
        self.columns = columns
        self.rows = rows or []
        self.title = title

        if self.title:
            label_frame = ctk.CTkFrame(self, fg_color="transparent")
            label_frame.pack(fill="x", pady=(6, 2))
            ctk.CTkLabel(label_frame, text=self.title,
                         font=("Segoe UI", 12, "bold"), text_color=ACCENT_PRIMARY).pack(anchor="w")

        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=4, pady=4)

        tree_frame = ctk.CTkFrame(self.frame, fg_color=CARD_BG, corner_radius=8)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings",
                                 height=min(len(self.rows) + 1, 12))
        self.tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor="center", minwidth=70)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self._style_tree()
        self.populate(self.rows)

    def _style_tree(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=CARD_BG,
                        foreground=TEXT_PRIMARY,
                        fieldbackground=CARD_BG,
                        font=("Segoe UI", 10),
                        rowheight=28)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=CARD_BORDER,
                        foreground=ACCENT_PRIMARY,
                        borderwidth=0)
        style.map("Treeview",
                  background=[("selected", "#1e3a5f")],
                  foreground=[("selected", "#ffffff")])

    def populate(self, rows: list):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            row_str = [str(v) if not isinstance(v, str) else v for v in row]
            self.tree.insert("", "end", values=row_str)


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, subtitle: str = "",
                 gradient_from: str = "#1a237e", gradient_to: str = "#283593", **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.configure(fg_color=gradient_from)

        inner = ctk.CTkFrame(self, fg_color=gradient_to, corner_radius=0)
        inner.place(relx=0, rely=0, relwidth=1, relheight=0.35)

        self.title_label = ctk.CTkLabel(self, text=title.upper(),
                                         font=("Segoe UI", 9, "bold"),
                                         text_color=TEXT_SECONDARY, anchor="w")
        self.title_label.place(relx=0.08, rely=0.42)

        self.value_label = ctk.CTkLabel(self, text=str(value),
                                         font=("Segoe UI", 22, "bold"),
                                         text_color="#ffffff", anchor="w")
        self.value_label.place(relx=0.08, rely=0.58)

        if subtitle:
            self.sub_label = ctk.CTkLabel(self, text=subtitle,
                                           font=("Segoe UI", 8),
                                           text_color=TEXT_SECONDARY, anchor="w")
            self.sub_label.place(relx=0.08, rely=0.82)

    def update_value(self, value: str):
        self.value_label.configure(text=str(value))


class ScrollableResultsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def add_section_title(self, text: str):
        frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        frame.pack(fill="x", pady=(8, 4), padx=4)
        label = ctk.CTkLabel(frame, text=text, font=("Segoe UI", 15, "bold"),
                              text_color=ACCENT_PRIMARY, anchor="w")
        label.pack(fill="x", padx=14, pady=10)
        return label

    def add_subtitle(self, text: str):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=(8, 2), padx=8)
        label = ctk.CTkLabel(frame, text=text, font=("Segoe UI", 12, "bold"),
                              text_color=ACCENT_SECONDARY, anchor="w")
        label.pack(fill="x")
        return label

    def add_text(self, text: str):
        label = ctk.CTkLabel(self, text=text, font=("Segoe UI", 11),
                              anchor="w", justify="left", wraplength=680,
                              text_color=TEXT_SECONDARY)
        label.pack(fill="x", pady=2, padx=12)
        return label

    def add_table(self, columns: list, rows: list, title: str = ""):
        table = TableWidget(self, columns=columns, rows=rows, title=title,
                            fg_color="transparent")
        table.pack(fill="x", padx=8, pady=6)
        return table

    def add_chart(self, chart_bytes, width: int = 540, height: int = 320):
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(chart_bytes.read()))
        chart_bytes.seek(0)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))
        frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        frame.pack(fill="x", pady=8, padx=8)
        label = ctk.CTkLabel(frame, image=ctk_img, text="")
        label.pack(pady=10)
        return label

    def add_separator(self):
        sep = ctk.CTkFrame(self, height=2, fg_color=CARD_BORDER)
        sep.pack(fill="x", pady=10, padx=30)

    def add_metrics_row(self, metrics: list):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=8, pady=4)
        for i, m in enumerate(metrics):
            frame.columnconfigure(i, weight=1)
            card = MetricCard(frame, **m)
            card.grid(row=0, column=i, sticky="ew", padx=4, pady=4)
