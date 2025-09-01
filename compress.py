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

# Global variables to store compression statistics
total_videos = 0
total_compression_time = 0
total_original_size = 0
total_compressed_size = 0

def find_handbrake_cli():
    """
    Finds the HandBrakeCLI executable.
    Checks the system's PATH first, then checks the default /Applications location.
    """
    path = shutil.which('HandBrakeCLI')
    if path:
        return path

    default_path = '/Applications/HandBrakeCLI'
    if os.path.isfile(default_path):
        return default_path

    return None

def get_compression_mode():
    """
    This function asks the user to select the compression mode.
    """
    print("Seleccione el modo de compresión:")
    while True:
        mode = input(
            "¿Cómo desea realizar el proceso?\n"
            " [1] Solo CPU (Alta Calidad, Más Lento)\n"
            " [2] CPU + GPU (Aceleración por Hardware)\n"
            " [3] Solo GPU (Aceleración por Hardware)\n"
            " : "
        ).strip()
        if mode in ['1', '2', '3']:
            if mode == '1':
                return 'cpu'
            else:
                return 'gpu' # Both 2 and 3 map to GPU acceleration
        else:
            print("Por favor, ingrese 1, 2 o 3.")

def get_all_videos(directory):
    """
    This function takes a directory path as input and returns a list of all video paths in that directory and its subdirectories.
    """
    videos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.mp4')):
                videos.append(os.path.join(root, file))
    return videos

def shutdown_option():
    """
    This function asks the user if they want the Mac to shut down after the compression process is finished.
    """
    print("¡Gracias por usar Compress MP4, sus archivos se guardarán en el mismo directorio que los archivos de origen!")
    while True:
        shutdown = input("¿Desea que el Mac se apague cuando finalice el proceso de compresión? \n [1] SI apagar \n [2] NO apagar \n : ").strip()
        if shutdown in ['1', '2']:
            break
        else:
            print("Por favor, ingrese 1 o 2.")

    if shutdown == '1':
        if os.geteuid() != 0:
            print("Para apagar el Mac debes ejecutar este script como superusuario. Intenta ejecutar el script con 'sudo'.")
            sys.exit()

    while True:
        compression_option = input("¿Cómo desea comprimir los videos? \n [1] Ingresar rutas de videos individuales \n [2] Ingresar ruta de un directorio con videos \n : ").strip()
        if compression_option in ['1', '2']:
            break
        else:
            print("Por favor, ingrese 1 o 2.")
    return shutdown, compression_option

def compress_video(source_path, dest_path, mode, handbrake_path):
    """
    This function compresses a video using HandBrakeCLI, showing progress.
    """
    global total_videos, total_compression_time, total_original_size, total_compressed_size

    # --- Pre-compression Safety Checks ---
    # 1. Check for write permissions in the destination directory
    dest_dir = os.path.dirname(dest_path)
    if not os.access(dest_dir, os.W_OK):
        print(f"\nError: No hay permisos de escritura en el directorio de destino: '{dest_dir}'")
        return

    # 2. Check if source file exists before processing
    try:
        original_size = os.path.getsize(source_path)
    except FileNotFoundError:
        print(f"\nError: No se encontró el archivo de origen en {source_path}")
        return

    total_videos += 1
    total_original_size += original_size
    start_time = time.time()

    encoder = 'x264' if mode == 'cpu' else 'vt_h264'

    print(f"\nComprimiendo con {mode.upper()}: {os.path.basename(source_path)}")

    command = [
        handbrake_path,
        '-i', source_path,
        '-o', dest_path,
        '-f', 'mp4',
        '--optimize',
        '-e', encoder,
        '-q', '26',
        '-r', '30',
        '-E', 'ca_aac',
        '-B', '96',
        '--max-width', '1920'
    ]

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

        if process.returncode != 0:
            print(f"\nError al comprimir el video: {os.path.basename(source_path)}. HandBrakeCLI devolvió el código de error {process.returncode}.")
            return

        sys.stdout.write(f"\rProgreso: 100% - ¡Completado!      \n")
        sys.stdout.flush()

        # --- Post-compression Safety Check ---
        if not os.path.isfile(dest_path):
            print(f"\nError: HandBrakeCLI finalizó pero el archivo de salida no fue encontrado.")
            print(f"Verifique los permisos y el espacio en disco para la ruta: '{dest_path}'")
            # Since the source file was not deleted, we can just stop here.
            # We also don't count this video in the final stats by returning early.
            # To do that, we need to decrement the counter.
            total_videos -= 1
            total_original_size -= original_size
            return

        compressed_size = os.path.getsize(dest_path)
        total_compressed_size += compressed_size
        total_compression_time += time.time() - start_time

        send2trash(source_path)

    except Exception as e:
        print(f"\nOcurrió un error inesperado durante la compresión de {os.path.basename(source_path)}: {e}")

