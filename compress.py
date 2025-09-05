import subprocess
import os
import sys
from dotenv import load_dotenv
import requests
import time
import getpass
import glob
from send2trash import send2trash
import re
import shutil

# --- Variables Globales de Estadísticas ---
total_videos = 0
total_compression_time = 0
total_original_size = 0
total_compressed_size = 0

def find_handbrake_cli():
    """
    Busca el ejecutable de HandBrakeCLI de forma inteligente.
    Primero verifica el PATH del sistema, luego la ubicación estándar en /Applications.
    Retorna: La ruta al ejecutable o None si no se encuentra.
    """
    path = shutil.which('HandBrakeCLI')
    if path:
        return path

    default_path = '/Applications/HandBrakeCLI'
    if os.path.isfile(default_path):
        return default_path

    return None

def get_video_width(source_path, handbrake_path):
    """
    Obtiene el ancho de un video usando el escaneo de HandBrakeCLI.
    El escaneo es rápido y no procesa el archivo completo.
    Parámetros:
        source_path (str): La ruta al video de origen.
        handbrake_path (str): La ruta al ejecutable de HandBrakeCLI.
    Retorna: El ancho del video como un entero, o 0 si no se puede determinar.
    """
    try:
        command = [handbrake_path, '-i', source_path, '--scan']
        # HandBrakeCLI imprime la información del escaneo en stderr.
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        size_regex = re.compile(r"\+ size: (\d+)x(\d+)")
        match = size_regex.search(process.stderr)

        if match:
            return int(match.group(1))  # El grupo 1 es el ancho.
    except Exception:
        return 0  # Si algo falla, retornamos 0 para no aplicar redimensión.
    return 0

def get_compression_mode():
    """
    Presenta al usuario las estrategias de compresión y obtiene su elección.
    Retorna: 'cpu' para el modo de máxima calidad, o 'gpu' para el modo de alta velocidad.
    """
    print("\nSeleccione la estrategia de compresión:")
    while True:
        mode = input(
            " [1] Máxima Calidad (CPU, 2-pasadas, lento)\n"
            " [2] Alta Velocidad (GPU, 1-pasada, rápido)\n"
            " : "
        ).strip()
        if mode in ['1', '2']:
            return 'cpu' if mode == '1' else 'gpu'
        else:
            print("Opción no válida. Por favor, ingrese 1 o 2.")

def compress_video(source_path, dest_path, mode, handbrake_path):
    """
    Comprime un video usando HandBrakeCLI con una estrategia optimizada.
    - Modo CPU: Usa 2 pasadas para máxima calidad y eficiencia de compresión.
    - Modo GPU: Usa 1 pasada para máxima velocidad con excelente calidad.
    """
    global total_videos, total_compression_time, total_original_size, total_compressed_size

    dest_dir = os.path.dirname(dest_path)
    if not os.access(dest_dir, os.W_OK):
        print(f"\nError: No hay permisos de escritura en el directorio: '{dest_dir}'")
        return

    try:
        original_size = os.path.getsize(source_path)
    except FileNotFoundError:
        print(f"\nError: No se encontró el archivo de origen: {source_path}")
        return

    total_videos += 1
    total_original_size += original_size
    start_time = time.time()

    # --- Construcción del Comando Base ---
    # Parámetros comunes para ambos modos de compresión.
    command_base = [
        handbrake_path,
        '-i', source_path,
        '-o', dest_path,
        '-f', 'mp4',
        '--optimize',
        '-r', '30',
        '-E', 'ca_aac',
        '-B', '96',
    ]

    # Redimensiona solo si es necesario para no agrandar videos pequeños.
    source_width = get_video_width(source_path, handbrake_path)
    if source_width > 1920:
        command_base.extend(['-w', '1920'])

    # --- Estrategia de Codificación Específica por Modo ---
    if mode == 'cpu':
        print(f"\nComprimiendo con MÁXIMA CALIDAD (CPU): {os.path.basename(source_path)}")
        # Codificación de 2 pasadas con bitrate de 4500 kbps para 1080p.
        command = command_base + ['-e', 'x265', '--multi-pass', '--turbo', '--vb', '4500']
    else: # mode == 'gpu'
        print(f"\nComprimiendo a ALTA VELOCIDAD (GPU): {os.path.basename(source_path)}")
        # Codificación de 1 pasada con un factor de calidad (CRF) de 20 (muy alta calidad).
        command = command_base + ['-e', 'vt_h265', '-q', '20']

    # --- Ejecución y Monitoreo del Proceso ---
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', errors='ignore')

        progress_regex = re.compile(r"Encoding: task \d+ of \d+, (\d+\.\d+)\s*%")
        for line in process.stdout:
            match = progress_regex.search(line)
            if match:
                percent = float(match.group(1))
                sys.stdout.write(f"\rProgreso: {int(percent)}%")
                sys.stdout.flush()

        process.wait()

        if process.returncode != 0 or not os.path.isfile(dest_path):
            print(f"\nError al comprimir: {os.path.basename(source_path)}. Verifique que el archivo no esté corrupto.")
            total_videos -= 1
            total_original_size -= original_size
            return

        sys.stdout.write("\rProgreso: 100% - ¡Completado!      \n")
        sys.stdout.flush()

        compressed_size = os.path.getsize(dest_path)
        total_compressed_size += compressed_size
        total_compression_time += time.time() - start_time

        send2trash(source_path)
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")

