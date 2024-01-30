import subprocess
import os
import sys
from dotenv import load_dotenv
import requests
import send2trash


def shutdown_option():
    """
    Esta función pregunta al usuario si desea que el Mac se apague cuando finalice el proceso de compresión.
    """
    # Pregunta al usuario si desea que el Mac se apague al finalizar la compresión
    shutdown = input("¿Desea que el Mac se apague cuando finalice el proceso de compresión? \n [1] SI apagar \n [2] NO apagar \n : ").strip()

    # Si el usuario eligió apagar el Mac, verifica si el script se está ejecutando con permisos de superusuario
    if shutdown == '1':
        if os.geteuid() != 0:
            print("Para apagar el Mac al finalizar la compresión, debes ejecutar este script como superusuario. Intenta ejecutar el script con 'sudo'.")
            sys.exit()

    return shutdown

# Llama a la función de opción de apagado al inicio del script y guarda la elección del usuario
shutdown = shutdown_option()

def comprimir_video(ruta_origen, ruta_destino):
    """
    Esta función comprime Multiples videos usando HandBrakeCLI.

    Parámetros:
    ruta_origen -- Ruta al archivo de video original.
    ruta_destino -- Ruta donde se guardará el video comprimido, es la misma de Origen.
    """

    # Reemplaza las barras invertidas en las rutas de los archivos
    ruta_origen = ruta_origen.replace('\\', '')
    ruta_destino = ruta_destino.replace('\\', '')

    # Comando para comprimir el video
    comando = ['/Applications/HandBrakeCLI', '-i', f'"{ruta_origen}"', '-o', f'"{ruta_destino}"', '-f', 'mp4', '--optimize', '-e', 'x264', '-q', '25.5', '-r', '30', '-E', 'ca_aac', '-B', '96', '-w', '1920']

    # Ejecuta el comando
    subprocess.run(' '.join(comando), shell=True)
    
    # Mueve el archivo original a la papelera
    send2trash.send2trash(ruta_origen)

def alert_success():
    """
    Esta función se ejecuta cuando el script finaliza la compresión.
    Genera un sonido de alerta en caso de éxito y envía un correo electrónico.
    """
    # Genera un sonido de alerta en caso de éxito
    os.system('afplay ok-notification-alert.wav')
    # Envía un correo electrónico al finalizar el proceso
    send_email("Compresión exitosa", "La compresión de sus videos se realizó satisfactoriamente.", "SUCORREO@gmail.com")

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
    
print("¡Gracias por usar Compress MP4, sus archivos se guardarán en el mismo directorio que los archivos de origen!")
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
    

# Llama a la función de alerta de éxito al finalizar la compresión de todos los videos
alert_success()

# Si el usuario eligió apagar el Mac, lo apaga
if shutdown == '1':
    os.system('shutdown -h now')