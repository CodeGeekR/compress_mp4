import subprocess
import os
import sys
from dotenv import load_dotenv
import requests
import send2trash
import time

# Variables globales para almacenar las estadísticas de compresión
total_videos = 0
total_compression_time = 0
total_original_size = 0
total_compressed_size = 0

def get_all_videos(directory):
    """
    Esta función toma una ruta de directorio como entrada y devuelve una lista de todas las rutas de video en ese directorio y sus subdirectorios.
    """
    # Lista para almacenar las rutas de los videos
    videos = []

    # Recorre todos los archivos en el directorio y sus subdirectorios
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Si el archivo es un video, añade su ruta a la lista
            if file.endswith(('.mp4', '.avi', '.mkv', '.flv', '.mov')):
                videos.append(os.path.join(root, file))

    return videos


def shutdown_option():
    """
    Esta función pregunta al usuario si desea que el Mac se apague cuando finalice el proceso de compresión.
    """
    print("¡Gracias por usar Compress MP4, sus archivos se guardarán en el mismo directorio que los archivos de origen!")

    # Pregunta al usuario si desea que el Mac se apague al finalizar la compresión
    shutdown = input("¿Desea que el Mac se apague cuando finalice el proceso de compresión? \n [1] SI apagar \n [2] NO apagar \n : ").strip()

    # Si el usuario eligió apagar el Mac, verifica si el script se está ejecutando con permisos de superusuario
    if shutdown == '1':
        if os.geteuid() != 0:
            print("Para apagar el Mac debes ejecutar este script como superusuario. Intenta ejecutar el script con 'sudo'.")
            sys.exit()

    # Pregunta al usuario si desea comprimir videos individuales o todos los videos en un directorio
    compression_option = input("¿Cómo desea comprimir los videos? \n [1] Ingresar rutas de videos individuales \n [2] Ingresar ruta de un directorio con videos \n : ").strip()

    return shutdown, compression_option

# Llama a la función de opción de apagado al inicio del script y guarda la elección del usuario
shutdown, compression_option = shutdown_option()

def comprimir_video(ruta_origen, ruta_destino):
    """
    Esta función comprime Multiples videos usando HandBrakeCLI.

    Parámetros:
    ruta_origen -- Ruta al archivo de video original.
    ruta_destino -- Ruta donde se guardará el video comprimido, es la misma de Origen.
    """
    
    global total_videos
    global total_compression_time
    global total_original_size
    global total_compressed_size

    # Incrementa el total de videos
    total_videos += 1

    # Reemplaza las barras invertidas en las rutas de los archivos
    ruta_origen = ruta_origen.replace('\\', '')
    ruta_destino = ruta_destino.replace('\\', '')
    
    # Obtiene el tamaño del video antes de la compresión
    original_size = os.path.getsize(ruta_origen)
    total_original_size += original_size

    # Registra el tiempo de inicio de la compresión
    start_time = time.time()

    # Comando para comprimir el video
    comando = ['/Applications/HandBrakeCLI', '-i', f'"{ruta_origen}"', '-o', f'"{ruta_destino}"', '-f', 'mp4', '--optimize', '-e', 'x264', '-q', '25.5', '-r', '30', '-E', 'ca_aac', '-B', '96', '-w', '1920']

    # Ejecuta el comando
    subprocess.run(' '.join(comando), shell=True)
    
    # Obtiene el tamaño del video después de la compresión
    compressed_size = os.path.getsize(ruta_destino)
    total_compressed_size += compressed_size

    # Calcula el tiempo que tomó la compresión en segundos
    compression_time_seconds = time.time() - start_time
    total_compression_time += compression_time_seconds
    
    # Mueve el archivo original a la papelera
    send2trash.send2trash(ruta_origen)

def alert_success():
    """
    Esta función se ejecuta cuando el script finaliza la compresión.
    Genera un sonido de alerta en caso de éxito y envía un correo electrónico.
    """
    global total_videos
    global total_compression_time
    global total_original_size
    global total_compressed_size

    # Convierte el tiempo de compresión a horas y minutos
    compression_time_minutes, compression_time_seconds = divmod(total_compression_time, 60)
    compression_time_hours, compression_time_minutes = divmod(compression_time_minutes, 60)

    # Calcula el porcentaje de espacio ganado y el espacio ganado en GB
    space_saved = total_original_size - total_compressed_size
    percent_space_saved = (space_saved / total_original_size) * 100
    space_saved_gb = space_saved / (1024 ** 3)
    
    # Genera un sonido de alerta en caso de éxito
    os.system('afplay ok-notification-alert.wav')
    
    # Prepara el mensaje del correo electrónico
    email_message = (
        f"La compresión de sus videos se realizó satisfactoriamente. Aquí están las estadísticas de la compresión:\n\n"
        f"Cantidad de videos comprimidos: {total_videos}\n"
        f"Tiempo total de compresión: {int(compression_time_hours)} hr: {int(compression_time_minutes)} min\n"
        f"Porcentaje de compresión: {percent_space_saved:.2f}%\n"
        f"Espacio ganado: {space_saved_gb:.2f} GB"
    )

    # Envía el correo electrónico
    send_email("Compresión exitosa", email_message, "SUCORREO@gmail.com")

