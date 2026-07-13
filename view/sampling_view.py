import customtkinter as ctk
from model.i18n import _
from view.ui_components import (
    MetricCard,
    CARD_BG, CARD_BORDER, CONTENT_BG,
    ACCENT_PRIMARY, ACCENT_SECONDARY, ACCENT_PURPLE, ACCENT_WARNING,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
)


class SamplingView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.configure(fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text=_("sampling.title"),
                     font=("Segoe UI", 17, "bold"), text_color=ACCENT_PRIMARY).pack(pady=(14, 2))
        ctk.CTkLabel(header, text=_("sampling.subtitle"),
                     font=("Segoe UI", 11), text_color=TEXT_SECONDARY).pack(pady=(0, 12))

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        input_frame = ctk.CTkFrame(main, fg_color=CARD_BG, corner_radius=12)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(input_frame, text=_("sampling.params"),
                     font=("Segoe UI", 14, "bold"), text_color=ACCENT_PRIMARY).pack(anchor="w", padx=20, pady=(16, 10))

        fields = [
            (_("sampling.confidence"), "combo"),
            (_("sampling.probability"), "entry", "0.5"),
            (_("sampling.error"), "entry", "0.05"),
            (_("sampling.population"), "entry", ""),
        ]

        self.confidence_var = ctk.StringVar(value="95%")
        self.p_entry = None
        self.e_entry = None
        self.N_entry = None

        for f in fields:
            ctk.CTkLabel(input_frame, text=f[0], font=("Segoe UI", 11),
                         text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(8, 2))
            if f[1] == "combo":
                self.confidence_menu = ctk.CTkComboBox(input_frame, values=["90%", "95%", "99%"],
                                                        variable=self.confidence_var, state="readonly",
                                                        width=220, fg_color=CARD_BG,
                                                        border_color=CARD_BORDER,
                                                        button_color=ACCENT_PRIMARY)
                self.confidence_menu.pack(anchor="w", padx=20, pady=(0, 4))
            else:
                entry = ctk.CTkEntry(input_frame, placeholder_text=f[2] if len(f) > 2 else "",
                                      width=220, fg_color=CARD_BG, border_color=CARD_BORDER)
                entry.pack(anchor="w", padx=20, pady=(0, 4))
                if f[0].startswith("Probabilidad"):
                    self.p_entry = entry
                elif f[0].startswith("Error"):
                    self.e_entry = entry
                elif f[0].startswith("Tama\u00F1o"):
                    self.N_entry = entry

        self.calc_btn = ctk.CTkButton(input_frame, text=_("sampling.calc_btn"),
                                       command=self.calculate,
                                       font=("Segoe UI", 13, "bold"), height=40,
                                       fg_color=ACCENT_PRIMARY, hover_color="#1976d2",
                                       text_color="#ffffff")
        self.calc_btn.pack(pady=(18, 20), padx=20, fill="x")

        self.error_label = ctk.CTkLabel(input_frame, text="", font=("Segoe UI", 11),
                                         text_color=ACCENT_WARNING)
        self.error_label.pack(pady=(0, 10))

        results_frame = ctk.CTkFrame(main, fg_color=CARD_BG, corner_radius=12)
        results_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(results_frame, text=_("sampling.results"),
                     font=("Segoe UI", 14, "bold"), text_color=ACCENT_SECONDARY).pack(anchor="w", padx=20, pady=(16, 12))

        self.cards_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=14, pady=4)

        self.z_card = MetricCard(self.cards_frame, _("sampling.z_value"), "\u2014",
                                  gradient_from="#0d47a1", gradient_to="#1565c0")
        self.z_card.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.cards_frame.columnconfigure(0, weight=1)
        self.cards_frame.columnconfigure(1, weight=1)

        self.n_card = MetricCard(self.cards_frame, _("sampling.n_unknown"), "\u2014",
                                  gradient_from="#00695c", gradient_to="#00897b")
        self.n_card.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.n0_card = MetricCard(self.cards_frame, _("sampling.n0"), "\u2014",
                                   gradient_from="#4a148c", gradient_to="#6a1b9a")
        self.n0_card.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        self.nf_card = MetricCard(self.cards_frame, _("sampling.nf"), "\u2014",
                                   gradient_from="#e65100", gradient_to="#ef6c00")
        self.nf_card.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        info = ctk.CTkTextbox(results_frame, height=110, wrap="word",
                                font=("Segoe UI", 10), fg_color=CARD_BG,
                                border_width=1, border_color=CARD_BORDER,
                                text_color=TEXT_SECONDARY)
        info.pack(fill="x", padx=16, pady=(10, 16))
        info.insert("1.0",
                     "F\u00F3rmulas:\n"
                     "\u2022 n = (Z\u00B2\u00B7p\u00B7q) / e\u00B2        (poblaci\u00F3n desconocida)\n"
                     "\u2022 n\u2080 = (Z\u00B2\u00B7p\u00B7q) / e\u00B2   \u2192   nf = n\u2080 / (1 + n\u2080/N)")
        info.configure(state="disabled")

    def calculate(self):
        self.error_label.configure(text="")
        try:
            conf_str = self.confidence_var.get().replace("%", "")
            confidence = int(conf_str)

            p_text = self.p_entry.get().strip() if self.p_entry else ""
            if not p_text:
                raise ValueError("Ingrese la probabilidad de \u00E9xito (p).")
            p = float(p_text)

            e_text = self.e_entry.get().strip() if self.e_entry else ""
            if not e_text:
                raise ValueError("Ingrese el error admisible (e).")
            e = float(e_text)

            N = None
            N_text = self.N_entry.get().strip() if self.N_entry else ""
            if N_text:
                N = int(N_text)

            result = self.controller.calculate(confidence, p, e, N)
            if not result["success"]:
                self.error_label.configure(text=result["error"])
                return

            data = result["data"]
            self.z_card.update_value(f"{data['Z']:.3f}")
            self.n_card.update_value(str(data["n_unknown"]))

            if data["N"] is not None and data["nf"] is not None:
                self.n0_card.update_value(str(data["n0"]))
                self.nf_card.update_value(str(data["nf"]))
            else:
                self.n0_card.update_value("\u2014")
                self.nf_card.update_value("\u2014")

        except ValueError as e:
            self.error_label.configure(text=str(e))
        except Exception as e:
            self.error_label.configure(text=f"Error: {str(e)}")
