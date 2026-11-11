# -*- coding: utf-8 -*-
# =====================================================================
#  TeleCauca - App de Telemedicina
#  Hospital Universitario San Jose (Popayan) - area de Telemedicina
#  Autora: Maria Alejandra Lopez
#
#  Que hace la app:
#   1) Lee la base de citas del hospital.
#   2) Identifica que pacientes son APTOS para telemedicina y cuales
#      deben ir a consulta PRESENCIAL (el modelo sugiere, el medico decide).
#   3) Calcula cuanto se AHORRAN los pacientes en kilometros, horas y dinero
#      al atenderse por telemedicina (sin viajar a Popayan).
#
#  Es una ventana (no hay que tocar codigo): se abre, se carga el archivo
#  de citas y se ven los resultados.
# =====================================================================

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

# ---------------------------------------------------------------------
#  COLORES Y ESTILO (la identidad visual de la app)
# ---------------------------------------------------------------------
AZUL     = "#1B3A6B"   # azul profundo (confianza, salud)
VERDE    = "#2A9D8F"   # verde-azulado (telemedicina)
NARANJA  = "#F4A259"   # naranja suave (acento, ahorro)
ROJO     = "#E76F51"   # para "presencial"
FONDO    = "#F4F6F8"   # fondo claro de las pantallas
BLANCO   = "#FFFFFF"
GRIS_TXT = "#5B6B7A"

# ---------------------------------------------------------------------
#  PARAMETROS DEL CALCULO (se pueden ajustar facilmente)
#  El dinero ahorrado por cada paciente que evita el viaje es la suma de:
#  transporte intermunicipal + transporte urbano en Popayan + almuerzo
#  + hotel (solo si el municipio es muy lejano y debe quedarse a dormir).
# ---------------------------------------------------------------------
COSTO_KM   = 250     # pesos por km (transporte intermunicipal, ida y vuelta)
VELOCIDAD  = 40      # km por hora (promedio carreteras del Cauca)
URBANO     = 12000   # transporte urbano en Popayan (terminal-hospital, ida y vuelta)
ALMUERZO   = 15000   # almuerzo fuera de casa el dia de la cita
HOTEL      = 70000   # hospedaje una noche (solo municipios muy lejanos)
KM_HOTEL   = 100     # si el municipio esta a mas de estos km (una via), se asume
                     # que el paciente debe quedarse a dormir (hotel)

# Palabras en la ACTIVIDAD que exigen presencia (examenes, procedimientos...)
NO_APTAS = ["TERAPIA", "ELECTRO", "RADIOLOG", "RX", "TAC", "RESONANC",
            "ECOCARDIO", "HOLTER", "PROCEDIMIENTO", "IMAGEN",
            "ADMINISTRACION DE MEDICAMENTOS", "ECOGRAF", "CANGURO"]

# Palabras en la ESPECIALIDAD que SIEMPRE exigen presencia, sin importar la
# actividad (terapias, imagenes, laboratorio, procedimientos invasivos...).
NO_APTAS_ESP = ["TERAPIA", "REHABILITAC", "MEDICINA FISICA", "RADIOLOG",
                "IMAGEN", "HEMODINAM", "ELECTROESTIMULA", "ELECTROFISIOLOG",
                "LABORATORIO", "PATOLOGIA", "ENDOSCOP", "ECOGRAF"]


def es_apta(actividad, especialidad=""):
    """Decide si una cita se puede atender por telemedicina.
    Mira primero la especialidad y luego el tipo de actividad."""
    esp = str(especialidad).upper()
    for palabra in NO_APTAS_ESP:
        if palabra in esp:
            return "Necesita ir en persona"
    texto = str(actividad).upper()
    for palabra in NO_APTAS:
        if palabra in texto:
            return "Necesita ir en persona"
    return "Apta para telemedicina"