def send_email(subject, text, to):
    """
    Esta función se ejecuta para enviar un correo electrónico al finalizar el proceso.

    Parámetros:
    subject -- Asunto del correo electrónico.
    text -- Texto del correo electrónico.
    to -- Destinatario del correo electrónico.
    """
    # Carga las variables de entorno del archivo .env
    load_dotenv()

    # Hacemos una solicitud POST a la API de Mailgun
    response = requests.post(
        # La URL de la API de Mailgun para enviar correos electrónicos
        "https://api.mailgun.net/v3/mail.SUDOMINIO.com.co/messages",
        # Usamos la autenticación básica de HTTP con la clave API de Mailgun
        auth=("api", os.getenv("MAILGUN_API_KEY")),
        # Los datos del correo electrónico
        data={"from": "noreply@mail.SUDOMINIO.com.co",
            "to": [to],
            "subject": subject,
            "text": text})

    # Devuelve True si el correo electrónico fue enviado con éxito, False en caso contrario
    if response.status_code == 200:
        print("Se envio una confirmacion de proceso finalizado al Correo electrónico.")
        return True
    else:
        print("Error al enviar el correo electrónico.")
        return False
    
if compression_option == '1':
    # Solicita la cantidad de videos a comprimir
    cantidad_videos = int(input("Ingrese la cantidad de videos a comprimir: ").strip())

    # Lista para almacenar las rutas de los videos
    rutas_videos = []

    for i in range(cantidad_videos):
        # Solicita la ruta del archivo de origen convirtiendo la ruta en relativa para que acepte espacios en el nombre del archivo o en la ruta del directorio que lo contiene
        ruta_origen = input(f"Ingrese la ruta del archivo de origen {i+1}: ").strip()
        rutas_videos.append(ruta_origen)
              
    # Procesa cada video
    for ruta_origen in rutas_videos:
        # Obtiene la ruta del directorio del archivo de origen
        ruta_directorio = os.path.dirname(ruta_origen)

        # Crea la ruta del archivo de destino en el mismo directorio que el archivo de origen
        nombre_archivo = os.path.basename(ruta_origen)
        nombre_base, extension = os.path.splitext(nombre_archivo)
        nombre_archivo_comprimido = f"{nombre_base}_compressed{extension}"
        ruta_destino = os.path.join(ruta_directorio, nombre_archivo_comprimido)

        # Uso de la función
        comprimir_video(ruta_origen, ruta_destino)
else:
    # Solicita la ruta del directorio con los videos
    directory = input("Ingrese la ruta del directorio con los videos: ").strip()
    
    # Expande la ruta del directorio y reemplaza las secuencias de escape de barra invertida y espacio con un espacio
    directory = directory.replace('\\', '')

    # Verifica si el directorio existe
    if not os.path.isdir(directory):
        print("El directorio ingresado no existe. Por favor, intente de nuevo.")
        sys.exit()

    # Obtiene todas las rutas de los videos en el directorio
    rutas_videos = get_all_videos(directory)

    # Verifica si hay videos en el directorio
    if not rutas_videos:
        print("No se encontraron videos en el directorio ingresado. Por favor, intente de nuevo.")
        sys.exit()

    # Procesa cada video
    for ruta_origen in rutas_videos:
        # Obtiene la ruta del directorio del archivo de origen
        ruta_directorio = os.path.dirname(ruta_origen)

        # Crea la ruta del archivo de destino en el mismo directorio que el archivo de origen
        nombre_archivo = os.path.basename(ruta_origen)
        nombre_base, extension = os.path.splitext(nombre_archivo)
        nombre_archivo_comprimido = f"{nombre_base}_compressed{extension}"
        ruta_destino = os.path.join(ruta_directorio, nombre_archivo_comprimido)

        # Uso de la función
        comprimir_video(ruta_origen, ruta_destino)
    

# Llama a la función de alerta de éxito al finalizar la compresión de todos los videos
alert_success()

# Si el usuario eligió apagar el Mac, lo apaga
if shutdown == '1':
    os.system('shutdown -h now')