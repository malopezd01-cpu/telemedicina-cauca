# Guía para armar el tablero de Power BI
### Proyecto Telemedicina — Hospital Universitario San José
Autora: María Alejandra López

---

## 1. Importar los datos

1. Abre **Power BI Desktop**.
2. En la pestaña **Inicio**, haz clic en **Obtener datos → Excel**.
3. Busca y abre el archivo **`telemedicina_powerbi.xlsx`**.
4. En la ventana que aparece, marca la hoja (**Sheet1** o **Hoja1**) y haz clic en **Cargar**.

Ya tienes una tabla con una fila por cada cita. Estas son las columnas más importantes:

| Columna | Qué es |
|---|---|
| `Clasificacion` | "Apta para telemedicina" o "Necesita ir en persona" |
| `Apta_flag` | 1 si es apta, 0 si no (sirve para contar) |
| `municipio` | municipio del paciente |
| `especialidad` | especialidad de la cita |
| `De_fuera` | "Si" si el paciente viene de fuera de Popayán |
| `Dinero_ahorrado` | ahorro de ese paciente (ya calculado) |
| `Km_evitados` | kilómetros que se evitan |
| `CO2_kg` | CO₂ que se deja de emitir |
| `Valor_hospital` | lo que el hospital puede facturar por esa cita |

---

## 2. Qué visuales poner (el "tablero de decisión")

El tablero responde dos preguntas: **¿cuánto ayuda la telemedicina?** y **¿dónde conviene crecer?**

### A. Tarjetas de resumen (arriba) — visual "Tarjeta"
- **Total de citas**: cuenta de `cita_id`.
- **% aptas para telemedicina**: promedio de `Apta_flag` (ponlo en formato %).
- **Ahorro total a pacientes**: suma de `Dinero_ahorrado`.
- **CO₂ evitado (kg)**: suma de `CO2_kg`.

### B. Aptas vs presenciales — visual "Gráfico de anillos" o "columnas"
- Leyenda / Eje: `Clasificacion`
- Valores: cuenta de `cita_id`

### C. Ahorro por municipio — visual "Mapa" o "Gráfico de barras"
- Ubicación / Eje: `municipio`
- Valores: suma de `Dinero_ahorrado`
- *(Si usas Mapa, Power BI ubica los municipios del Cauca; si prefieres algo seguro, usa barras horizontales.)*

### D. Aptitud por especialidad — visual "Gráfico de barras"
- Eje: `especialidad`
- Valores: suma de `Apta_flag` (citas aptas por especialidad)
- Ordénalo de mayor a menor. Así ves **en qué especialidades conviene más la telemedicina**.

### E. Segmentadores (filtros) — visual "Segmentación de datos"
- Uno con `especialidad` y otro con `municipio`. Así el profe puede filtrar en vivo.

---

## 3. Qué decir en la sustentación sobre el tablero

- "El tablero muestra **dónde conviene crecer** con telemedicina: los municipios y especialidades con más pacientes aptos."
- "En una semana, la telemedicina le ahorraría a los pacientes del Cauca más de **$65 millones** y evitaría casi **4.000 kg de CO₂**."
- **Honestidad importante:** como el hospital apenas arranca y solo hay **una semana** de datos, todavía no se puede mostrar el "crecimiento mes a mes". Eso se podrá agregar cuando el hospital tenga varios meses. Por ahora el tablero es de **impacto** y **oportunidad**, que es lo más valioso al inicio.

---

## 4. Guardar
Guarda el tablero con **Archivo → Guardar como** → `telemedicina_tablero.pbix`.
Ese `.pbix` es uno de los entregables del proyecto.
