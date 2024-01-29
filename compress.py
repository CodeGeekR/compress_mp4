import subprocess
import os

def comprimir_video(ruta_origen, ruta_destino):
    """
    Comprime un video usando HandBrakeCLI.

    Parámetros:
    ruta_origen -- Ruta al archivo de video original.
    ruta_destino -- Ruta donde se guardará el video comprimido.
    """

    # Comando para comprimir el video
    comando = ['/Applications/HandBrakeCLI', '-i', ruta_origen, '-o', ruta_destino, '-f', 'mp4', '--optimize', '-e', 'x264', '-q', '25.5', '-r', '30', '-E', 'ca_aac', '-B', '96', '-w', '1920']

    # Ejecuta el comando
    subprocess.run(comando, check=True)

print("¡Bienvenido a Compress MP4, su archivo se guardara en el mismo directorio que el archivo de origen!")
# Solicita la ruta del archivo de origen convirtiendo la ruta en relativa para que acepte espacios en el nombre del archivo o en la ruta del directorio que lo contiene
ruta_origen = input("Ingrese la ruta del archivo de origen: ").strip()

# Obtiene la ruta del directorio del archivo de origen
ruta_directorio = os.path.dirname(ruta_origen)

# Crea la ruta del archivo de destino en el mismo directorio que el archivo de origen
nombre_archivo = os.path.basename(ruta_origen)
nombre_base, extension = os.path.splitext(nombre_archivo)
nombre_archivo_comprimido = f"{nombre_base}_comprimido{extension}"
ruta_destino = os.path.join(ruta_directorio, nombre_archivo_comprimido)

# Uso de la función
comprimir_video(ruta_origen, ruta_destino)