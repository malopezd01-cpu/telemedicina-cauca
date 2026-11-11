# -*- coding: utf-8 -*-
# =====================================================================
#  TelemedicinaCauca - App de Telemedicina  (version moderna)
#  Hospital Universitario San Jose (Popayan) - area de Telemedicina
#  Autora: Maria Alejandra Lopez
#
#  Hecha con CustomTkinter (interfaz moderna).
#  1) Identifica que citas son APTAS para telemedicina y cuales deben ir
#     en PERSONA.  2) Calcula el AHORRO de los pacientes (transporte,
#     almuerzo, hotel).  3) Muestra el IMPACTO ECONOMICO para el hospital.
# =====================================================================

import os
import sys
import unicodedata
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import customtkinter as ctk


def ruta_recurso(nombre):
    """Encuentra un archivo que viaja con la app (logo, CSV de datos).
    Funciona igual si corres con Python o si la app ya es un programa
    empaquetado (.app en Mac / .exe en Windows con PyInstaller)."""
    base = getattr(sys, "_MEIPASS",
                   os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)
import matplotlib
matplotlib.use("TkAgg")                       # para dibujar dentro de la ventana
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------------
#  COLORES
# ---------------------------------------------------------------------
AZUL     = "#1B3A6B"
VERDE    = "#2A9D8F"
VERDE_SU = "#D7F0EB"   # verde suave para resaltar filas aptas
NARANJA  = "#E8954A"
ROJO     = "#E76F51"
FONDO    = "#EEF2F6"
CARD     = "#FFFFFF"
GRIS     = "#6B7A8A"
TEXTO    = "#1F2937"

# ---------------------------------------------------------------------
#  PARAMETROS DEL CALCULO (ajustables)
# ---------------------------------------------------------------------
COSTO_KM       = 250     # pasaje intermunicipal aprox. por km (tarifas del Cauca)
VELOCIDAD      = 40      # km/h promedio carreteras del Cauca
URBANO         = 6000    # transporte urbano en Popayan, ida y vuelta, por persona
COMIDA         = 25000   # alimentacion del dia: desayuno + almuerzo
JORNAL         = 47450   # dia de trabajo/ingreso perdido = salario minimo 2025
                         # ($1.423.500 / 30 dias). Es el "costo de oportunidad".
HOTEL          = 70000   # hospedaje una noche en Popayan
KM_HOTEL       = 100     # a mas de estos km (una via) se asume 1 noche de hotel
KM_HOTEL2      = 200     # a mas de estos km se asumen 2 noches
ACOMPANANTE    = True    # muchos pacientes viajan con un acompañante (dobla
                         # transporte, comida y dia perdido; el hotel se comparte)
VALOR_CONSULTA = 40000   # valor estimado que recibe el hospital por consulta
                         # (CAMBIAR por el valor real que indique el hospital)
CO2_POR_KM     = 0.12    # kg de CO2 por km (vehiculo de pasajeros promedio)
                         # para estimar la contaminacion que se evita al no viajar

NO_APTAS = ["TERAPIA", "ELECTRO", "RADIOLOG", "RX", "TAC", "RESONANC",
            "ECOCARDIO", "HOLTER", "PROCEDIMIENTO", "IMAGEN",
            "ADMINISTRACION DE MEDICAMENTOS", "ECOGRAF", "CANGURO"]
NO_APTAS_ESP = ["TERAPIA", "REHABILITAC", "MEDICINA FISICA", "RADIOLOG",
                "IMAGEN", "HEMODINAM", "ELECTROESTIMULA", "ELECTROFISIOLOG",
                "LABORATORIO", "PATOLOGIA", "ENDOSCOP", "ECOGRAF"]


def es_apta(actividad, especialidad=""):
    esp = str(especialidad).upper()
    for p in NO_APTAS_ESP:
        if p in esp:
            return "Necesita ir en persona"
    texto = str(actividad).upper()
    for p in NO_APTAS:
        if p in texto:
            return "Necesita ir en persona"
    return "Apta para telemedicina"


def pesos(n):
    """Formatea un numero como pesos colombianos: 19252000 -> $19.252.000"""
    return "$" + f"{int(n):,}".replace(",", ".")


def quitar_tildes(texto):
    """POPAYÁN -> POPAYAN ; deja todo en mayuscula y sin tildes."""
    t = str(texto).strip().upper()
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