def get_all_videos(directory):
    videos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.mp4')):
                videos.append(os.path.join(root, file))
    return videos

def shutdown_option():
    print("¡Gracias por usar Compress MP4, sus archivos se guardarán en el mismo directorio que los archivos de origen!")
    while True:
        shutdown = input("¿Desea que el Mac se apague cuando finalice el proceso de compresión? \n [1] SI apagar \n [2] NO apagar \n : ").strip()
        if shutdown in ['1', '2']:
            break
        else:
            print("Opción no válida. Por favor, ingrese 1 o 2.")

    if shutdown == '1' and os.geteuid() != 0:
        print("Para apagar el Mac debes ejecutar este script como superusuario. Intenta ejecutar el script con 'sudo'.")
        sys.exit()

    while True:
        compression_option = input("¿Cómo desea comprimir los videos? \n [1] Ingresar rutas de videos individuales \n [2] Ingresar ruta de un directorio con videos \n : ").strip()
        if compression_option in ['1', '2']:
            break
        else:
            print("Opción no válida. Por favor, ingrese 1 o 2.")
    return shutdown, compression_option

def alert_success():
    if total_videos == 0:
        print("No se comprimió ningún video.")
        return

    compression_time_minutes, _ = divmod(total_compression_time, 60)
    compression_time_hours, compression_time_minutes = divmod(compression_time_minutes, 60)

    if total_original_size > 0:
        space_saved = total_original_size - total_compressed_size
        percent_space_saved = (space_saved / total_original_size) * 100
        space_saved_gb = space_saved / (1024 ** 3)
    else:
        percent_space_saved = 0
        space_saved_gb = 0

    os.system('afplay ok-notification-alert.wav')
    
    email_message = (
        f"La compresión de sus videos se realizó satisfactoriamente. Aquí están las estadísticas:\n\n"
        f"Videos comprimidos: {total_videos}\n"
        f"Tiempo total: {int(compression_time_hours)} hr: {int(compression_time_minutes)} min\n"
        f"Porcentaje de compresión: {percent_space_saved:.2f}%\n"
        f"Espacio ahorrado: {space_saved_gb:.2f} GB"
    )
    send_email("Compresión exitosa", email_message)

def send_email(subject, text):
    load_dotenv()
    env_vars = ["MAILGUN_API_KEY", "MAILGUN_API_URL", "MAILGUN_FROM_EMAIL", "MAILGUN_TO_EMAIL"]
    if not all(os.getenv(var) for var in env_vars):
        print("\nAdvertencia: Faltan variables de entorno de Mailgun. No se enviará el correo.")
        return False
    try:
        response = requests.post(
            os.getenv("MAILGUN_API_URL"),
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data={"from": os.getenv("MAILGUN_FROM_EMAIL"),
                  "to": [os.getenv("MAILGUN_TO_EMAIL")],
                  "subject": subject,
                  "text": text})
        if response.status_code == 200:
            print("Se envió una confirmación por correo electrónico.")
            return True
        else:
            print(f"Error al enviar correo. Código: {response.status_code}")
            return False
    except Exception as e:
        print(f"Ocurrió un error al enviar el correo: {e}")
        return False

def process_videos(video_paths, mode, handbrake_path):
    for source_path in video_paths:
        source_path = source_path.replace('\\', '')
        if not os.path.isfile(source_path):
            print(f"Archivo no encontrado: {source_path}. Saltando.")
            continue

        source_path = os.path.abspath(source_path)
        dir_path = os.path.dirname(source_path)
        file_name = os.path.basename(source_path)
        base_name, extension = os.path.splitext(file_name)
        compressed_file_name = f"{base_name}_compressed{extension}"
        dest_path = os.path.join(dir_path, compressed_file_name)

        compress_video(source_path, dest_path, mode, handbrake_path)

# --- Flujo Principal de Ejecución ---
if __name__ == "__main__":
    handbrake_cli_path = find_handbrake_cli()
    if not handbrake_cli_path:
        print("\nError: No se pudo encontrar 'HandBrakeCLI'.")
        print("Asegúrese de que esté instalado y en su PATH o en la carpeta /Applications.")
        sys.exit(1)

    shutdown, compression_option = shutdown_option()
    compression_mode = get_compression_mode()

    if compression_option == '1':
        try:
            amount_videos = int(input("Ingrese la cantidad de videos a comprimir: ").strip())
            video_paths = [input(f"Ruta del video {i+1}: ").strip() for i in range(amount_videos)]
            process_videos(video_paths, compression_mode, handbrake_cli_path)
        except ValueError:
            print("Entrada no válida. Por favor, ingrese un número.")
            sys.exit()
    else:
        directory = input("Ingrese la ruta del directorio con los videos: ").strip().replace('\\', '')
        if not os.path.isdir(directory):
            print("El directorio ingresado no existe.")
            sys.exit()
        video_paths = get_all_videos(directory)
        if not video_paths:
            print("No se encontraron videos en el directorio.")
            sys.exit()
        process_videos(video_paths, compression_mode, handbrake_cli_path)

    alert_success()

    if shutdown == '1':
        print("Apagando el Mac...")
        os.system('shutdown -h now')