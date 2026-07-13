import customtkinter as ctk
from view.ui_components import (
    CARD_BG, CARD_BORDER, CONTENT_BG,
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
)


class TutorialOverlay(ctk.CTkToplevel):
    def __init__(self, master, steps, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.steps = steps
        self.current_step = 0

        top = master.winfo_toplevel()
        self.transient(top)
        self.geometry(f"{top.winfo_width()}x{top.winfo_height()}+{top.winfo_x()}+{top.winfo_y()}")
        self.attributes("-alpha", 0.85)
        self.attributes("-topmost", True)
        self.configure(fg_color="#000000")
        self.overrideredirect(True)

        self.card_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16,
                                        border_width=2, border_color=ACCENT_PRIMARY)
        self.card_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.step_label = ctk.CTkLabel(self.card_frame, text="",
                                        font=("Segoe UI", 10), text_color=TEXT_MUTED)
        self.step_label.pack(anchor="w", padx=20, pady=(14, 2))

        self.title_label = ctk.CTkLabel(self.card_frame, text="",
                                         font=("Segoe UI", 16, "bold"), text_color=ACCENT_PRIMARY)
        self.title_label.pack(anchor="w", padx=20, pady=(0, 4))

        self.desc_label = ctk.CTkLabel(self.card_frame, text="",
                                        font=("Segoe UI", 12), text_color=TEXT_PRIMARY,
                                        wraplength=480, justify="left")
        self.desc_label.pack(anchor="w", padx=20, pady=(0, 12))

        btn_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 14))

        self.prev_btn = ctk.CTkButton(btn_frame, text="Anterior",
                                        font=("Segoe UI", 11, "bold"), height=32,
                                        fg_color="#455a64", hover_color="#546e7a",
                                        corner_radius=8, command=self._prev)
        self.prev_btn.pack(side="left")

        self.close_btn = ctk.CTkButton(btn_frame, text="Cerrar",
                                         font=("Segoe UI", 11, "bold"), height=32,
                                         fg_color="#bf360c", hover_color="#d84315",
                                         corner_radius=8, command=self._close)
        self.close_btn.pack(side="left", padx=8)

        self.next_btn = ctk.CTkButton(btn_frame, text="Siguiente",
                                        font=("Segoe UI", 11, "bold"), height=32,
                                        fg_color=ACCENT_PRIMARY, hover_color="#1976d2",
                                        corner_radius=8, command=self._next)
        self.next_btn.pack(side="right")

        self._show_step(0)

    def _show_step(self, idx):
        if idx < 0 or idx >= len(self.steps):
            return
        step = self.steps[idx]
        self.current_step = idx
        self.step_label.configure(text=f"Paso {idx + 1} de {len(self.steps)}")
        self.title_label.configure(text=step.get("title", ""))
        self.desc_label.configure(text=step.get("text", ""))
        self.prev_btn.configure(state="normal" if idx > 0 else "disabled")
        self.next_btn.configure(text="Finalizar" if idx == len(self.steps) - 1 else "Siguiente")
        self._highlight_widget(step.get("widget"))

    def _highlight_widget(self, widget):
        pass

    def _next(self):
        if self.current_step < len(self.steps) - 1:
            self._show_step(self.current_step + 1)
        else:
            self._close()

    def _prev(self):
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _close(self):
        self.grab_release()
        self.destroy()
