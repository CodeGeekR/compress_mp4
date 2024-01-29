import subprocess
import os

def comprimir_video(ruta_origen, ruta_destino):
    """
    Esta función comprime un video usando HandBrakeCLI.

    Parámetros:
    ruta_origen -- Ruta al archivo de video original.
    ruta_destino -- Ruta donde se guardará el video comprimido.
    """

    # Reemplaza las barras invertidas en las rutas de los archivos
    ruta_origen = ruta_origen.replace('\\', '')
    ruta_destino = ruta_destino.replace('\\', '')

    # Comando para comprimir el video
    comando = ['/Applications/HandBrakeCLI', '-i', f'"{ruta_origen}"', '-o', f'"{ruta_destino}"', '-f', 'mp4', '--optimize', '-e', 'x264', '-q', '25.5', '-r', '30', '-E', 'ca_aac', '-B', '96', '-w', '1920']

    # Ejecuta el comando
    subprocess.run(' '.join(comando), shell=True)

print("¡Bienvenido a Compress MP4, sus archivos se guardarán en el mismo directorio que los archivos de origen!")
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
    nombre_archivo_comprimido = f"{nombre_base}_comprimido{extension}"
    ruta_destino = os.path.join(ruta_directorio, nombre_archivo_comprimido)

    # Uso de la función
    comprimir_video(ruta_origen, ruta_destino)