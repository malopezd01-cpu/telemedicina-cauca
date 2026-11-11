# Convertir TelemedicinaCauca en programa de escritorio (Mac)

Esto crea un `TelemedicinaCauca.app` que se abre con doble clic, **sin Python**.

## Antes de empezar
En la **misma carpeta** deben estar estos 4 archivos:
- `app_telemedicina.py`
- `logo_telecauca.png`
- `citas_anonimizado.csv`
- `distancias_municipios.csv`

## Paso 1 — Abrir la terminal (desde Thonny)
En Thonny: menú **Herramientas (Tools) → Abrir shell del sistema…**
(Se abre una ventana negra de Terminal, ya con el Python correcto.)

## Paso 2 — Instalar PyInstaller
Copia y pega esta línea, luego Enter:

```
pip3 install pyinstaller
```

Espera a que termine (dice "Successfully installed...").

## Paso 3 — Ir a la carpeta de la app
Escribe `cd ` (con espacio), **arrastra la carpeta** de la app a la terminal (pega la ruta sola) y Enter. Ejemplo:

```
cd /Users/maria/Desktop/TelemedicinaCauca
```

## Paso 4 — Empaquetar
Copia y pega TODO este bloque de una vez y Enter:

```
pyinstaller --windowed --name "TelemedicinaCauca" \
  --collect-all customtkinter \
  --add-data "logo_telecauca.png:." \
  --add-data "citas_anonimizado.csv:." \
  --add-data "distancias_municipios.csv:." \
  app_telemedicina.py
```

Tarda uno o dos minutos. Cuando termine dice algo como *"Building ... completed successfully"*.

## Paso 5 — Abrir la app
- Se crea una carpeta **`dist`**.
- Dentro está **`TelemedicinaCauca.app`**.
- Doble clic y se abre 🎉
- La primera vez, si Mac dice que es de un desarrollador no identificado: **clic derecho sobre la app → Abrir → Abrir**. (Solo la primera vez.)

## Si algo falla
- Si al abrir la app se cierra sola, cuéntame y la empaquetamos en "modo visible" para ver el error.
- Si dice que falta un módulo (por ejemplo `matplotlib`), agrega al comando del Paso 4:
  `--collect-all matplotlib`
