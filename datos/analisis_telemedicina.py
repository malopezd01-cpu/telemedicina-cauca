# -*- coding: utf-8 -*-
# =====================================================================
#  PROYECTO FINAL - TELEMEDICINA HOSPITAL UNIVERSITARIO SAN JOSE
#  Autora: Maria Alejandra Lopez
#  Que hace: lee las citas del hospital, decide cuales se pueden
#  atender por TELEMEDICINA y calcula cuanto AHORRARIAN los pacientes
#  (transporte, almuerzo y hotel) al no viajar a Popayan.
# =====================================================================

import pandas as pd                 # pandas: para leer y manejar tablas
import matplotlib.pyplot as plt     # matplotlib: para hacer graficas

# ---- PARAMETROS DEL CALCULO (se pueden ajustar) -----------------------
COSTO_KM    = 250     # pasaje intermunicipal aprox. por km (tarifas del Cauca)
VELOCIDAD   = 40      # km por hora (promedio carreteras del Cauca)
URBANO      = 6000    # transporte urbano en Popayan, ida y vuelta, por persona
COMIDA      = 25000   # alimentacion del dia: desayuno + almuerzo
JORNAL      = 47450   # dia de trabajo/ingreso perdido = salario minimo 2025
                      # ($1.423.500 / 30 dias) = costo de oportunidad del tiempo
HOTEL       = 70000   # hospedaje una noche en Popayan
KM_HOTEL    = 100     # a mas de estos km (una via) se asume 1 noche de hotel
KM_HOTEL2   = 200     # a mas de estos km se asumen 2 noches
ACOMPANANTE = True    # muchos pacientes viajan con un acompañante

# ---- 1. LEER LOS DATOS -------------------------------------------------
citas = pd.read_csv("citas_anonimizado.csv")
distancias = pd.read_csv("distancias_municipios.csv")
print("Total de citas:", len(citas))

# ---- 2. DECIDIR QUE CITAS SON APTAS PARA TELEMEDICINA ------------------
# Las consultas y controles se pueden hacer por video. Los examenes,
# terapias, imagenes y procedimientos necesitan al paciente presente.
# Miramos la ESPECIALIDAD y tambien el tipo de ACTIVIDAD.
NO_APTAS = ["TERAPIA", "ELECTRO", "RADIOLOG", "RX", "TAC", "RESONANC",
            "ECOCARDIO", "HOLTER", "PROCEDIMIENTO", "IMAGEN",
            "ADMINISTRACION DE MEDICAMENTOS", "ECOGRAF", "CANGURO"]

NO_APTAS_ESP = ["TERAPIA", "REHABILITAC", "MEDICINA FISICA", "RADIOLOG",
                "IMAGEN", "HEMODINAM", "ELECTROESTIMULA", "ELECTROFISIOLOG",
                "LABORATORIO", "PATOLOGIA", "ENDOSCOP", "ECOGRAF"]


def es_apta(actividad, especialidad=""):
    esp = str(especialidad).upper()
    for palabra in NO_APTAS_ESP:
        if palabra in esp:
            return "Necesita ir en persona"
    texto = str(actividad).upper()
    for palabra in NO_APTAS:
        if palabra in texto:
            return "Necesita ir en persona"
    return "Apta para telemedicina"


citas["clasificacion"] = citas.apply(
    lambda r: es_apta(r["actividad"], r.get("especialidad", "")), axis=1)
print(citas["clasificacion"].value_counts())

# ---- 3. UNIR CADA CITA CON LA DISTANCIA DE SU MUNICIPIO ----------------
citas = citas.merge(distancias, on="municipio", how="left")

# ---- 4. CALCULAR EL AHORRO --------------------------------------------
# Solo cuentan las citas APTAS, de pacientes de FUERA de Popayan y con via terrestre
aptas = citas[(citas["clasificacion"] == "Apta para telemedicina") &
              (citas["municipio"] != "POPAYAN") &
              (citas["via_terrestre"] == "si")].copy()

personas = 2 if ACOMPANANTE else 1   # paciente (+ acompañante)
aptas["km_ida_vuelta"] = aptas["km_una_via"] * 2
aptas["horas_viaje"]   = aptas["km_ida_vuelta"] / VELOCIDAD
# Noches de hotel segun que tan lejos queda el municipio
aptas["noches"] = aptas["km_una_via"].apply(
    lambda k: 2 if k >= KM_HOTEL2 else (1 if k >= KM_HOTEL else 0))
# Dinero ahorrado por paciente apto de fuera de Popayan:
#   pasaje intermunicipal + urbano + comida + dia de trabajo perdido + hotel
# Pasajes, comida y dia perdido se multiplican por las personas (con acompañante).
aptas["transporte"] = aptas["km_ida_vuelta"] * COSTO_KM * personas
aptas["urbano"]     = URBANO * personas
aptas["comida"]     = COMIDA * personas
aptas["jornal"]     = (1 + aptas["noches"]) * JORNAL * personas   # dias perdidos
aptas["hotel"]      = aptas["noches"] * HOTEL                     # se comparte
aptas["dinero"] = (aptas["transporte"] + aptas["urbano"]
                   + aptas["comida"] + aptas["jornal"] + aptas["hotel"])

print("\n--- AHORRO POTENCIAL (solo citas aptas, de fuera de Popayan) ---")
print("Citas que se podrian hacer por telemedicina:", len(aptas))
print("Kilometros evitados:", int(aptas["km_ida_vuelta"].sum()), "km")
print("Horas evitadas:", int(aptas["horas_viaje"].sum()), "h")
print("Dinero ahorrado: $", int(aptas["dinero"].sum()), "COP")

# ---- 5. AHORRO POR MUNICIPIO (el mapa de oportunidades) ----------------
por_muni = aptas.groupby("municipio")["dinero"].sum().sort_values(ascending=False)
print("\nTop municipios por ahorro:")
print(por_muni.head(10))

# ---- 6. GRAFICAS ------------------------------------------------------
# Grafica 1: cuantas citas son aptas y cuantas no
plt.figure(figsize=(7, 4))
citas["clasificacion"].value_counts().plot(kind="bar", color=["#2a9d8f", "#e76f51"])
plt.title("Citas aptas para telemedicina vs presencial")
plt.ylabel("Numero de citas")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("grafica_aptas.png", dpi=120)

# Grafica 2: ahorro por municipio (top 10)
plt.figure(figsize=(8, 5))
por_muni.head(10).sort_values().plot(kind="barh", color="#264653")
plt.title("Ahorro potencial por municipio (telemedicina)")
plt.xlabel("Pesos ahorrados")
plt.tight_layout()
plt.savefig("grafica_ahorro_municipio.png", dpi=120)

print("\nListo. Se guardaron dos graficas: grafica_aptas.png y grafica_ahorro_municipio.png")
