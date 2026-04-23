"""
SISTEMA DE FIADO — LIZBETH
Interfaz gráfica intuitiva para registrar ventas al crédito por voz o texto.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from config import EXCEL_PATH, DATE_FORMAT
from audio_capture import grabar_audio
from transcriber import transcribir_audio
from entity_extractor import extraer_datos
from excel_manager import (
    registrar_venta,
    corregir_monto,
    borrar_entrada,
    resumen_dia,
    resumen_semanal,
    _ensure_workbook,
)

# ── Colores ──────────────────────────────────────────────
BG           = "#1e1e2e"      # Fondo principal
BG_CARD      = "#2a2a3d"      # Fondo de tarjetas
ACCENT       = "#7c3aed"      # Violeta principal
ACCENT_HOVER = "#9333ea"      # Violeta hover
RED          = "#ef4444"
RED_HOVER    = "#dc2626"
GREEN        = "#22c55e"
YELLOW       = "#eab308"
TEXT_PRIMARY = "#f1f5f9"      # Texto claro
TEXT_MUTED   = "#94a3b8"      # Texto secundario
BORDER       = "#3b3b54"
REC_COLOR    = "#ef4444"      # Rojo de grabación
REC_ACTIVE   = "#b91c1c"


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Fiado — Lizbeth")
        self.geometry("720x780")
        self.configure(bg=BG)
        self.resizable(False, False)

        # Centrar ventana
        self.update_idletasks()
        w, h = 720, 780
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._recording = False
        _ensure_workbook()

        self._build_header()
        self._build_voice_section()
        self._build_manual_section()
        self._build_status_bar()
        self._build_table_section()
        self._build_action_buttons()

        self._refresh_table()

    # ── Header ───────────────────────────────────────────
    def _build_header(self):
        frame = tk.Frame(self, bg=ACCENT, pady=14)
        frame.pack(fill="x")

        tk.Label(
            frame, text="🍽️  SISTEMA DE FIADO — LIZBETH",
            bg=ACCENT, fg="white", font=("Segoe UI", 16, "bold"),
        ).pack()

        today = datetime.now().strftime("%A %d/%m/%Y").capitalize()
        tk.Label(
            frame, text=f"📅  {today}",
            bg=ACCENT, fg="#e0d4f7", font=("Segoe UI", 11),
        ).pack()

    # ── Sección de voz ───────────────────────────────────
    def _build_voice_section(self):
        frame = tk.Frame(self, bg=BG, pady=12)
        frame.pack(fill="x", padx=24)

        self.btn_voice = tk.Button(
            frame,
            text="🎙️  DICTAR VENTA",
            font=("Segoe UI", 15, "bold"),
            bg=REC_COLOR, fg="white",
            activebackground=REC_ACTIVE, activeforeground="white",
            relief="flat", cursor="hand2",
            padx=20, pady=14,
            command=self._on_voice_click,
        )
        self.btn_voice.pack(fill="x")

    # ── Entrada manual ───────────────────────────────────
    def _build_manual_section(self):
        frame = tk.Frame(self, bg=BG, pady=4)
        frame.pack(fill="x", padx=24)

        tk.Label(
            frame, text="O escribe aquí  (ej: Carlos 3.50)",
            bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 9),
        ).pack(anchor="w")

        row = tk.Frame(frame, bg=BG)
        row.pack(fill="x", pady=(4, 0))

        self.entry_manual = tk.Entry(
            row, font=("Segoe UI", 13),
            bg=BG_CARD, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat", bd=0,
        )
        self.entry_manual.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry_manual.bind("<Return>", lambda e: self._on_manual_submit())

        self.btn_manual = tk.Button(
            row, text="Registrar",
            font=("Segoe UI", 11, "bold"),
            bg=GREEN, fg="white",
            activebackground="#16a34a", activeforeground="white",
            relief="flat", cursor="hand2",
            padx=16, pady=6,
            command=self._on_manual_submit,
        )
        self.btn_manual.pack(side="right")

    # ── Barra de estado ──────────────────────────────────
    def _build_status_bar(self):
        frame = tk.Frame(self, bg=BG, pady=6)
        frame.pack(fill="x", padx=24)

        self.lbl_status = tk.Label(
            frame, text="Listo. Dicta o escribe una venta.",
            bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 10),
            anchor="w",
        )
        self.lbl_status.pack(fill="x")

    # ── Tabla de registros ───────────────────────────────
    def _build_table_section(self):
        frame = tk.Frame(self, bg=BG, pady=4)
        frame.pack(fill="both", expand=True, padx=24)

        # Título + pestañas
        header_row = tk.Frame(frame, bg=BG)
        header_row.pack(fill="x", pady=(0, 6))

        self.lbl_table_title = tk.Label(
            header_row, text="📋  REGISTRO DEL DÍA",
            bg=BG, fg=TEXT_PRIMARY, font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self.lbl_table_title.pack(side="left")

        self._view_mode = "dia"  # "dia" o "semanal"

        self.btn_toggle = tk.Button(
            header_row, text="📊 Ver Semanal",
            font=("Segoe UI", 9),
            bg=BG_CARD, fg=TEXT_MUTED,
            activebackground=BORDER, activeforeground=TEXT_PRIMARY,
            relief="flat", cursor="hand2",
            padx=10, pady=2,
            command=self._toggle_view,
        )
        self.btn_toggle.pack(side="right")

        # Tabla
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
            background=BG_CARD,
            foreground=TEXT_PRIMARY,
            fieldbackground=BG_CARD,
            font=("Segoe UI", 11),
            rowheight=32,
        )
        style.configure("Custom.Treeview.Heading",
            background=ACCENT,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Custom.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")],
        )

        columns = ("nombre", "diario", "semanal")
        self.tree = ttk.Treeview(
            frame, columns=columns, show="headings",
            style="Custom.Treeview", height=10,
        )
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("diario", text="Total Diario (S/)")
        self.tree.heading("semanal", text="Total Semanal (S/)")
        self.tree.column("nombre", width=240, anchor="w")
        self.tree.column("diario", width=160, anchor="center")
        self.tree.column("semanal", width=180, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Total
        self.lbl_total = tk.Label(
            frame, text="Total del día: S/ 0.00",
            bg=BG, fg=YELLOW, font=("Segoe UI", 12, "bold"),
            anchor="e",
        )
        self.lbl_total.pack(fill="x", pady=(6, 0))

    # ── Botones de acción ────────────────────────────────
    def _build_action_buttons(self):
        frame = tk.Frame(self, bg=BG, pady=12)
        frame.pack(fill="x", padx=24)

        btn_style = dict(
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            padx=14, pady=8,
        )

        self.btn_corregir = tk.Button(
            frame, text="✏️ Corregir", bg="#3b82f6", fg="white",
            activebackground="#2563eb", activeforeground="white",
            command=self._on_corregir, **btn_style,
        )
        self.btn_corregir.pack(side="left", padx=(0, 8))

        self.btn_borrar = tk.Button(
            frame, text="🗑️ Borrar", bg=RED, fg="white",
            activebackground=RED_HOVER, activeforeground="white",
            command=self._on_borrar, **btn_style,
        )
        self.btn_borrar.pack(side="left", padx=(0, 8))

        self.btn_refresh = tk.Button(
            frame, text="🔄 Actualizar", bg=BG_CARD, fg=TEXT_MUTED,
            activebackground=BORDER, activeforeground=TEXT_PRIMARY,
            command=self._refresh_table, **btn_style,
        )
        self.btn_refresh.pack(side="right")

    # ── Lógica: Voz ──────────────────────────────────────
    def _on_voice_click(self):
        if self._recording:
            return
        self._recording = True
        self.btn_voice.config(text="🔴  GRABANDO... habla ahora", bg=REC_ACTIVE)
        self._set_status("Grabando audio...", YELLOW)
        threading.Thread(target=self._voice_worker, daemon=True).start()

    def _voice_worker(self):
        try:
            ruta = grabar_audio()
            if ruta is None:
                self.after(0, lambda: self._voice_done(None, "No se detectó voz. Intenta de nuevo."))
                return

            self.after(0, lambda: self._set_status("Transcribiendo audio...", YELLOW))
            texto = transcribir_audio(ruta)
            if texto is None:
                self.after(0, lambda: self._voice_done(None, "No se pudo transcribir. Intenta de nuevo."))
                return

            nombre, monto = extraer_datos(texto)
            self.after(0, lambda: self._voice_result(texto, nombre, monto))

        except Exception as e:
            self.after(0, lambda: self._voice_done(None, f"Error: {e}"))

    def _voice_result(self, texto, nombre, monto):
        self._recording = False
        self.btn_voice.config(text="🎙️  DICTAR VENTA", bg=REC_COLOR)

        if nombre is None and monto is None:
            self._set_status(f'Escuché: "{texto}" — no pude extraer datos.', RED)
            return

        if nombre is None:
            nombre = simpledialog.askstring(
                "Nombre faltante",
                f"Escuché un monto de S/ {monto:.2f}\n¿Para quién es?",
                parent=self,
            )
            if not nombre:
                self._set_status("Cancelado.", TEXT_MUTED)
                return

        if monto is None:
            monto_str = simpledialog.askstring(
                "Monto faltante",
                f"Escuché el nombre '{nombre}'\n¿Cuánto fue? (ej: 3.50)",
                parent=self,
            )
            if not monto_str:
                self._set_status("Cancelado.", TEXT_MUTED)
                return
            try:
                monto = float(monto_str.replace(",", "."))
            except ValueError:
                self._set_status("Monto inválido. Cancelado.", RED)
                return

        # Confirmar
        ok = messagebox.askyesno(
            "Confirmar venta",
            f"¿Registrar?\n\n  Nombre:  {nombre}\n  Monto:   S/ {monto:.2f}",
        )
        if not ok:
            self._set_status("Descartado.", TEXT_MUTED)
            return

        self._do_register(nombre, monto, f'(voz: "{texto}")')

    def _voice_done(self, _result, msg):
        self._recording = False
        self.btn_voice.config(text="🎙️  DICTAR VENTA", bg=REC_COLOR)
        self._set_status(msg, RED if "Error" in msg or "No se" in msg else TEXT_MUTED)

    # ── Lógica: Manual ───────────────────────────────────
    def _on_manual_submit(self):
        texto = self.entry_manual.get().strip()
        if not texto:
            return

        nombre, monto = extraer_datos(texto)

        if nombre is None and monto is None:
            self._set_status("No pude entender. Usa: Nombre Monto (ej: Carlos 3.50)", RED)
            return

        if nombre is None:
            nombre = simpledialog.askstring(
                "Nombre faltante",
                f"Detecté S/ {monto:.2f}\n¿Para quién es?",
                parent=self,
            )
            if not nombre:
                return

        if monto is None:
            monto_str = simpledialog.askstring(
                "Monto faltante",
                f"Detecté '{nombre}'\n¿Cuánto fue?",
                parent=self,
            )
            if not monto_str:
                return
            try:
                monto = float(monto_str.replace(",", "."))
            except ValueError:
                self._set_status("Monto inválido.", RED)
                return

        self._do_register(nombre, monto, "(manual)")
        self.entry_manual.delete(0, "end")

    # ── Registrar venta ──────────────────────────────────
    def _do_register(self, nombre, monto, via=""):
        resultado = registrar_venta(nombre, monto)
        accion = resultado["accion"]

        if accion == "INSERT":
            msg = f"✅  {resultado['nombre']} registrado: S/ {monto:.2f}"
        else:
            msg = (
                f"✅  {resultado['nombre']} actualizado: "
                f"S/ {resultado['monto_anterior']:.2f} → S/ {resultado['nuevo_total']:.2f}"
            )

        self._set_status(msg, GREEN)
        self._refresh_table()

    # ── Corregir ─────────────────────────────────────────
    def _on_corregir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Corregir", "Selecciona un nombre de la tabla primero.")
            return

        values = self.tree.item(sel[0])["values"]
        nombre = values[0]

        nuevo_str = simpledialog.askstring(
            "Corregir monto",
            f"Monto actual de {nombre}: S/ {values[1]}\n\nNuevo monto:",
            parent=self,
        )
        if not nuevo_str:
            return
        try:
            nuevo = float(nuevo_str.replace(",", "."))
        except ValueError:
            self._set_status("Monto inválido.", RED)
            return

        resultado = corregir_monto(nombre, nuevo)
        if "error" in resultado:
            self._set_status(f"❌  {resultado['error']}", RED)
        else:
            self._set_status(
                f"✅  {nombre} corregido: S/ {resultado['monto_anterior']:.2f} → S/ {resultado['nuevo_monto']:.2f}",
                GREEN,
            )
        self._refresh_table()

    # ── Borrar ───────────────────────────────────────────
    def _on_borrar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Borrar", "Selecciona un nombre de la tabla primero.")
            return

        values = self.tree.item(sel[0])["values"]
        nombre = values[0]

        ok = messagebox.askyesno(
            "Confirmar borrar",
            f"¿Eliminar a {nombre} del registro de hoy?\n(S/ {values[1]})",
        )
        if not ok:
            return

        resultado = borrar_entrada(nombre)
        if "error" in resultado:
            self._set_status(f"❌  {resultado['error']}", RED)
        else:
            self._set_status(f"🗑️  {nombre} eliminado.", GREEN)
        self._refresh_table()

    # ── Toggle vista día/semanal ─────────────────────────
    def _toggle_view(self):
        if self._view_mode == "dia":
            self._view_mode = "semanal"
            self.btn_toggle.config(text="📋 Ver Día")
            self.lbl_table_title.config(text="📊  RESUMEN SEMANAL")
        else:
            self._view_mode = "dia"
            self.btn_toggle.config(text="📊 Ver Semanal")
            self.lbl_table_title.config(text="📋  REGISTRO DEL DÍA")
        self._refresh_table()

    # ── Refrescar tabla ──────────────────────────────────
    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self._view_mode == "dia":
            registros = resumen_dia()
            total = 0.0
            for r in registros:
                diario = r["total_diario"]
                semanal = r["total_semanal"]
                self.tree.insert("", "end", values=(
                    r["nombre"],
                    f"{diario:.2f}",
                    f"{semanal:.2f}",
                ))
                total += diario
            self.lbl_total.config(text=f"Total del día: S/ {total:.2f}")
        else:
            registros = resumen_semanal()
            total = 0.0
            for r in registros:
                semanal = r["total_semanal"]
                self.tree.insert("", "end", values=(
                    r["nombre"],
                    "—",
                    f"{semanal:.2f}",
                ))
                total += semanal
            self.lbl_total.config(text=f"Total semanal: S/ {total:.2f}")

    # ── Utilidad ─────────────────────────────────────────
    def _set_status(self, text, color=TEXT_MUTED):
        self.lbl_status.config(text=text, fg=color)


if __name__ == "__main__":
    app = App()
    app.mainloop()
