# Crear el programa de escritorio en Windows (.exe)
### Para la máquina virtual de Windows (la versión del hospital)

Al final te queda un **`TelemedicinaCauca.exe`**: un solo archivo que se abre con doble clic, sin instalar Python.

---

## Paso 0 — Llevar los archivos a Windows
Copia a una carpeta en el Windows (por ejemplo en el Escritorio, llámala `TelemedicinaCauca`) estos 4 archivos:
- `app_telemedicina.py`
- `logo_telecauca.png`
- `citas_anonimizado.csv`
- `distancias_municipios.csv`

*(Los puedes pasar por la carpeta compartida de VMware, por correo, o descargándolos del proyecto.)*

---

## Paso 1 — Instalar Python en Windows
1. Abre el navegador en la VM y entra a **https://www.python.org/downloads/**
2. Descarga **Python** (el botón grande amarillo) e instálalo.
3. ⚠️ **MUY IMPORTANTE:** en la primera pantalla del instalador, marca la casilla **"Add Python to PATH"** (abajo) antes de darle *Install Now*.

---

## Paso 2 — Abrir la consola e instalar los paquetes
1. Menú Inicio → escribe **cmd** → abre **Símbolo del sistema**.
2. Instala todo lo que necesita la app (copia y pega, Enter):

```
pip install pyinstaller customtkinter pandas matplotlib openpyxl pillow
```

Espera a que termine (puede tardar un par de minutos).

---

## Paso 3 — Ir a la carpeta de la app
Escribe `cd ` y la ruta de tu carpeta. Si la pusiste en el Escritorio:

```
cd %USERPROFILE%\Desktop\TelemedicinaCauca
```

---

## Paso 4 — Crear el .exe
Copia y pega esta línea COMPLETA (es una sola línea) y Enter:

```
pyinstaller --noconsole --onefile --name "TelemedicinaCauca" --collect-all customtkinter --add-data "logo_telecauca.png;." --add-data "citas_anonimizado.csv;." --add-data "distancias_municipios.csv;." app_telemedicina.py
```

> Nota: en Windows el separador de `--add-data` es punto y coma `;` (en Mac era `:`). Ya está puesto correcto aquí.

Tarda uno o dos minutos. Cuando termine dice *"completed successfully"*.

---

## Paso 5 — Abrir el programa
- Se crea una carpeta **`dist`**.
- Dentro está **`TelemedicinaCauca.exe`**.
- Doble clic y abre 🎉
- La primera vez Windows (SmartScreen) puede decir "Windows protegió tu PC": clic en **"Más información" → "Ejecutar de todas formas"**.

Ese `.exe` es el que le dejas al hospital. Para usarlo, él solo abre el programa y carga su Excel de citas.

---

## Si algo falla
- Si dice que falta un módulo (ej. `matplotlib`), agrega al comando del Paso 4: `--collect-all matplotlib`
- Si el .exe abre y se cierra solo, quita `--noconsole` del comando y vuelve a empaquetar: así se ve el error en una ventana negra y me lo mandas.
