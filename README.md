# Script de Compresión de Video MP4

[![Python](https://img.shields.io/badge/Python-yellow?style=for-the-badge&logo=python&logoColor=white&labelColor=101010)](https://www.python.org)

Este script de Python está diseñado para comprimir múltiples videos utilizando HandBrakeCLI en un sistema operativo macOS. El script está optimizado para proporcionar una alta tasa de compresión, reduciendo el tamaño del video significativamente, manteniendo una calidad de video aceptable.

## Características Principales

- **Aceleración por Hardware (GPU)**: Utiliza la potencia de la GPU de los chips Apple Silicon (M1, M2, M3, etc.) para acelerar el proceso de compresión.
- **Menú de Selección de Compresión**: Permite elegir entre compresión por CPU (alta calidad, más lento) o GPU (alta velocidad).
- **Notificaciones por Correo Electrónico**: Envía un resumen con estadísticas de la compresión al finalizar (configurable).
- **Manejo de Errores Mejorado**: El script es robusto y maneja errores comunes como la falta de permisos o la no localización de `HandBrakeCLI`.
- **Barra de Progreso en Tiempo Real**: Muestra el progreso de la compresión de cada video.
- **Función de Apagado**: Opción para apagar el Mac automáticamente al finalizar.
- **Envío a la Papelera**: El video original se envía a la papelera de forma segura después de una compresión exitosa.

<p align="center">
  <img src="https://github.com/CodeGeekR/compress_mp4/blob/main/images/stadists_mail.jpg?raw=true" alt="Estadisticas en e-mail">
</p>

## Requisitos

- macOS
- Python 3
- HandBrakeCLI

## Instalación

1.  **Instalar HandBrakeCLI**:
    Descargue HandBrakeCLI desde el <a href="https://handbrake.fr/downloads2.php" target="_blank">sitio oficial de HandBrake</a>. Asegúrese de que `HandBrakeCLI` esté en su carpeta de `/Applications` o que su ubicación esté incluida en el `PATH` del sistema para que el script pueda encontrarlo.

2.  **Clonar el Repositorio**:
    ```bash
    git clone https://github.com/CodeGeekR/compress_mp4.git
    cd compress_mp4
    ```

3.  **Configurar Entorno Virtual e Instalar Dependencias**:
    ```bash
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    ```

## Configuración de Notificaciones (Opcional)

Para recibir notificaciones por correo electrónico, debe crear un archivo llamado `.env` en la raíz del proyecto.

1.  Cree el archivo `.env`:
    ```bash
    touch .env
    ```
2.  Añada las siguientes variables al archivo `.env` con sus propios valores del servicio Mailgun:
    ```
    MAILGUN_API_KEY="key-yourkeyhere"
    MAILGUN_API_URL="https://api.mailgun.net/v3/your.domain.com/messages"
    MAILGUN_FROM_EMAIL="Compress MP4 <noreply@your.domain.com>"
    MAILGUN_TO_EMAIL="your-email@example.com"
    ```
Si no se configuran estas variables, el script mostrará una advertencia y continuará sin enviar correos electrónicos.

## Uso

1.  Active el entorno virtual (si no está activo):
    ```bash
    source env/bin/activate
    ```

2.  Ejecute el script:
    ```bash
    python3 compress.py
    ```
    El script le guiará a través de las opciones para seleccionar los videos y el modo de compresión. Los videos resultantes se guardarán en el mismo directorio que los archivos de origen con el sufijo `_compressed`.

## Contribuye

¡Te invito a contribuir a este proyecto y hacerlo aún mejor! 😊

Si te gusta este proyecto, no olvides darle una Star ⭐️ en GitHub. Si encuentras algún problema o tienes alguna sugerencia, abre un Issue en el repositorio. Estaré encantado de ayudarte.

Agradecimientos
¡Gracias por tu interés en este proyecto! Esperamos que sea útil. Si tienes alguna pregunta, no dudes en contactarme.