def alert_success():
    """
    This function is executed when the script finishes the compression.
    It generates a success alert sound and sends an email.
    """
    global total_videos, total_compression_time, total_original_size, total_compressed_size

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
        f"La compresión de sus videos se realizó satisfactoriamente. Aquí están las estadísticas de la compresión:\n\n"
        f"Cantidad de videos comprimidos: {total_videos}\n"
        f"Tiempo total de compresión: {int(compression_time_hours)} hr: {int(compression_time_minutes)} min\n"
        f"Porcentaje de compresión: {percent_space_saved:.2f}%\n"
        f"Espacio ahorrado: {space_saved_gb:.2f} GB"
    )

    send_email("Compresión exitosa", email_message, "sammydn7@gmail.com")

def send_email(subject, text, to):
    """
    This function sends an email when the process is finished.
    """
    load_dotenv()
    try:
        response = requests.post(
            "https://api.mailgun.net/v3/mail.colombianmacstore.com.co/messages",
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data={"from": "noreply@mail.colombianmacstore.com.co",
                  "to": [to],
                  "subject": subject,
                  "text": text})
        if response.status_code == 200:
            print("Se envió una confirmación del proceso finalizado al correo electrónico.")
            return True
        else:
            print(f"Error al enviar el correo electrónico. Código de estado: {response.status_code}, Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"Ocurrió un error al enviar el correo electrónico: {e}")
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

# --- Main script execution ---
if __name__ == "__main__":
    handbrake_cli_path = find_handbrake_cli()
    if not handbrake_cli_path:
        print("\nError: No se pudo encontrar 'HandBrakeCLI'.")
        print("Asegúrese de que HandBrakeCLI esté instalado en su PATH o en la carpeta /Applications.")
        sys.exit(1)

    shutdown, compression_option = shutdown_option()
    compression_mode = get_compression_mode()

    if compression_option == '1':
        try:
            amount_videos = int(input("Ingrese la cantidad de videos a comprimir: ").strip())
            video_paths = [
                input(f"Ingrese la ruta del archivo de origen {i+1}: ").strip()
                for i in range(amount_videos)
            ]
            process_videos(video_paths, compression_mode, handbrake_cli_path)
        except ValueError:
            print("Entrada no válida. Por favor, ingrese un número.")
            sys.exit()
    else:
        directory = input("Ingrese la ruta del directorio con los videos: ").strip().replace('\\', '')
        if not os.path.isdir(directory):
            print("El directorio ingresado no existe. Por favor, intente de nuevo.")
            sys.exit()

        video_paths = get_all_videos(directory)
        if not video_paths:
            print("No se encontraron videos en el directorio ingresado. Por favor, intente de nuevo.")
            sys.exit()

        process_videos(video_paths, compression_mode, handbrake_cli_path)

    alert_success()

    if shutdown == '1':
        print("Apagando el Mac...")
        os.system('shutdown -h now')