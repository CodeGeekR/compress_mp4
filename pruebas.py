from pathlib import Path
import sys

directory = input("Ingrese la ruta del directorio con los videos: ").strip()
# directory = directory.replace('\\', '')  # Elimina las barras invertidas. Funciona en macOS y Linux
directory = directory.replace('\\', '/')  # Reemplaza las barras invertidas por barras normales. Funciona en Windows
directory = Path(directory)

# Verifica si el directorio existe
print(directory.exists())