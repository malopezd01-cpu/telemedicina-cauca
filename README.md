# TelemedicinaCauca

Aplicación de escritorio para el área de **telemedicina del Hospital Universitario San José (Popayán)**.

A partir de la base de citas del hospital, la app:

1. **Clasifica** qué pacientes son aptos para atención por telemedicina y cuáles deben ir de forma presencial (el modelo sugiere; el médico decide).
2. **Calcula el ahorro** de cada paciente (kilómetros, tiempo y dinero) al evitar el desplazamiento a Popayán.
3. **Muestra el impacto** económico y ambiental (CO₂ evitado) del programa.

> Proyecto final del Diplomado de Análisis de Datos — Universidad del Cauca.

---

## 📁 Contenido del repositorio

| Carpeta | Qué hay |
|---|---|
| `app/` | La aplicación (`app_telemedicina.py`), el logo y los datos **anonimizados** que necesita. |
| `datos/` | Script de análisis (`analisis_telemedicina.py`) y el dataset para Power BI. |
| `powerbi/` | Guía paso a paso para armar el tablero de decisión. |
| `.github/workflows/` | Automatización que arma el programa `.exe` de Windows en la nube. |

---

## 💻 Descargar el programa (.exe) — sin instalar nada

El `.exe` se construye solo en GitHub cada vez que se actualiza el código.

1. Entra a la pestaña **Actions** (arriba).
2. Abre la última ejecución de *"Construir TelemedicinaCauca (.exe Windows)"* (con ✅ verde).
3. Abajo, en **Artifacts**, descarga **`TelemedicinaCauca-Windows`**.
4. Descomprime el `.zip` → adentro está **`TelemedicinaCauca.exe`**.
5. Doble clic y listo. La primera vez Windows puede decir *"Windows protegió tu PC"* → **Más información → Ejecutar de todas formas**.

Para usarlo, el hospital solo abre el programa y carga su Excel de citas.

---

## ▶️ Correr la app desde el código (opcional, para desarrollo)

```bash
pip install -r requirements.txt
cd app
python app_telemedicina.py
```

---

## 🔒 Privacidad de los datos

- En este repositorio **solo hay datos anonimizados** (sin nombres, cédulas, teléfonos ni diagnósticos).
- El Excel con datos reales de pacientes **se queda únicamente en el computador del hospital** y **nunca** se sube aquí.
- La app puede mostrar datos personales **solo si** el Excel que se carga en ese momento los trae (uso interno del hospital, con autorización).