class AppTelemedicina(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TelemedicinaCauca - Hospital Universitario San Jose")
        self.configure(bg=FONDO)
        self.geometry("920x640")
        self.minsize(820, 600)

        self.citas = None          # aqui guardamos los datos cargados
        self.resultado = None      # aqui guardamos el resumen calculado
        self.aptas_df = None       # citas aptas en detalle (para la ventana por municipio)
        self.citas_full = None     # todas las citas clasificadas (para el detalle)

        self._configurar_estilo()  # deja las tablas mas ordenadas y bonitas

        self._construir_encabezado()
        self._construir_barra_acciones()
        self._construir_paneles()   # 3 pestañas: Inicio, Clasificacion y Ahorro
        self._construir_pie()

        # Al abrir, intenta cargar automaticamente el archivo de la carpeta
        self._cargar_automatico()

    # -----------------------------------------------------------------
    #  ESTILO DE LAS TABLAS (para que se vean ordenadas, como Power BI)
    # -----------------------------------------------------------------
    def _configurar_estilo(self):
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")   # tema que si deja poner colores
        except Exception:
            pass
        estilo.configure("Treeview", rowheight=28, font=("Helvetica", 11),
                         background=BLANCO, fieldbackground=BLANCO, borderwidth=0)
        estilo.configure("Treeview.Heading", font=("Helvetica", 11, "bold"),
                         background=AZUL, foreground=BLANCO, relief="flat", padding=6)
        estilo.map("Treeview.Heading", background=[("active", AZUL)])
        estilo.map("Treeview", background=[("selected", VERDE)],
                   foreground=[("selected", BLANCO)])

    def _limpiar_actividad(self, texto):
        """Deja el tipo de cita mas corto y legible."""
        t = str(texto).title()
        t = t.replace("Actividad De ", "").replace("Actividad ", "")
        return t.strip()

    # -----------------------------------------------------------------
    #  ENCABEZADO (logo + titulo)
    # -----------------------------------------------------------------
    def _construir_encabezado(self):
        cabe = tk.Frame(self, bg=AZUL, height=84)
        cabe.pack(fill="x")
        cabe.pack_propagate(False)

        # Logo (si esta el archivo logo_telecauca.png al lado de la app)
        self.logo_img = None
        ruta_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "logo_telecauca.png")
        if os.path.exists(ruta_logo):
            try:
                # Mejor opcion: usar Pillow (PIL) para achicar el logo SUAVE,
                # asi se ve nitido y no pixelado. (Pillow viene con matplotlib.)
                try:
                    from PIL import Image, ImageTk
                    pil = Image.open(ruta_logo).convert("RGBA")
                    pil = pil.resize((72, 72), Image.LANCZOS)
                    self.logo_img = ImageTk.PhotoImage(pil)
                except Exception:
                    # Plan B (sin Pillow): achicar a la mitad exacta (mas limpio)
                    img = tk.PhotoImage(file=ruta_logo)
                    factor = max(1, round(img.height() / 72))
                    self.logo_img = img.subsample(factor, factor)
                tk.Label(cabe, image=self.logo_img, bg=AZUL).pack(
                    side="left", padx=(16, 12), pady=8)
            except Exception:
                self.logo_img = None

        textos = tk.Frame(cabe, bg=AZUL)
        textos.pack(side="left", pady=16)
        tk.Label(textos, text="TelemedicinaCauca", bg=AZUL, fg=BLANCO,
                 font=("Helvetica", 20, "bold")).pack(anchor="w")
        tk.Label(textos, text="Hospital Universitario San Jose  -  Telemedicina",
                 bg=AZUL, fg="#C7D6EA", font=("Helvetica", 11)).pack(anchor="w")

    # -----------------------------------------------------------------
    #  BARRA DE ACCIONES (botones)
    # -----------------------------------------------------------------
    def _construir_barra_acciones(self):
        barra = tk.Frame(self, bg=FONDO)
        barra.pack(fill="x", padx=16, pady=(14, 6))

        self._boton(barra, "📂   Cargar archivo de citas", VERDE,
                    self._cargar_archivo).pack(side="left")
        self._boton(barra, "⬇   Exportar resultados a Excel", AZUL,
                    self._exportar_excel).pack(side="left", padx=10)

        self.lbl_archivo = tk.Label(barra, text="", bg=FONDO, fg=GRIS_TXT,
                                    font=("Helvetica", 10))
        self.lbl_archivo.pack(side="left", padx=10)

    def _oscurecer(self, hexcolor, factor=0.85):
        """Devuelve el color un poco mas oscuro (para el efecto al pasar el mouse)."""
        hexcolor = hexcolor.lstrip("#")
        r, g, b = (int(hexcolor[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = (int(c * factor) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _boton(self, padre, texto, color, comando):
        """Boton 'de verdad' hecho con un Label, porque en Mac los botones
        normales de Tkinter no dejan ponerles color de fondo."""
        b = tk.Label(padre, text=texto, bg=color, fg=BLANCO,
                     font=("Helvetica", 11, "bold"),
                     padx=18, pady=10, cursor="hand2")
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>", lambda e: b.config(bg=self._oscurecer(color)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    # -----------------------------------------------------------------
    #  TARJETAS DE RESULTADOS (los numeros grandes)
    # -----------------------------------------------------------------
    def _construir_tarjetas(self, parent):
        cont = tk.Frame(parent, bg=FONDO)
        cont.pack(fill="x", padx=10, pady=(16, 8))

        self.tarjetas = {}
        datos = [
            ("aptas",     "Aptas para telemedicina", VERDE),
            ("presencial","Deben ir en persona",     ROJO),
            ("km",        "Kilometros ahorrados",    AZUL),
            ("dinero",    "Dinero ahorrado",         NARANJA),
        ]
        for clave, titulo, color in datos:
            tarjeta = tk.Frame(cont, bg=BLANCO, highlightbackground="#E4E9EE",
                               highlightthickness=1)
            tarjeta.pack(side="left", expand=True, fill="both", padx=6)
            tk.Frame(tarjeta, bg=color, height=5).pack(fill="x")
            valor = tk.Label(tarjeta, text="-", bg=BLANCO, fg=color,
                             font=("Helvetica", 24, "bold"))
            valor.pack(pady=(16, 2), padx=10)
            tk.Label(tarjeta, text=titulo, bg=BLANCO, fg=GRIS_TXT,
                     font=("Helvetica", 11), wraplength=160).pack(
                         pady=(0, 16), padx=10)
            self.tarjetas[clave] = valor

    # -----------------------------------------------------------------
    #  PANELES: dos pestañas (1. Clasificacion de citas  2. Ahorro)
    # -----------------------------------------------------------------
    def _construir_paneles(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(8, 4))

        # --- Pestaña 0: MENU PRINCIPAL (resumen de todo) ---
        tab0 = tk.Frame(self.notebook, bg=FONDO)
        self.notebook.add(tab0, text="  🏠 Menu principal  ")
        tk.Label(tab0, text="Resumen general", bg=FONDO, fg=AZUL,
                 font=("Helvetica", 15, "bold")).pack(anchor="w", padx=14, pady=(14, 0))
        self._construir_tarjetas(tab0)   # las tarjetas grandes van aqui
        self.lbl_resumen = tk.Label(
            tab0, text="Carga un archivo de citas para ver el resumen.",
            bg=FONDO, fg=GRIS_TXT, font=("Helvetica", 12), justify="left",
            wraplength=840)
        self.lbl_resumen.pack(anchor="w", padx=16, pady=(6, 10))
        tk.Label(tab0,
                 text="➡  Mira la pestana '1. Clasificacion' para ver cada cita "
                      "(apta o presencial),\n"
                      "     y '2. Ahorro por municipio' para ver donde se beneficia "
                      "mas la gente.",
                 bg=FONDO, fg=GRIS_TXT, font=("Helvetica", 11),
                 justify="left").pack(anchor="w", padx=16, pady=(0, 10))

        # --- Pestaña 1: CLASIFICACION (apta / no apta) ---
        tab1 = tk.Frame(self.notebook, bg=FONDO)
        self.notebook.add(tab1, text="  1. Clasificacion de citas  ")
        tk.Label(tab1, text="💡 Esta pestana funciona con cualquier archivo que tenga la columna 'actividad'.",
                 bg=FONDO, fg=GRIS_TXT, font=("Helvetica", 10)).pack(
                     anchor="w", padx=4, pady=(8, 4))

        cols1 = ("cod", "especialidad", "actividad", "tele")
        self.tabla_clasif = ttk.Treeview(tab1, columns=cols1, show="headings")
        enc1 = {"cod": "Cod. paciente", "especialidad": "Especialidad",
                "actividad": "Tipo de cita", "tele": "Telemedicina"}
        anchos1 = {"cod": 110, "especialidad": 200, "actividad": 260, "tele": 170}
        for c in cols1:
            self.tabla_clasif.heading(c, text=enc1[c])
            self.tabla_clasif.column(
                c, width=anchos1[c],
                anchor="w" if c in ("especialidad", "actividad", "tele") else "center")
        barra1 = ttk.Scrollbar(tab1, orient="vertical",
                               command=self.tabla_clasif.yview)
        self.tabla_clasif.configure(yscrollcommand=barra1.set)
        self.tabla_clasif.pack(side="left", fill="both", expand=True, padx=(4, 0))
        barra1.pack(side="right", fill="y")
        self.tabla_clasif.tag_configure("par", background="#FFFFFF")
        self.tabla_clasif.tag_configure("impar", background="#EEF3F7")

        # --- Pestaña 2: AHORRO POR MUNICIPIO ---
        tab2 = tk.Frame(self.notebook, bg=FONDO)
        self.notebook.add(tab2, text="  2. Ahorro por municipio  ")
        self.aviso_muni = tk.Label(
            tab2, text="💡 Doble clic en un municipio para ver sus pacientes y citas",
            bg=FONDO, fg=GRIS_TXT, font=("Helvetica", 10))
        self.aviso_muni.pack(anchor="w", padx=4, pady=(8, 4))

        cols = ("municipio", "citas", "km", "horas", "dinero")
        self.tabla = ttk.Treeview(tab2, columns=cols, show="headings")
        encabezados = {
            "municipio": "Municipio", "citas": "Citas aptas",
            "km": "Km evitados", "horas": "Horas", "dinero": "Dinero ahorrado"}
        anchos = {"municipio": 220, "citas": 90, "km": 110, "horas": 90, "dinero": 150}
        for c in cols:
            self.tabla.heading(c, text=encabezados[c])
            self.tabla.column(c, width=anchos[c],
                              anchor="center" if c != "municipio" else "w")
        barra2 = ttk.Scrollbar(tab2, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra2.set)
        self.tabla.pack(side="left", fill="both", expand=True, padx=(4, 0))
        barra2.pack(side="right", fill="y")
        self.tabla.tag_configure("par", background="#FFFFFF")
        self.tabla.tag_configure("impar", background="#EEF3F7")
        # Doble clic en un municipio -> detalle de sus pacientes
        self.tabla.bind("<Double-1>", self._abrir_detalle)

        # --- Pestaña 3: ESTADISTICAS (por especialidad) ---
        tab3 = tk.Frame(self.notebook, bg=FONDO)
        self.notebook.add(tab3, text="  📈 Estadisticas  ")
        tk.Label(tab3, text="Citas por especialidad: ¿cuales se pueden hacer por "
                            "telemedicina?", bg=FONDO, fg=AZUL,
                 font=("Helvetica", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Label(tab3, text="Esto le ayuda al hospital a decidir en que "
                            "especialidades conviene crecer con telemedicina.",
                 bg=FONDO, fg=GRIS_TXT, font=("Helvetica", 10)).pack(
                     anchor="w", padx=14, pady=(0, 4))
        leyenda = tk.Frame(tab3, bg=FONDO)
        leyenda.pack(anchor="w", padx=14, pady=(0, 2))
        tk.Frame(leyenda, bg=VERDE, width=14, height=14).pack(side="left")
        tk.Label(leyenda, text="Apta para telemedicina   ", bg=FONDO, fg=GRIS_TXT,
                 font=("Helvetica", 10)).pack(side="left", padx=(4, 10))
        tk.Frame(leyenda, bg=ROJO, width=14, height=14).pack(side="left")
        tk.Label(leyenda, text="Debe ir en persona", bg=FONDO, fg=GRIS_TXT,
                 font=("Helvetica", 10)).pack(side="left", padx=(4, 0))
        self.canvas_stats = tk.Canvas(tab3, bg=BLANCO, highlightthickness=1,
                                      highlightbackground="#E4E9EE")
        self.canvas_stats.pack(fill="both", expand=True, padx=14, pady=(6, 12))

    # -----------------------------------------------------------------
    #  ESTADISTICAS: barras por especialidad (apta vs presencial)
    # -----------------------------------------------------------------
    def _llenar_estadisticas(self, citas):
        cv = self.canvas_stats
        cv.delete("all")
        if "especialidad" not in citas.columns:
            cv.create_text(20, 30, anchor="w", fill=GRIS_TXT,
                           text="Este archivo no tiene columna 'especialidad'.",
                           font=("Helvetica", 12))
            return
        tmp = citas.copy()
        tmp["_apta"] = (tmp["clasificacion"] == "Apta para telemedicina").astype(int)
        g = tmp.groupby("especialidad").agg(
            total=("_apta", "size"), aptas=("_apta", "sum"))
        g = g.sort_values("total", ascending=False).head(12)
        if len(g) == 0:
            return
        max_total = int(g["total"].max())

        x_label = 14
        x_bar   = 230
        bar_max = 360
        row_h   = 30
        y = 16
        for esp, r in g.iterrows():
            total = int(r["total"]); aptas = int(r["aptas"]); pres = total - aptas
            nombre = str(esp).title()
            if len(nombre) > 26:
                nombre = nombre[:25] + "…"
            cv.create_text(x_label, y + 9, anchor="w", text=nombre,
                           font=("Helvetica", 10), fill="#333333")
            wg = (aptas / max_total) * bar_max
            wr = (pres / max_total) * bar_max
            if wg > 0:
                cv.create_rectangle(x_bar, y, x_bar + wg, y + 18, fill=VERDE, width=0)
            if wr > 0:
                cv.create_rectangle(x_bar + wg, y, x_bar + wg + wr, y + 18,
                                    fill=ROJO, width=0)
            cv.create_text(x_bar + wg + wr + 8, y + 9, anchor="w",
                           text=f"{aptas} aptas / {total} total",
                           font=("Helvetica", 9), fill=GRIS_TXT)
            y += row_h
        cv.configure(scrollregion=(0, 0, 760, y + 10))

    # -----------------------------------------------------------------
    #  VENTANA DE DETALLE: pacientes y citas de un municipio
    #  (anonimizado: muestra el CODIGO del paciente, no el nombre real)
    # -----------------------------------------------------------------
    def _buscar_columna(self, df, nombres_posibles):
        """Busca en el archivo una columna con alguno de estos nombres
        (sin importar mayusculas ni espacios). Devuelve el nombre real o None."""
        mapa = {str(c).lower().replace(" ", "").replace("_", ""): c
                for c in df.columns}
        for n in nombres_posibles:
            clave = n.lower().replace(" ", "").replace("_", "")
            if clave in mapa:
                return mapa[clave]
        return None

    def _abrir_detalle(self, evento=None):
        seleccion = self.tabla.focus()
        if not seleccion or self.citas_full is None:
            return
        municipio = self.tabla.item(seleccion, "values")[0]
        # Mostramos TODAS las citas del municipio (aptas y presenciales)
        datos = self.citas_full[self.citas_full["municipio"] == municipio]
        if len(datos) == 0:
            return

        tiene_personales = any([self.col_nombre, self.col_doc, self.col_tel])
        n_aptas = int((datos["clasificacion"] == "Apta para telemedicina").sum())

        win = tk.Toplevel(self)
        win.title("Detalle de " + municipio)
        win.configure(bg=FONDO)
        win.geometry("940x500")

        cab = tk.Frame(win, bg=VERDE, height=62)
        cab.pack(fill="x")
        cab.pack_propagate(False)
        tk.Label(cab, text=municipio, bg=VERDE, fg=BLANCO,
                 font=("Helvetica", 16, "bold")).pack(anchor="w", padx=16, pady=(9, 0))
        subtitulo = (f"{len(datos)} citas  ·  {n_aptas} aptas para telemedicina  ·  "
                     + ("datos personales (uso interno del hospital)"
                        if tiene_personales
                        else "datos anonimizados (codigo de paciente)"))
        tk.Label(cab, text=subtitulo, bg=VERDE, fg="#E8F5F2",
                 font=("Helvetica", 10)).pack(anchor="w", padx=16)

        marco = tk.Frame(win, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=12, pady=12)

        # Columnas: codigo, (nombre/doc/tel si existen), sexo, especialidad,
        # tipo de cita, TELEMEDICINA (apta/no), fecha y ahorro.
        cols, enc, anchos, fuentes = [], {}, {}, {}
        cols.append("cod"); enc["cod"] = "Cod. paciente"; anchos["cod"] = 95
        fuentes["cod"] = "paciente_cod"
        if self.col_nombre:
            cols.append("nombre"); enc["nombre"] = "Nombre"; anchos["nombre"] = 150
            fuentes["nombre"] = self.col_nombre
        if self.col_doc:
            cols.append("doc"); enc["doc"] = "Documento"; anchos["doc"] = 100
            fuentes["doc"] = self.col_doc
        if self.col_tel:
            cols.append("tel"); enc["tel"] = "Telefono"; anchos["tel"] = 100
            fuentes["tel"] = self.col_tel
        for c, titulo, ancho, fuente in [
                ("sexo", "Sexo", 60, "sexo"),
                ("especialidad", "Especialidad", 150, "especialidad"),
                ("actividad", "Tipo de cita", 170, "actividad"),
                ("tele", "Telemedicina", 150, "clasificacion"),
                ("fecha", "Fecha", 95, "fecha_cita"),
                ("dinero", "Ahorro", 90, "dinero")]:
            cols.append(c); enc[c] = titulo; anchos[c] = ancho; fuentes[c] = fuente

        tabla = ttk.Treeview(marco, columns=cols, show="headings")
        izquierda = ("nombre", "especialidad", "actividad", "tele")
        for c in cols:
            tabla.heading(c, text=enc[c])
            tabla.column(c, width=anchos[c],
                         anchor="w" if c in izquierda else "center")
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        # Filas alternadas (clara / gris) para que se vea ordenado.
        tabla.tag_configure("par", background="#FFFFFF")
        tabla.tag_configure("impar", background="#EEF3F7")

        for i, (_, r) in enumerate(datos.iterrows()):
            es_apta_fila = r["clasificacion"] == "Apta para telemedicina"
            fila = []
            for c in cols:
                fuente = fuentes[c]
                if c == "dinero":
                    val = r.get("dinero")
                    fila.append("$" + f"{int(val):,}".replace(",", ".")
                                if pd.notna(val) else "-")
                elif c == "tele":
                    fila.append("Apta" if es_apta_fila else "Debe ir en persona")
                elif c == "fecha":
                    fila.append(str(r.get(fuente, "-"))[:10])
                elif c == "especialidad":
                    fila.append(str(r.get(fuente, "-")).title())
                elif c == "actividad":
                    fila.append(self._limpiar_actividad(r.get(fuente, "-")))
                else:
                    fila.append(r.get(fuente, "-"))
            etiqueta = "par" if i % 2 == 0 else "impar"
            tabla.insert("", "end", values=tuple(fila), tags=(etiqueta,))

        self._boton(win, "Cerrar", AZUL, win.destroy).pack(pady=(0, 12))

    # -----------------------------------------------------------------
    #  PIE DE PAGINA (autoria)
    # -----------------------------------------------------------------
    def _construir_pie(self):
        pie = tk.Frame(self, bg=FONDO)
        pie.pack(fill="x", padx=16, pady=(2, 10))
        tk.Label(pie,
                 text="Desarrollada por Maria Alejandra Lopez",
                 bg=FONDO, fg=GRIS_TXT, font=("Helvetica", 9)).pack(side="left")

    # -----------------------------------------------------------------
    #  CARGA DE DATOS
    # -----------------------------------------------------------------
    def _cargar_automatico(self):
        """Al abrir, busca citas_anonimizado.csv en la misma carpeta."""
        carpeta = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(carpeta, "citas_anonimizado.csv")
        if os.path.exists(ruta):
            self._procesar(ruta)

    def _cargar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Elige el archivo de citas",
            filetypes=[("Excel o CSV", "*.xlsx *.xls *.csv"),
                       ("Todos", "*.*")])
        if ruta:
            self._procesar(ruta)

    def _procesar(self, ruta):
        """Lee el archivo, clasifica las citas y calcula el ahorro."""
        try:
            if ruta.lower().endswith(".csv"):
                citas = pd.read_csv(ruta)
            else:
                citas = pd.read_excel(ruta)
        except Exception as e:
            messagebox.showerror("No se pudo leer el archivo", str(e))
            return

        # Lo UNICO imprescindible es la columna 'actividad' (para clasificar).
        # El municipio y el ahorro son un extra: si no estan, igual se carga.
        if "actividad" not in citas.columns:
            messagebox.showerror(
                "Falta una columna",
                "El archivo debe tener al menos la columna 'actividad'\n"
                "(es la que dice el tipo de cita).")
            return

        # ---- PARTE 1: CLASIFICAR (siempre funciona) ----
        # Clasifica mirando la actividad y, si existe, tambien la especialidad.
        if "especialidad" in citas.columns:
            citas["clasificacion"] = citas.apply(
                lambda r: es_apta(r["actividad"], r.get("especialidad", "")), axis=1)
        else:
            citas["clasificacion"] = citas["actividad"].apply(es_apta)
        n_aptas = int((citas["clasificacion"] == "Apta para telemedicina").sum())
        n_pres  = int((citas["clasificacion"] == "Necesita ir en persona").sum())

        # ---- PARTE 2: AHORRO (solo si hay municipio y tabla de distancias) ----
        carpeta = os.path.dirname(os.path.abspath(__file__))
        ruta_dist = os.path.join(carpeta, "distancias_municipios.csv")
        hay_ahorro = ("municipio" in citas.columns) and os.path.exists(ruta_dist)

        total_km = total_horas = total_dinero = 0
        por_muni = None
        if hay_ahorro:
            distancias = pd.read_csv(ruta_dist)
            citas = citas.merge(distancias, on="municipio", how="left")
            aptas = citas[(citas["clasificacion"] == "Apta para telemedicina") &
                          (citas["municipio"] != "POPAYAN") &
                          (citas["via_terrestre"] == "si")].copy()
            aptas["km_ida_vuelta"] = aptas["km_una_via"] * 2
            aptas["horas_viaje"]   = aptas["km_ida_vuelta"] / VELOCIDAD
            # Dinero ahorrado = transporte intermunicipal + urbano + almuerzo + hotel
            aptas["transporte"] = aptas["km_ida_vuelta"] * COSTO_KM
            aptas["urbano"]     = URBANO
            aptas["almuerzo"]   = ALMUERZO
            aptas["hotel"]      = aptas["km_una_via"].apply(
                lambda k: HOTEL if k >= KM_HOTEL else 0)
            aptas["dinero"] = (aptas["transporte"] + aptas["urbano"]
                               + aptas["almuerzo"] + aptas["hotel"])
            total_km     = int(aptas["km_ida_vuelta"].sum())
            total_horas  = int(aptas["horas_viaje"].sum())
            total_dinero = int(aptas["dinero"].sum())
            self.aptas_df = aptas
            por_muni = (aptas.groupby("municipio")
                        .agg(citas=("dinero", "size"),
                             km=("km_ida_vuelta", "sum"),
                             horas=("horas_viaje", "sum"),
                             dinero=("dinero", "sum"))
                        .sort_values("dinero", ascending=False))
        else:
            self.aptas_df = None

        self.citas_full = citas   # todas las citas clasificadas (para el detalle)

        # Detectamos datos personales (nombre, documento, telefono) si vienen
        self.col_nombre = self._buscar_columna(
            citas, ["nombre", "nombres", "paciente_nombre", "pacientenombre",
                    "nombre_paciente"])
        self.col_doc = self._buscar_columna(
            citas, ["documento", "cedula", "identificacion", "paciente_documento",
                    "pacientedocumento", "num_documento"])
        self.col_tel = self._buscar_columna(
            citas, ["telefono", "celular", "paciente_telefono", "pacientetelefono",
                    "tel", "movil"])

        # guardar para exportar
        self.resultado = {
            "total": len(citas), "aptas": n_aptas, "presencial": n_pres,
            "km": total_km, "horas": total_horas, "dinero": total_dinero,
            "por_muni": por_muni}

        # ---- PINTAR TARJETAS ----
        self.tarjetas["aptas"].config(text=f"{n_aptas}")
        self.tarjetas["presencial"].config(text=f"{n_pres}")
        if hay_ahorro:
            self.tarjetas["km"].config(text=f"{total_km:,}".replace(",", "."))
            self.tarjetas["dinero"].config(
                text="$" + f"{total_dinero:,}".replace(",", "."))
        else:
            self.tarjetas["km"].config(text="-")
            self.tarjetas["dinero"].config(text="-")

        # ---- FRASE RESUMEN (menu principal) ----
        resumen_txt = (f"Se analizaron {len(citas)} citas:  "
                       f"{n_aptas} aptas para telemedicina  y  "
                       f"{n_pres} que deben ir en persona.")
        if hay_ahorro and total_dinero > 0:
            resumen_txt += ("\nLos pacientes de fuera de Popayan se ahorrarian "
                            + f"{total_km:,}".replace(",", ".") + " km, "
                            + f"{total_horas} horas de viaje y $"
                            + f"{total_dinero:,}".replace(",", ".")
                            + " en transporte.")
        else:
            resumen_txt += ("\n(Este archivo no tiene municipios reconocidos, "
                            "por eso no se calcula el ahorro.)")
        self.lbl_resumen.config(text=resumen_txt)

        # ---- PESTAÑA 1: lista de clasificacion (apta / no apta) ----
        self._llenar_clasificacion(citas)

        # ---- PESTAÑA 3: estadisticas por especialidad ----
        self._llenar_estadisticas(citas)

        # ---- PESTAÑA 2: tabla de ahorro por municipio ----
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        if hay_ahorro and por_muni is not None and len(por_muni) > 0:
            self.aviso_muni.config(
                text="💡 Doble clic en un municipio para ver sus pacientes y citas")
            for i, (muni, r) in enumerate(por_muni.iterrows()):
                etiqueta = "par" if i % 2 == 0 else "impar"
                self.tabla.insert("", "end", tags=(etiqueta,), values=(
                    muni, int(r["citas"]), f"{int(r['km']):,}".replace(",", "."),
                    int(r["horas"]),
                    "$" + f"{int(r['dinero']):,}".replace(",", ".")))
        else:
            self.aviso_muni.config(
                text="ⓘ Este archivo no tiene municipios reconocidos, asi que no se "
                     "calcula el ahorro. La clasificacion (pestana 1) si funciona.")

        self.lbl_archivo.config(text="Archivo: " + os.path.basename(ruta))

    def _llenar_clasificacion(self, citas):
        """Llena la pestana 1 con todas las citas y su clasificacion."""
        for fila in self.tabla_clasif.get_children():
            self.tabla_clasif.delete(fila)
        tiene_cod = "paciente_cod" in citas.columns
        tiene_esp = "especialidad" in citas.columns
        for i, (_, r) in enumerate(citas.iterrows()):
            apta = r["clasificacion"] == "Apta para telemedicina"
            etiqueta = "par" if i % 2 == 0 else "impar"
            self.tabla_clasif.insert("", "end", tags=(etiqueta,), values=(
                r.get("paciente_cod", "-") if tiene_cod else "-",
                str(r.get("especialidad", "-")).title() if tiene_esp else "-",
                self._limpiar_actividad(r.get("actividad", "-")),
                "Apta" if apta else "Debe ir en persona"))

    # -----------------------------------------------------------------
    #  EXPORTAR A EXCEL
    # -----------------------------------------------------------------
    def _exportar_excel(self):
        if self.resultado is None:
            messagebox.showinfo("Primero carga un archivo",
                                "Carga un archivo de citas antes de exportar.")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar resultados",
            defaultextension=".xlsx",
            initialfile="resultados_telemedicina.xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not ruta:
            return
        r = self.resultado
        resumen = pd.DataFrame({
            "Indicador": ["Total de citas", "Aptas para telemedicina",
                          "Deben ir en persona", "Kilometros ahorrados",
                          "Horas ahorradas", "Dinero ahorrado (COP)"],
            "Valor": [r["total"], r["aptas"], r["presencial"],
                      r["km"], r["horas"], r["dinero"]]})
        try:
            with pd.ExcelWriter(ruta) as writer:
                resumen.to_excel(writer, sheet_name="Resumen", index=False)
                if self.citas_full is not None:
                    cols_clasif = [c for c in ["paciente_cod", "sexo", "especialidad",
                                               "actividad", "municipio", "fecha_cita",
                                               "clasificacion"]
                                   if c in self.citas_full.columns]
                    self.citas_full[cols_clasif].to_excel(
                        writer, sheet_name="Clasificacion", index=False)
                if r["por_muni"] is not None and len(r["por_muni"]) > 0:
                    r["por_muni"].reset_index().to_excel(
                        writer, sheet_name="Por municipio", index=False)
            messagebox.showinfo("Listo",
                                "Resultados guardados en:\n" + ruta)
        except Exception as e:
            messagebox.showerror("No se pudo guardar", str(e))


if __name__ == "__main__":
    app = AppTelemedicina()
    app.mainloop()
