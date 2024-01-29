# Script de Compresión de Video

Este script de Python está diseñado para comprimir videos utilizando HandBrakeCLI en un sistema operativo macOS. El script está optimizado para proporcionar una alta tasa de compresión, reduciendo el tamaño del video en más del 80% en la mayoría de los casos, manteniendo una calidad de video aceptable.

## Requisitos

- macOS
- HandBrakeCLI

## Instalación

Descargue HandBrakeCLI desde el [sitio oficial de HandBrake](https://handbrake.fr/downloads2.php)

Una vez descargado, copie HandBrakeCLI en su carpeta de Aplicaciones.

## Uso

1. Clona este repositorio en tu máquina local:

   ```bash copyable
   git clone https://github.com/CodeGeekR/compress_mp4.git

   ```

2. Navega hasta el directorio del proyecto en la terminal:

   ```bash copyable
   cd <ruta_carpeta>
   ```

3. Ejecuta el script y arrastra el archivo de video a comprimir

   ```bash copyable
   python compress.py
   ```

El script comprime un video utilizando HandBrakeCLI. Solicita la ruta del video a comprimir y la ruta donde se guardará el video comprimido. El video de salida será un archivo MP4 optimizado, con una tasa de compresión de más del 80%, una resolución de 1920px de ancho, una tasa de cuadros de 30 fps, y una tasa de bits de audio de 96 kbps.