# Nombres posibles de cada columna (para leer CUALQUIER Excel del hospital).
# Se buscan como "contiene": por ejemplo "actividad" encuentra "Actividad.Nombre".
# El orden importa: se usa el primero que aparezca.
ALIAS_COLUMNAS = {
    "actividad":    ["actividad", "tipodecita", "tipocita", "servicio",
                     "procedimiento", "tipoatencion", "motivo"],
    "especialidad": ["especialidad", "espec"],
    "municipio":    ["nombremunicipio", "municipio", "ciudad", "mpio"],
    "paciente_cod": ["pacientecod", "codigopaciente", "codpaciente", "idpaciente",
                     "identificador", "codigopac"],
    "sexo":         ["pacientesexo", "sexo", "genero"],
    "fecha_cita":   ["fechainicialcita", "fechacita", "fechadelacita",
                     "fechaatencion", "fecha"],
}


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TelemedicinaCauca - Hospital Universitario San Jose")
        self.geometry("1040x700")
        self.minsize(940, 660)
        self.configure(fg_color=FONDO)

        self.citas_full = None
        self.aptas_df = None
        self.resultado = None
        self.col_nombre = self.col_doc = self.col_tel = None
        self.modo_clasif = "Todas"
        self.filtro_esp = "Todas"
        self.filtro_muni = "Todos"
        self.busqueda = ""
        self._buscar_job = None
        self.cols_clasif = ("cod", "especialidad", "actividad", "tele")
        self.clasif_src = {"cod": "paciente_cod", "especialidad": "especialidad",
                           "actividad": "actividad", "tele": "clasificacion"}

        self._estilo_treeview()
        self._header()
        self._barra_acciones()
        self._tabs()
        self._pie()
        self._cargar_automatico()

    # -----------------------------------------------------------------
    def _estilo_treeview(self):
        est = ttk.Style()
        try:
            est.theme_use("clam")
        except Exception:
            pass
        est.configure("Treeview", rowheight=38, font=("Helvetica", 15),
                      background=CARD, fieldbackground=CARD, borderwidth=0)
        est.configure("Treeview.Heading", font=("Helvetica", 15, "bold"),
                      background=AZUL, foreground="white", relief="flat", padding=8)
        est.map("Treeview.Heading", background=[("active", AZUL)])
        est.map("Treeview", background=[("selected", VERDE)],
                foreground=[("selected", "white")])

    # -----------------------------------------------------------------
    def _header(self):
        head = ctk.CTkFrame(self, fg_color=AZUL, corner_radius=0, height=86)
        head.pack(fill="x")
        head.pack_propagate(False)

        ruta_logo = ruta_recurso("logo_telecauca.png")
        if os.path.exists(ruta_logo):
            try:
                from PIL import Image
                img = Image.open(ruta_logo)
                self.logo = ctk.CTkImage(light_image=img, dark_image=img,
                                         size=(58, 58))
                ctk.CTkLabel(head, image=self.logo, text="").pack(
                    side="left", padx=(20, 14))
            except Exception:
                pass

        cajatxt = ctk.CTkFrame(head, fg_color="transparent")
        cajatxt.pack(side="left", pady=16)
        ctk.CTkLabel(cajatxt, text="TelemedicinaCauca", text_color="white",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(cajatxt, text="Hospital Universitario San Jose  ·  Telemedicina",
                     text_color="#C7D6EA",
                     font=ctk.CTkFont(size=13)).pack(anchor="w")

    # -----------------------------------------------------------------
    def _barra_acciones(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(14, 4))

        ctk.CTkButton(barra, text="📂  Cargar archivo de citas",
                      command=self._cargar_archivo, fg_color=VERDE,
                      hover_color="#228377", corner_radius=10, height=40,
                      font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(barra, text="📞  Lista para llamar",
                      command=self._lista_llamar, fg_color=NARANJA,
                      hover_color="#cf7f3a", corner_radius=10, height=40,
                      font=ctk.CTkFont(size=13, weight="bold")).pack(
                          side="left", padx=10)
        ctk.CTkButton(barra, text="⬇  Exportar a Excel",
                      command=self._exportar_excel, fg_color=AZUL,
                      hover_color="#142d53", corner_radius=10, height=40,
                      font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.lbl_archivo = ctk.CTkLabel(barra, text="", text_color=GRIS,
                                        font=ctk.CTkFont(size=12))
        self.lbl_archivo.pack(side="left", padx=10)

    # -----------------------------------------------------------------
    def _tabs(self):
        self.tabs = ctk.CTkTabview(self, fg_color=CARD,
                                   segmented_button_selected_color=VERDE,
                                   segmented_button_selected_hover_color="#228377")
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(8, 6))
        self.tabs.add("🏠 Inicio")
        self.tabs.add("1. Clasificacion")
        self.tabs.add("2. Ahorro por municipio")
        self.tabs.add("📈 Estadisticas")
        # Agrandar la letra del menu de pestañas (se veia muy chiquita)
        try:
            self.tabs._segmented_button.configure(
                font=ctk.CTkFont(size=15, weight="bold"), height=40)
        except Exception:
            pass

        self._tab_inicio(self.tabs.tab("🏠 Inicio"))
        self._tab_clasificacion(self.tabs.tab("1. Clasificacion"))
        self._tab_ahorro(self.tabs.tab("2. Ahorro por municipio"))
        self._tab_estadisticas(self.tabs.tab("📈 Estadisticas"))

    # ---------- TARJETA KPI reutilizable ----------
    def _kpi(self, parent, color):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14,
                            border_width=1, border_color="#E2E8F0")
        ctk.CTkFrame(card, fg_color=color, corner_radius=0, height=6).pack(fill="x")
        valor = ctk.CTkLabel(card, text="-", text_color=color,
                             font=ctk.CTkFont(size=28, weight="bold"))
        valor.pack(pady=(16, 0))
        titulo = ctk.CTkLabel(card, text="", text_color=GRIS,
                              font=ctk.CTkFont(size=12))
        titulo.pack(pady=(2, 16), padx=12)
        return card, valor, titulo

    # ---------- TAB INICIO ----------
    def _tab_inicio(self, tab):
        ctk.CTkLabel(tab, text="Resumen general", text_color=AZUL,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(
                         anchor="w", padx=16, pady=(16, 8))

        fila = ctk.CTkFrame(tab, fg_color="transparent")
        fila.pack(fill="x", padx=10)
        self.tarjetas = {}
        for clave, titulo, color in [
                ("aptas", "Aptas para telemedicina", VERDE),
                ("presencial", "Deben ir en persona", ROJO),
                ("km", "Kilometros ahorrados", AZUL),
                ("dinero", "Ahorro a pacientes", NARANJA)]:
            card, valor, tit = self._kpi(fila, color)
            card.pack(side="left", expand=True, fill="both", padx=6)
            tit.configure(text=titulo)
            self.tarjetas[clave] = valor

        self.lbl_resumen = ctk.CTkLabel(
            tab, text="Carga un archivo de citas para ver el resumen.",
            text_color=TEXTO, font=ctk.CTkFont(size=14), justify="left",
            wraplength=900)
        self.lbl_resumen.pack(anchor="w", padx=18, pady=(14, 8))

        ctk.CTkLabel(
            tab, text="Explora las pestanas de arriba:  '1. Clasificacion' para ver "
                      "cada cita,\n'2. Ahorro por municipio' y '📈 Estadisticas' para "
                      "el impacto en el hospital.",
            text_color=GRIS, font=ctk.CTkFont(size=13), justify="left").pack(
                anchor="w", padx=18, pady=(0, 10))

    # ---------- TAB CLASIFICACION ----------
    def _tab_clasificacion(self, tab):
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(14, 6))
        ctk.CTkLabel(top, text="Clasificacion de cada cita", text_color=AZUL,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(top, text="Las citas aptas para telemedicina aparecen "
                               "resaltadas en verde. Usa el filtro para verlas.",
                     text_color=GRIS, font=ctk.CTkFont(size=12)).pack(anchor="w")

        self.filtro = ctk.CTkSegmentedButton(
            tab, values=["Todas", "✓ Solo telemedicina", "Presenciales"],
            command=self._set_filtro, selected_color=VERDE,
            selected_hover_color="#228377",
            font=ctk.CTkFont(size=13, weight="bold"))
        self.filtro.set("Todas")
        self.filtro.pack(anchor="w", padx=12, pady=(4, 8))

        # --- buscador de paciente (por nombre o codigo) ---
        buscar = ctk.CTkFrame(tab, fg_color="transparent")
        buscar.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(buscar, text="🔎 Buscar paciente:",
                     text_color=AZUL,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.entry_buscar = ctk.CTkEntry(
            buscar, placeholder_text="nombre, cedula o codigo de paciente",
            width=300, height=34, corner_radius=10)
        self.entry_buscar.pack(side="left", padx=8)
        self.entry_buscar.bind("<KeyRelease>", self._buscar)
        ctk.CTkButton(buscar, text="Limpiar", command=self._limpiar_busqueda,
                      fg_color=GRIS, hover_color="#55606e", width=80, height=34,
                      corner_radius=10,
                      font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(buscar, text="Doble clic en un paciente para ver toda su "
                                  "informacion.",
                     text_color=GRIS, font=ctk.CTkFont(size=11)).pack(
                         side="left", padx=12)

        # --- filtros por especialidad y municipio ---
        filtros = ctk.CTkFrame(tab, fg_color="transparent")
        filtros.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(filtros, text="Especialidad:", text_color=AZUL,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.opt_esp = ctk.CTkOptionMenu(
            filtros, values=["Todas"], command=self._set_filtro_esp,
            width=220, fg_color=AZUL, button_color="#142d53",
            button_hover_color="#0f2340")
        self.opt_esp.pack(side="left", padx=(6, 16))
        ctk.CTkLabel(filtros, text="Municipio:", text_color=AZUL,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.opt_muni = ctk.CTkOptionMenu(
            filtros, values=["Todos"], command=self._set_filtro_muni,
            width=200, fg_color=AZUL, button_color="#142d53",
            button_hover_color="#0f2340")
        self.opt_muni.pack(side="left", padx=6)

        cont = ctk.CTkFrame(tab, fg_color="transparent")
        cont.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        cols = ("cod", "especialidad", "actividad", "tele")
        self.tabla_clasif = ttk.Treeview(cont, columns=cols, show="headings")
        enc = {"cod": "Cod. paciente", "especialidad": "Especialidad",
               "actividad": "Tipo de cita", "tele": "Telemedicina"}
        anchos = {"cod": 110, "especialidad": 210, "actividad": 280, "tele": 170}
        for c in cols:
            self.tabla_clasif.heading(c, text=enc[c])
            self.tabla_clasif.column(
                c, width=anchos[c],
                anchor="w" if c in ("especialidad", "actividad", "tele") else "center")
        sb = ttk.Scrollbar(cont, orient="vertical", command=self.tabla_clasif.yview)
        self.tabla_clasif.configure(yscrollcommand=sb.set)
        self.tabla_clasif.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tabla_clasif.tag_configure("apta", background=VERDE_SU,
                                        foreground="#0F5C52")
        self.tabla_clasif.tag_configure("pres", background=CARD, foreground=GRIS)
        self.tabla_clasif.bind("<Double-1>", self._detalle_paciente)
        self._fila_idx = {}   # relaciona cada fila de la tabla con su cita

    # ---------- TAB AHORRO ----------
    def _tab_ahorro(self, tab):
        self.aviso_muni = ctk.CTkLabel(
            tab, text="Doble clic en un municipio para ver sus pacientes y citas",
            text_color=GRIS, font=ctk.CTkFont(size=12))
        self.aviso_muni.pack(anchor="w", padx=14, pady=(14, 6))

        cont = ctk.CTkFrame(tab, fg_color="transparent")
        cont.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        cols = ("municipio", "citas", "km", "horas", "dinero")
        self.tabla = ttk.Treeview(cont, columns=cols, show="headings")
        enc = {"municipio": "Municipio", "citas": "Citas aptas",
               "km": "Km evitados", "horas": "Horas", "dinero": "Dinero ahorrado"}
        anchos = {"municipio": 230, "citas": 95, "km": 110, "horas": 90, "dinero": 160}
        for c in cols:
            self.tabla.heading(c, text=enc[c])
            self.tabla.column(c, width=anchos[c],
                              anchor="center" if c != "municipio" else "w")
        sb = ttk.Scrollbar(cont, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tabla.tag_configure("par", background=CARD)
        self.tabla.tag_configure("impar", background="#F1F5F9")
        self.tabla.bind("<Double-1>", self._abrir_detalle)

    # ---------- TAB ESTADISTICAS ----------
    def _tab_estadisticas(self, tab):
        cont = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        cont.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(cont, text="Impacto economico para el hospital", text_color=AZUL,
                     font=ctk.CTkFont(size=17, weight="bold")).pack(
                         anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(cont, text="Cada cita atendida por telemedicina es un servicio "
                               "que el hospital presta y puede facturar, llegando "
                               "ademas a municipios lejanos.",
                     text_color=GRIS, font=ctk.CTkFont(size=12),
                     wraplength=900, justify="left").pack(anchor="w", padx=12)

        fila = ctk.CTkFrame(cont, fg_color="transparent")
        fila.pack(fill="x", padx=6, pady=(10, 4))
        self.eco = {}
        for clave, titulo, color in [
                ("tele", "Teleconsultas / semana", VERDE),
                ("sem", "Valor para el hospital / semana", AZUL),
                ("anio", "Proyeccion al año (estimada)", NARANJA),
                ("cob", "Llegan desde otros municipios", VERDE)]:
            card, valor, tit = self._kpi(fila, color)
            card.pack(side="left", expand=True, fill="both", padx=6)
            tit.configure(text=titulo)
            self.eco[clave] = valor

        self.lbl_eco = ctk.CTkLabel(cont, text="", text_color=GRIS,
                                    font=ctk.CTkFont(size=12), justify="left",
                                    wraplength=900)
        self.lbl_eco.pack(anchor="w", padx=12, pady=(2, 8))

        # --- caja de OPORTUNIDAD + IMPACTO AMBIENTAL ---
        caja = ctk.CTkFrame(cont, fg_color=VERDE_SU, corner_radius=12)
        caja.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(caja, text="🎯 Donde conviene impulsar la telemedicina",
                     text_color=AZUL,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
                         anchor="w", padx=14, pady=(10, 0))
        self.lbl_alerta = ctk.CTkLabel(caja, text="Carga un archivo para ver la "
                                       "oportunidad.", text_color=TEXTO,
                                       font=ctk.CTkFont(size=13), justify="left",
                                       wraplength=870)
        self.lbl_alerta.pack(anchor="w", padx=14, pady=(2, 6))
        self.lbl_ambiental = ctk.CTkLabel(caja, text="", text_color="#1E6F63",
                                          font=ctk.CTkFont(size=13, weight="bold"),
                                          justify="left", wraplength=870)
        self.lbl_ambiental.pack(anchor="w", padx=14, pady=(0, 12))

        # --- graficas dentro de la app ---
        ctk.CTkLabel(cont, text="Graficas", text_color=AZUL,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
                         anchor="w", padx=12, pady=(2, 2))
        self.graf_frame = ctk.CTkFrame(cont, fg_color=CARD, corner_radius=12,
                                       height=300)
        self.graf_frame.pack(fill="x", padx=12, pady=(2, 10))
        self.graf_frame.pack_propagate(False)
        self._canvas_graf = None

        # --- aptitud por especialidad ---
        ctk.CTkLabel(cont, text="¿Que tan apta es cada especialidad para telemedicina?",
                     text_color=AZUL,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
                         anchor="w", padx=12, pady=(4, 2))
        self.scroll_esp = ctk.CTkFrame(cont, fg_color=CARD, corner_radius=12)
        self.scroll_esp.pack(fill="x", padx=12, pady=(2, 12))

    # =================================================================
    #  CARGA Y PROCESAMIENTO
    # =================================================================
    def _cargar_automatico(self):
        ruta = ruta_recurso("citas_anonimizado.csv")
        if os.path.exists(ruta):
            self._procesar(ruta)

    def _cargar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Elige el archivo de citas",
            filetypes=[("Excel o CSV", "*.xlsx *.xls *.csv"), ("Todos", "*.*")])
        if ruta:
            self._procesar(ruta)

    def _norm_col(self, texto):
        """Normaliza un nombre de columna: minusculas, sin espacios, puntos,
        guiones ni tildes. 'Actividad.Nombre' -> 'actividadnombre'."""
        t = quitar_tildes(texto).lower()
        for ch in " ._-/":
            t = t.replace(ch, "")
        return t

    def _buscar_columna(self, df, nombres):
        """Busca una columna cuyo nombre CONTENGA alguno de los alias.
        Primero intenta coincidencia exacta, luego 'contiene'."""
        mapa = {self._norm_col(c): c for c in df.columns}
        for n in nombres:
            k = self._norm_col(n)
            if k in mapa:
                return mapa[k]
        for n in nombres:
            k = self._norm_col(n)
            for col_norm, col_real in mapa.items():
                if k in col_norm:
                    return col_real
        return None

    def _estandarizar(self, citas):
        """Detecta como se llaman las columnas en ESTE Excel y las renombra a
        nombres estandar. Asi la app lee cualquier archivo del hospital aunque
        las columnas tengan otro nombre."""
        renombrar = {}
        for estandar, alias in ALIAS_COLUMNAS.items():
            if estandar in citas.columns:
                continue
            encontrada = self._buscar_columna(citas, alias)
            if encontrada:
                renombrar[encontrada] = estandar
        if renombrar:
            citas = citas.rename(columns=renombrar)
        if "municipio" in citas.columns:
            citas["municipio"] = citas["municipio"].apply(quitar_tildes)
        return citas

    def _procesar(self, ruta):
        try:
            citas = (pd.read_csv(ruta) if ruta.lower().endswith(".csv")
                     else pd.read_excel(ruta))
        except Exception as e:
            messagebox.showerror("No se pudo leer el archivo", str(e))
            return

        # Algunos archivos del hospital traen muchas filas repetidas; las
        # quitamos para no contar la misma cita varias veces.
        citas = citas.drop_duplicates().reset_index(drop=True)

        # Detectar y estandarizar los nombres de las columnas
        citas = self._estandarizar(citas)
        if "actividad" not in citas.columns:
            messagebox.showwarning(
                "No encuentro el tipo de cita",
                "No pude identificar la columna con el tipo de cita o actividad.\n\n"
                "El Excel deberia tener una columna como 'actividad', "
                "'tipo de cita', 'servicio' o 'procedimiento'.\n\n"
                "Columnas de tu archivo:\n"
                + ", ".join(str(c) for c in citas.columns))
            return

        # clasificar
        if "especialidad" in citas.columns:
            citas["clasificacion"] = citas.apply(
                lambda r: es_apta(r["actividad"], r.get("especialidad", "")), axis=1)
        else:
            citas["clasificacion"] = citas["actividad"].apply(es_apta)
        n_aptas = int((citas["clasificacion"] == "Apta para telemedicina").sum())
        n_pres = int((citas["clasificacion"] == "Necesita ir en persona").sum())

        # ahorro de pacientes (si hay municipio + distancias)
        ruta_dist = ruta_recurso("distancias_municipios.csv")
        hay_ahorro = ("municipio" in citas.columns) and os.path.exists(ruta_dist)
        total_km = total_horas = total_dinero = 0
        aptas_fuera = 0
        por_muni = None
        if hay_ahorro:
            dist = pd.read_csv(ruta_dist)
            dist["municipio"] = dist["municipio"].apply(quitar_tildes)
            citas = citas.merge(dist, on="municipio", how="left")
            aptas = citas[(citas["clasificacion"] == "Apta para telemedicina") &
                          (citas["municipio"] != "POPAYAN") &
                          (citas["via_terrestre"] == "si")].copy()
            personas = 2 if ACOMPANANTE else 1   # paciente (+ acompañante)
            aptas["km_ida_vuelta"] = aptas["km_una_via"] * 2
            aptas["horas_viaje"] = aptas["km_ida_vuelta"] / VELOCIDAD
            # noches de hotel segun que tan lejos queda el municipio
            aptas["noches"] = aptas["km_una_via"].apply(
                lambda k: 2 if k >= KM_HOTEL2 else (1 if k >= KM_HOTEL else 0))
            # pasajes, comida y dia perdido se multiplican por las personas
            aptas["transporte"] = aptas["km_ida_vuelta"] * COSTO_KM * personas
            aptas["urbano"] = URBANO * personas
            aptas["comida"] = COMIDA * personas
            # dias perdidos = 1 + las noches que tengan que quedarse
            aptas["jornal"] = (1 + aptas["noches"]) * JORNAL * personas
            # el hotel se comparte, no se multiplica por persona
            aptas["hotel"] = aptas["noches"] * HOTEL
            aptas["dinero"] = (aptas["transporte"] + aptas["urbano"]
                               + aptas["comida"] + aptas["jornal"]
                               + aptas["hotel"])
            total_km = int(aptas["km_ida_vuelta"].sum())
            total_horas = int(aptas["horas_viaje"].sum())
            total_dinero = int(aptas["dinero"].sum())
            aptas_fuera = len(aptas)
            self.aptas_df = aptas
            por_muni = (aptas.groupby("municipio")
                        .agg(citas=("dinero", "size"), km=("km_ida_vuelta", "sum"),
                             horas=("horas_viaje", "sum"), dinero=("dinero", "sum"))
                        .sort_values("dinero", ascending=False))
        else:
            self.aptas_df = None

        self.citas_full = citas
        # (especificos primero, para no confundir con otras columnas que
        #  tengan la palabra 'nombre', como NombreMunicipio o Medico.Nombre)
        self.col_nombre = self._buscar_columna(
            citas, ["pacientenombre", "nombrepaciente", "nombredelpaciente"])
        self.col_doc = self._buscar_columna(
            citas, ["pacientedocumento", "documento", "cedula", "identificacion"])
        self.col_tel = self._buscar_columna(
            citas, ["pacientetelefono", "telefono", "celular", "movil"])

        # Ajustar las columnas de la tabla de Clasificacion segun lo que
        # traiga el archivo (nombre y documento si existen, para poder buscar).
        self._config_clasif_cols()
        self._poblar_filtros(citas)

        # valor economico para el hospital
        valor_sem = n_aptas * VALOR_CONSULTA
        valor_anio = valor_sem * 52
        self.resultado = {"total": len(citas), "aptas": n_aptas,
                          "presencial": n_pres, "km": total_km,
                          "horas": total_horas, "dinero": total_dinero,
                          "por_muni": por_muni}

        # ---- pintar tarjetas inicio ----
        self.tarjetas["aptas"].configure(text=str(n_aptas))
        self.tarjetas["presencial"].configure(text=str(n_pres))
        self.tarjetas["km"].configure(
            text=f"{total_km:,}".replace(",", ".") if hay_ahorro else "-")
        self.tarjetas["dinero"].configure(
            text=pesos(total_dinero) if hay_ahorro else "-")

        resumen = (f"Se analizaron {len(citas)} citas:  {n_aptas} aptas para "
                   f"telemedicina  y  {n_pres} que deben ir en persona.")
        if hay_ahorro and total_dinero > 0:
            resumen += (f"\nLos pacientes de fuera de Popayan se ahorrarian "
                        + f"{total_km:,}".replace(",", ".")
                        + f" km, {total_horas} horas y " + pesos(total_dinero)
                        + " en una semana.")
        else:
            resumen += "\n(Este archivo no tiene municipios reconocidos; no se " \
                       "calcula el ahorro de transporte.)"
        self.lbl_resumen.configure(text=resumen)

        # ---- pintar clasificacion ----
        self._pintar_clasif()

        # ---- pintar estadisticas economicas ----
        self.eco["tele"].configure(text=str(n_aptas))
        self.eco["sem"].configure(text=pesos(valor_sem))
        self.eco["anio"].configure(text=pesos(valor_anio))
        pct_cob = (aptas_fuera / n_aptas * 100) if (hay_ahorro and n_aptas) else 0
        self.eco["cob"].configure(
            text=(f"{pct_cob:.0f}%" if hay_ahorro else "-"))
        self.lbl_eco.configure(text=(
            f"Estimacion: {n_aptas} teleconsultas x {pesos(VALOR_CONSULTA)} por "
            f"consulta = {pesos(valor_sem)} en la semana.  "
            f"El 'valor por consulta' es ajustable (confirmar con el hospital)."))
        self._pintar_estadisticas(citas)

        # ---- alerta de oportunidad + impacto ambiental ----
        self._pintar_alerta(citas, hay_ahorro)
        if hay_ahorro and total_km > 0:
            co2 = total_km * CO2_POR_KM
            arboles = int(co2 / 21)   # un arbol absorbe ~21 kg CO2 al año
            self.lbl_ambiental.configure(text=(
                f"🌱 Al evitar {total_km:,}".replace(",", ".")
                + f" km de viajes se dejan de emitir cerca de "
                + f"{int(co2):,}".replace(",", ".")
                + f" kg de CO₂ en la semana (lo que absorben unos {arboles} "
                  "árboles en un año)."))
        else:
            self.lbl_ambiental.configure(text="")

        # ---- graficas dentro de la app ----
        self._pintar_graficas()

        # ---- pintar ahorro por municipio ----
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        if hay_ahorro and por_muni is not None and len(por_muni) > 0:
            self.aviso_muni.configure(
                text="Doble clic en un municipio para ver sus pacientes y citas")
            for i, (muni, r) in enumerate(por_muni.iterrows()):
                tag = "par" if i % 2 == 0 else "impar"
                self.tabla.insert("", "end", tags=(tag,), values=(
                    muni, int(r["citas"]), f"{int(r['km']):,}".replace(",", "."),
                    int(r["horas"]), pesos(r["dinero"])))
        else:
            self.aviso_muni.configure(
                text="Este archivo no tiene municipios reconocidos; el ahorro no "
                     "se calcula. La pestana 1 (Clasificacion) si funciona.")

        self.lbl_archivo.configure(text="Archivo: " + os.path.basename(ruta))

    # -----------------------------------------------------------------
    def _set_filtro(self, valor):
        self.modo_clasif = valor
        self._pintar_clasif()

    def _set_filtro_esp(self, valor):
        self.filtro_esp = valor
        self._pintar_clasif()

    def _set_filtro_muni(self, valor):
        self.filtro_muni = valor
        self._pintar_clasif()

    def _poblar_filtros(self, citas):
        """Llena los menus de especialidad y municipio con lo que trae el
        archivo, y reinicia los filtros a 'Todas/Todos'."""
        self.filtro_esp = "Todas"
        self.filtro_muni = "Todos"
        if "especialidad" in citas.columns:
            esps = sorted(str(e).title() for e in citas["especialidad"].dropna()
                          .unique())
            self.opt_esp.configure(values=["Todas"] + esps)
        else:
            self.opt_esp.configure(values=["Todas"])
        self.opt_esp.set("Todas")
        if "municipio" in citas.columns:
            munis = sorted(str(m) for m in citas["municipio"].dropna().unique())
            self.opt_muni.configure(values=["Todos"] + munis)
        else:
            self.opt_muni.configure(values=["Todos"])
        self.opt_muni.set("Todos")

    def _config_clasif_cols(self):
        """Arma las columnas de la tabla de Clasificacion segun el archivo:
        si trae Nombre y/o Documento, los agrega para poder buscar y llevar
        registro. El anonimizado muestra el codigo."""
        cols, enc, anchos, src = [], {}, {}, {}
        if self.col_nombre:
            cols.append("nombre"); enc["nombre"] = "Paciente"
            anchos["nombre"] = 190; src["nombre"] = self.col_nombre
        if "paciente_cod" in self.citas_full.columns:
            cols.append("cod"); enc["cod"] = "Cod. paciente"
            anchos["cod"] = 110; src["cod"] = "paciente_cod"
        if self.col_doc:
            cols.append("doc"); enc["doc"] = "Documento"
            anchos["doc"] = 110; src["doc"] = self.col_doc
        for c, t, a, f in [("especialidad", "Especialidad", 230, "especialidad"),
                           ("actividad", "Tipo de cita", 270, "actividad"),
                           ("tele", "Telemedicina", 170, "clasificacion")]:
            cols.append(c); enc[c] = t; anchos[c] = a; src[c] = f

        self.tabla_clasif.configure(columns=cols)
        izq = ("nombre", "doc", "especialidad", "actividad", "tele")
        for c in cols:
            self.tabla_clasif.heading(c, text=enc[c])
            self.tabla_clasif.column(
                c, width=anchos[c], anchor="w" if c in izq else "center")
        self.cols_clasif = cols
        self.clasif_src = src

    def _pintar_clasif(self):
        if self.citas_full is None:
            return
        datos = self.citas_full
        if self.modo_clasif == "✓ Solo telemedicina":
            datos = datos[datos["clasificacion"] == "Apta para telemedicina"]
        elif self.modo_clasif == "Presenciales":
            datos = datos[datos["clasificacion"] == "Necesita ir en persona"]

        # filtros por especialidad y municipio
        if (self.filtro_esp not in ("Todas", "")
                and "especialidad" in datos.columns):
            datos = datos[datos["especialidad"].astype(str).str.title()
                          == self.filtro_esp]
        if (self.filtro_muni not in ("Todos", "")
                and "municipio" in datos.columns):
            datos = datos[datos["municipio"] == self.filtro_muni]

        # filtro del buscador (por nombre o por codigo de paciente)
        texto = self.busqueda.strip().lower()
        if texto:
            def coincide(r):
                cod = str(r.get("paciente_cod", "")).lower()
                nom = (str(r.get(self.col_nombre, "")).lower()
                       if self.col_nombre else "")
                doc = (str(r.get(self.col_doc, "")).lower()
                       if self.col_doc else "")
                return texto in cod or texto in nom or texto in doc
            datos = datos[datos.apply(coincide, axis=1)]

        for f in self.tabla_clasif.get_children():
            self.tabla_clasif.delete(f)
        self._fila_idx = {}
        for idx, r in datos.iterrows():
            apta = r["clasificacion"] == "Apta para telemedicina"
            fila = []
            for c in self.cols_clasif:
                fu = self.clasif_src[c]
                if c == "tele":
                    fila.append("✓ Telemedicina" if apta else "Debe ir en persona")
                elif c == "especialidad":
                    fila.append(str(r.get(fu, "-")).title())
                elif c == "actividad":
                    fila.append(self._limpiar(r.get(fu, "-")))
                else:
                    v = r.get(fu, "-")
                    fila.append("-" if pd.isna(v) else v)
            iid = self.tabla_clasif.insert(
                "", "end", tags=("apta" if apta else "pres",),
                values=tuple(fila))
            self._fila_idx[iid] = idx

    # -----------------------------------------------------------------
    def _buscar(self, evento=None):
        # No repintar en cada tecla (se traba con muchos pacientes):
        # esperamos a que deje de escribir ~350 ms y ahi filtramos.
        self.busqueda = self.entry_buscar.get()
        if self._buscar_job is not None:
            self.after_cancel(self._buscar_job)
        self._buscar_job = self.after(350, self._pintar_clasif)

    def _limpiar_busqueda(self):
        self.entry_buscar.delete(0, "end")
        self.busqueda = ""
        self._pintar_clasif()

    def _limpiar(self, texto):
        t = str(texto).title().replace("Actividad De ", "").replace("Actividad ", "")
        return t.strip()

    def _pintar_estadisticas(self, citas):
        for w in self.scroll_esp.winfo_children():
            w.destroy()
        if "especialidad" not in citas.columns:
            ctk.CTkLabel(self.scroll_esp, text="Este archivo no tiene especialidad.",
                         text_color=GRIS).pack(anchor="w", padx=10, pady=10)
            return
        tmp = citas.copy()
        tmp["_a"] = (tmp["clasificacion"] == "Apta para telemedicina").astype(int)
        g = (tmp.groupby("especialidad").agg(total=("_a", "size"), aptas=("_a", "sum"))
             .sort_values("total", ascending=False).head(14))
        for esp, r in g.iterrows():
            total, aptas = int(r["total"]), int(r["aptas"])
            pct = aptas / total if total else 0
            row = ctk.CTkFrame(self.scroll_esp, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=4)
            nombre = str(esp).title()
            if len(nombre) > 28:
                nombre = nombre[:27] + "…"
            ctk.CTkLabel(row, text=nombre, width=210, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(side="left")
            pb = ctk.CTkProgressBar(row, progress_color=VERDE, height=16,
                                    corner_radius=8)
            pb.set(pct)
            pb.pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkLabel(row, text=f"{aptas}/{total}  ({pct*100:.0f}% aptas)",
                         width=150, anchor="e", text_color=GRIS,
                         font=ctk.CTkFont(size=11)).pack(side="left")

    # -----------------------------------------------------------------
    def _pintar_alerta(self, citas, hay_ahorro):
        """Texto que dice en que municipio y especialidad conviene mas
        impulsar la telemedicina (donde hay mas pacientes aptos de lejos)."""
        partes = []
        if hay_ahorro and self.aptas_df is not None and len(self.aptas_df) > 0:
            top_muni = (self.aptas_df.groupby("municipio").size()
                        .sort_values(ascending=False))
            m = top_muni.index[0]
            partes.append(f"El municipio con mas pacientes aptos de fuera es "
                          f"{str(m).title()} ({int(top_muni.iloc[0])} pacientes).")
        if "especialidad" in citas.columns:
            ap = citas[citas["clasificacion"] == "Apta para telemedicina"]
            if len(ap) > 0:
                top_esp = ap.groupby("especialidad").size().sort_values(
                    ascending=False)
                e = top_esp.index[0]
                partes.append(f"La especialidad con mas citas aptas es "
                              f"{str(e).title()} ({int(top_esp.iloc[0])} citas).")
        if partes:
            self.lbl_alerta.configure(
                text=" ".join(partes) + "  Ahi es donde conviene arrancar o "
                "reforzar la telemedicina.")
        else:
            self.lbl_alerta.configure(
                text="Carga un archivo con municipios y especialidad para ver la "
                     "oportunidad.")

    # -----------------------------------------------------------------
    def _pintar_graficas(self):
        """Dibuja dentro de la app dos graficas: aptas vs presenciales y el
        top de municipios por ahorro."""
        if self._canvas_graf is not None:
            self._canvas_graf.get_tk_widget().destroy()
            self._canvas_graf = None
        if self.resultado is None:
            return
        r = self.resultado
        por_muni = r.get("por_muni")
        tiene_muni = por_muni is not None and len(por_muni) > 0
        fig = Figure(figsize=(9, 2.9), dpi=100)
        fig.patch.set_facecolor("white")

        # Grafica 1: aptas vs presenciales
        ax1 = fig.add_subplot(1, 2, 1) if tiene_muni else fig.add_subplot(1, 1, 1)
        ax1.bar(["Telemedicina", "Presencial"], [r["aptas"], r["presencial"]],
                color=[VERDE, ROJO])
        ax1.set_title("Citas aptas vs presenciales", fontsize=10)
        ax1.tick_params(labelsize=8)
        for i, v in enumerate([r["aptas"], r["presencial"]]):
            ax1.text(i, v, str(v), ha="center", va="bottom", fontsize=8)

        # Grafica 2: top municipios por ahorro
        if tiene_muni:
            top = por_muni.head(6).iloc[::-1]
            nombres = [str(m).title()[:14] for m in top.index]
            ax2 = fig.add_subplot(1, 2, 2)
            ax2.barh(nombres, top["dinero"].values, color=AZUL)
            ax2.set_title("Top municipios por ahorro", fontsize=10)
            ax2.tick_params(labelsize=8)
            ax2.xaxis.set_major_formatter(FuncFormatter(
                lambda x, _: (f"${int(x/1_000_000)}M" if x >= 1_000_000
                              else f"${int(x/1000)}k")))

        fig.tight_layout()
        self._canvas_graf = FigureCanvasTkAgg(fig, master=self.graf_frame)
        self._canvas_graf.draw()
        self._canvas_graf.get_tk_widget().pack(fill="both", expand=True,
                                               padx=6, pady=6)

    # =================================================================
    #  VENTANA DE DETALLE POR MUNICIPIO
    # =================================================================
    def _abrir_detalle(self, evento=None):
        sel = self.tabla.focus()
        if not sel or self.citas_full is None:
            return
        municipio = self.tabla.item(sel, "values")[0]
        datos = self.citas_full[self.citas_full["municipio"] == municipio]
        if len(datos) == 0:
            return
        personales = any([self.col_nombre, self.col_doc, self.col_tel])
        n_aptas = int((datos["clasificacion"] == "Apta para telemedicina").sum())

        win = ctk.CTkToplevel(self)
        win.title("Detalle de " + municipio)
        win.geometry("960x520")
        win.configure(fg_color=FONDO)

        cab = ctk.CTkFrame(win, fg_color=VERDE, corner_radius=0, height=64)
        cab.pack(fill="x")
        cab.pack_propagate(False)
        ctk.CTkLabel(cab, text=municipio, text_color="white",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(
                         anchor="w", padx=18, pady=(10, 0))
        ctk.CTkLabel(cab, text=f"{len(datos)} citas  ·  {n_aptas} aptas  ·  "
                     + ("datos personales (uso interno)" if personales
                        else "datos anonimizados"),
                     text_color="#E8F5F2", font=ctk.CTkFont(size=12)).pack(
                         anchor="w", padx=18)

        cont = ctk.CTkFrame(win, fg_color="transparent")
        cont.pack(fill="both", expand=True, padx=12, pady=12)
        cols, enc, anchos, fuentes = [], {}, {}, {}
        cols.append("cod"); enc["cod"] = "Cod. paciente"; anchos["cod"] = 100
        fuentes["cod"] = "paciente_cod"
        if self.col_nombre:
            cols.append("nom"); enc["nom"] = "Nombre"; anchos["nom"] = 150
            fuentes["nom"] = self.col_nombre
        if self.col_doc:
            cols.append("doc"); enc["doc"] = "Documento"; anchos["doc"] = 100
            fuentes["doc"] = self.col_doc
        if self.col_tel:
            cols.append("tel"); enc["tel"] = "Telefono"; anchos["tel"] = 100
            fuentes["tel"] = self.col_tel
        for c, t, a, f in [("sexo", "Sexo", 60, "sexo"),
                           ("esp", "Especialidad", 150, "especialidad"),
                           ("act", "Tipo de cita", 170, "actividad"),
                           ("tele", "Telemedicina", 150, "clasificacion"),
                           ("fecha", "Fecha", 95, "fecha_cita"),
                           ("dinero", "Ahorro", 95, "dinero")]:
            cols.append(c); enc[c] = t; anchos[c] = a; fuentes[c] = f

        tabla = ttk.Treeview(cont, columns=cols, show="headings")
        izq = ("nom", "esp", "act", "tele")
        for c in cols:
            tabla.heading(c, text=enc[c])
            tabla.column(c, width=anchos[c], anchor="w" if c in izq else "center")
        sb = ttk.Scrollbar(cont, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        tabla.tag_configure("apta", background=VERDE_SU)
        tabla.tag_configure("pres", background=CARD)

        for _, r in datos.iterrows():
            apta = r["clasificacion"] == "Apta para telemedicina"
            fila = []
            for c in cols:
                fu = fuentes[c]
                if c == "dinero":
                    v = r.get("dinero")
                    fila.append(pesos(v) if pd.notna(v) else "-")
                elif c == "tele":
                    fila.append("✓ Apta" if apta else "Debe ir en persona")
                elif c == "fecha":
                    fila.append(str(r.get(fu, "-"))[:10])
                elif c == "esp":
                    fila.append(str(r.get(fu, "-")).title())
                elif c == "act":
                    fila.append(self._limpiar(r.get(fu, "-")))
                else:
                    fila.append(r.get(fu, "-"))
            tabla.insert("", "end", tags=("apta" if apta else "pres",),
                         values=tuple(fila))

        ctk.CTkButton(win, text="Cerrar", command=win.destroy, fg_color=AZUL,
                      hover_color="#142d53", corner_radius=10).pack(pady=(0, 12))

    # =================================================================
    #  FICHA DE UN PACIENTE (doble clic en la pestana Clasificacion)
    # =================================================================
    def _detalle_paciente(self, evento=None):
        sel = self.tabla_clasif.focus()
        if not sel or self.citas_full is None or sel not in self._fila_idx:
            return
        r = self.citas_full.loc[self._fila_idx[sel]]
        apta = r["clasificacion"] == "Apta para telemedicina"

        win = ctk.CTkToplevel(self)
        win.title("Ficha del paciente")
        win.geometry("520x560")
        win.configure(fg_color=FONDO)

        color_cab = VERDE if apta else ROJO
        cab = ctk.CTkFrame(win, fg_color=color_cab, corner_radius=0, height=76)
        cab.pack(fill="x")
        cab.pack_propagate(False)
        ctk.CTkLabel(cab, text=str(r.get("paciente_cod", "Paciente")),
                     text_color="white",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(
                         anchor="w", padx=20, pady=(14, 0))
        ctk.CTkLabel(cab, text=("✓ Apta para telemedicina" if apta
                                else "Debe ir en persona"),
                     text_color="white",
                     font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20)

        cont = ctk.CTkScrollableFrame(win, fg_color=CARD, corner_radius=12)
        cont.pack(fill="both", expand=True, padx=16, pady=16)

        # Que campos mostrar (solo los que existan en el archivo cargado)
        campos = [("Codigo de paciente", r.get("paciente_cod", "-"))]
        if self.col_nombre:
            campos.append(("Nombre", r.get(self.col_nombre, "-")))
        if self.col_doc:
            campos.append(("Documento", r.get(self.col_doc, "-")))
        if self.col_tel:
            campos.append(("Telefono", r.get(self.col_tel, "-")))
        if "sexo" in self.citas_full.columns:
            campos.append(("Sexo", r.get("sexo", "-")))
        if "municipio" in self.citas_full.columns:
            campos.append(("Municipio", r.get("municipio", "-")))
        if "especialidad" in self.citas_full.columns:
            campos.append(("Especialidad", str(r.get("especialidad", "-")).title()))
        campos.append(("Tipo de cita", self._limpiar(r.get("actividad", "-"))))
        if "fecha_cita" in self.citas_full.columns:
            campos.append(("Fecha de la cita", str(r.get("fecha_cita", "-"))[:10]))
        campos.append(("Clasificacion",
                       "Apta para telemedicina" if apta else "Necesita ir en persona"))
        if apta and "dinero" in self.citas_full.columns and pd.notna(r.get("dinero")):
            campos.append(("Ahorro estimado de este paciente", pesos(r.get("dinero"))))

        for etiqueta, valor in campos:
            fila = ctk.CTkFrame(cont, fg_color="transparent")
            fila.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(fila, text=etiqueta, text_color=GRIS, width=200,
                         anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
            ctk.CTkLabel(fila, text=str(valor), text_color=TEXTO, anchor="w",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         wraplength=230, justify="left").pack(
                             side="left", fill="x", expand=True)

        if not any([self.col_nombre, self.col_doc, self.col_tel]):
            ctk.CTkLabel(
                win, text="Este archivo esta anonimizado: no trae nombre, documento "
                          "ni telefono.",
                text_color=GRIS, font=ctk.CTkFont(size=11), wraplength=470,
                justify="left").pack(padx=18, pady=(0, 4))

        ctk.CTkButton(win, text="Cerrar", command=win.destroy, fg_color=AZUL,
                      hover_color="#142d53", corner_radius=10).pack(pady=(0, 12))

    # =================================================================
    #  LISTA DE PACIENTES APTOS PARA LLAMAR Y OFRECER TELEMEDICINA
    # =================================================================
    def _lista_llamar(self):
        if self.citas_full is None:
            messagebox.showinfo("Primero carga un archivo",
                                "Carga un archivo de citas antes de generar la lista.")
            return
        aptos = self.citas_full[
            self.citas_full["clasificacion"] == "Apta para telemedicina"].copy()
        if len(aptos) == 0:
            messagebox.showinfo("Sin pacientes aptos",
                                "No hay citas aptas para telemedicina en este archivo.")
            return

        # ORDENAR POR PRIORIDAD: primero los que viven mas lejos (los que mas
        # se benefician de la telemedicina). Si no hay distancia, queda igual.
        if "km_una_via" in aptos.columns:
            aptos = aptos.sort_values("km_una_via", ascending=False,
                                      na_position="last")

        def prioridad(km):
            if pd.isna(km):
                return "-"
            if km >= 100:
                return "Alta"
            if km >= 40:
                return "Media"
            return "Normal"

        # Armamos la lista solo con las columnas que el archivo tenga
        salida = pd.DataFrame()
        if "km_una_via" in aptos.columns:
            salida["Prioridad"] = aptos["km_una_via"].apply(prioridad)
        if self.col_nombre:
            salida["Paciente"] = aptos[self.col_nombre]
        if "paciente_cod" in aptos.columns:
            salida["Cod. paciente"] = aptos["paciente_cod"]
        if self.col_doc:
            salida["Documento"] = aptos[self.col_doc]
        if self.col_tel:
            salida["Telefono"] = aptos[self.col_tel]
        if "especialidad" in aptos.columns:
            salida["Especialidad"] = aptos["especialidad"].astype(str).str.title()
        if "municipio" in aptos.columns:
            salida["Municipio"] = aptos["municipio"]
        if "km_una_via" in aptos.columns:
            salida["Km a Popayan"] = aptos["km_una_via"]
        if "fecha_cita" in aptos.columns:
            salida["Fecha"] = aptos["fecha_cita"].astype(str).str[:10]
        # columnas en blanco para que el hospital lleve el registro
        salida["Contactado"] = ""
        salida["Acepta telemedicina"] = ""

        ruta = filedialog.asksaveasfilename(
            title="Guardar lista de pacientes para llamar",
            defaultextension=".xlsx", initialfile="pacientes_para_llamar.xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not ruta:
            return
        try:
            salida.to_excel(ruta, index=False)
            msg = (f"Lista de {len(salida)} pacientes aptos para telemedicina "
                   f"guardada en:\n{ruta}")
            if not self.col_tel:
                msg += ("\n\nNota: este archivo esta anonimizado, por eso la lista "
                        "no trae telefonos. En el hospital, con el archivo real, "
                        "la lista saldra con el telefono de cada paciente.")
            messagebox.showinfo("Lista lista", msg)
        except Exception as e:
            messagebox.showerror("No se pudo guardar", str(e))

    # =================================================================
    def _exportar_excel(self):
        if self.resultado is None:
            messagebox.showinfo("Primero carga un archivo",
                                "Carga un archivo de citas antes de exportar.")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar resultados", defaultextension=".xlsx",
            initialfile="resultados_telemedicina.xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not ruta:
            return
        r = self.resultado
        resumen = pd.DataFrame({
            "Indicador": ["Total de citas", "Aptas para telemedicina",
                          "Deben ir en persona", "Kilometros ahorrados",
                          "Horas ahorradas", "Ahorro a pacientes (COP)",
                          "Valor para el hospital / semana (COP)"],
            "Valor": [r["total"], r["aptas"], r["presencial"], r["km"],
                      r["horas"], r["dinero"], r["aptas"] * VALOR_CONSULTA]})
        try:
            with pd.ExcelWriter(ruta) as w:
                resumen.to_excel(w, sheet_name="Resumen", index=False)
                if self.citas_full is not None:
                    cc = [c for c in ["paciente_cod", "sexo", "especialidad",
                                      "actividad", "municipio", "fecha_cita",
                                      "clasificacion"]
                          if c in self.citas_full.columns]
                    self.citas_full[cc].to_excel(w, sheet_name="Clasificacion",
                                                 index=False)
                if r["por_muni"] is not None and len(r["por_muni"]) > 0:
                    r["por_muni"].reset_index().to_excel(
                        w, sheet_name="Por municipio", index=False)
            messagebox.showinfo("Listo", "Resultados guardados en:\n" + ruta)
        except Exception as e:
            messagebox.showerror("No se pudo guardar", str(e))

    # =================================================================
    def _pie(self):
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(pie, text="Desarrollada por Maria Alejandra Lopez",
                     text_color=GRIS, font=ctk.CTkFont(size=11)).pack(side="left")


if __name__ == "__main__":
    app = App()
    app.mainloop()
