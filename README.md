# Script de Compresión de Video MP4

Este script de Python está diseñado para comprimir múltiples videos utilizando HandBrakeCLI en un sistema operativo macOS. El script está optimizado para proporcionar una alta tasa de compresión, reduciendo el tamaño del video en más del 80% en la mayoría de los casos, manteniendo una calidad de video aceptable. Al finalizar el proceso de compresión de todos los videos, el script notificará con un sonido y enviará un correo electrónico mediante el servicio Mailgun (es necesario configurar las variables de entorno para el servicio Mailgun en un archivo `.env`).

## Requisitos

- macOS
- HandBrakeCLI

## Instalación

Descargue HandBrakeCLI desde el <a href="https://handbrake.fr/downloads2.php" target="_blank">sitio oficial de HandBrake</a>

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

3. Crea un entorno virtual:

   ```bash copyable
   python3 -m venv env
   ```

4. Activa el entorno virtual:
   ```bash copyable
   source env/bin/activate
   ```

5. Instala las dependencias necesarias desde el archivo requirements.txt:
   ```bash copyable
   pip install -r requirements.txt
   ```

6. Ejecuta el script, escribe el número de videos a comprimir y copia la ruta de cada video:

   ```bash copyable
   python compress.py
   ```

El script comprime los videos uno tras otro, utilizando HandBrakeCLI. Solicita la cantidad de videos a comprimir y las rutas de los videos. Los videos comprimidos se guardan en el mismo directorio que los archivos de origen, con un sufijo "_compress" en el nombre del archivo.  El video de salida será un archivo MP4 optimizado, con una tasa de compresión de más del 80%, una resolución de 1080p, una tasa de cuadros de 30 fps, y una tasa de bits de audio de 96 kbps.

## Contribuye

¡Te invito a contribuir a este proyecto y hacerlo aún mejor! 😊

Si te gusta este proyecto, no olvides darle una Star ⭐️ en GitHub.

Si deseas contribuir con código, sigue estos pasos:

Haz un fork de este repositorio.

- Crea una rama con tu nueva funcionalidad: git checkout -b feature/nueva-funcionalidad.
- Realiza tus cambios y realiza commits: git commit -m "Añade nueva funcionalidad".
- Envía tus cambios a tu repositorio remoto: git push origin feature/nueva-funcionalidad.
- Abre un Pull Request en este repositorio principal.

Si encuentras algún problema o tienes alguna sugerencia, abre un Issue en el repositorio. Estaré encantado de ayudarte.

Comparte este proyecto con tus amigos y colegas.

Agradecimientos
¡Gracias por tu interés en este proyecto! Esperamos que sea útil y te diviertas explorando y contribuyendo. Si tienes alguna pregunta, no dudes en contactarme.
