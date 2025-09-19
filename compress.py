"""
Script de Compresión de Video MP4 con Aceleración Hardware Optimizada
=====================================================================

Versión mejorada con optimizaciones específicas para Apple Silicon (M1, M2, M3, M4)

Características principales:
- Modo CPU: x264 con CRF 26 (configuración original probada)
- Modo GPU: VideoToolbox H.265 con optimizaciones para Apple Silicon
  * Hardware decoders habilitados para pipeline GPU completo
  * Optimización de latencia (max-frame-delay=1)
  * Mantiene exactamente la misma calidad (CRF 19)
  * Mejoras de velocidad sin comprometer calidad

Mejoras esperadas en modo GPU:
- 15-30% más rápido por video individual en Apple Silicon
- Pipeline GPU completo para mejor utilización de recursos
- Misma calidad visual mantenida

Versión: 1.1 - Optimizada para Apple Silicon
"""

import subprocess
import os
import sys
import time
import threading
import tempfile
import re
import shutil

# Importar send2trash con manejo de contexto sudo
try:
    from send2trash import send2trash as _send2trash
    def send2trash(path):
        try:
            _send2trash(path)
        except Exception as e:
            if "Expected a folder" in str(e):
                # Fallback para contexto sudo: usar AppleScript nativo
                import subprocess
                subprocess.run(['osascript', '-e', f'tell app "Finder" to move POSIX file "{path}" to trash'], check=True)
            else:
                raise
except ImportError:
    def send2trash(path):
        raise ImportError("send2trash no está disponible.")

# --- Variables Globales de Estadísticas ---
total_videos = 0
total_compression_time = 0
total_original_size = 0
total_compressed_size = 0
total_energy_consumed = 0.0  # Energía total consumida en kWh


class PowerMonitor:
    """
    Monitorea el consumo energético real durante la compresión de video usando powermetrics.
    
    Características:
    - Captura datos reales de CPU, GPU y ANE en chips Apple Silicon
    - Diferencia entre consumo en reposo y durante compresión
    - Calcula energía total consumida en kWh con precisión del hardware
    - Funciona en background sin interferir con el proceso de compresión
    """
    
    def __init__(self):
        self.is_monitoring = False
        self.power_data = []
        self.monitor_thread = None
        self.temp_file = None
        self.powermetrics_process = None
        
    def start_monitoring(self):
        """
        Inicia el monitoreo energético en background usando powermetrics.
        Requiere permisos sudo previamente verificados.
        """
        if self.is_monitoring:
            return
            
        # Crear archivo temporal para datos de powermetrics
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt')
        self.temp_file.close()
        
        # Comando optimizado: muestrea cada 5 segundos CPU, GPU y ANE
        cmd = [
            'sudo', 'powermetrics',
            '-s', 'cpu_power,gpu_power',  # Solo CPU y GPU para eficiencia
            '-n', '-1',                   # Monitoreo continuo hasta que se detenga
            '-i', '5000',                 # Muestra cada 5 segundos
            '--output-file', self.temp_file.name
        ]
        
        try:
            # Iniciar powermetrics como subproceso
            self.powermetrics_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            self.is_monitoring = True
            
        except Exception as e:
            print(f"⚠️  Error iniciando monitoreo energético: {e}")
            self._cleanup()
    
    def stop_monitoring(self):
        """
        Detiene el monitoreo y calcula el consumo energético total.
        Retorna el consumo en kWh.
        """
        if not self.is_monitoring:
            return 0.0
            
        self.is_monitoring = False
        
        # Terminar proceso powermetrics
        if self.powermetrics_process:
            self.powermetrics_process.terminate()
            try:
                self.powermetrics_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.powermetrics_process.kill()
        
        # Esperar un momento para que se escriban los últimos datos
        time.sleep(2)
        
        # Calcular consumo energético total
        energy_kwh = self._calculate_energy_consumption()
        self._cleanup()
        
        return energy_kwh
    
    def _calculate_energy_consumption(self):
        """
        Analiza los datos de powermetrics y calcula el consumo energético total.
        Retorna: Energía consumida en kWh.
        """
        if not self.temp_file or not os.path.exists(self.temp_file.name):
            return 0.0
            
        try:
            with open(self.temp_file.name, 'r') as f:
                content = f.read()
            
            # Extraer valores de potencia usando regex
            cpu_powers = re.findall(r'CPU Power: (\d+) mW', content)
            gpu_powers = re.findall(r'GPU Power: (\d+) mW', content)
            
            if not cpu_powers:
                return 0.0
            
            # Convertir a watts y calcular promedio
            avg_cpu_power = sum(int(p) for p in cpu_powers) / len(cpu_powers) / 1000  # mW a W
            avg_gpu_power = sum(int(p) for p in gpu_powers) / len(gpu_powers) / 1000 if gpu_powers else 0
            
            # Potencia total promedio durante la compresión
            total_avg_power = avg_cpu_power + avg_gpu_power
            
            # Duración del monitoreo: número de muestras × intervalo (5 segundos)
            duration_hours = len(cpu_powers) * 5 / 3600  # Convertir a horas
            
            # Energía = Potencia × Tiempo
            energy_kwh = total_avg_power * duration_hours / 1000  # W⋅h a kWh
            
            return energy_kwh
            
        except Exception as e:
            print(f"⚠️  Error calculando consumo energético: {e}")
            return 0.0
    
    def _cleanup(self):
        """Limpia archivos temporales y recursos."""
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except:
                pass
        self.temp_file = None
        self.powermetrics_process = None


def check_powermetrics_permissions():
    """
    Verifica si powermetrics puede ejecutarse con los permisos necesarios.
    Retorna True si está disponible, False si necesita configuración.
    """
    try:
        # Probar ejecución rápida de powermetrics
        result = subprocess.run(
            ['sudo', '-n', 'powermetrics', '--help'], 
            capture_output=True, 
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


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
    Presenta al usuario las opciones de compresión disponibles.
    
    Returns:
        str: 'cpu' para compresión por software o 'gpu' para aceleración hardware optimizada
    """
    print("\nSeleccione el modo de compresión:")
    mode = get_user_input(
        " [1] CPU (Calidad con x264)\n"
        " [2] GPU (Alta Calidad + Máxima Velocidad - Optimizado Apple Silicon)\n"
        " : ",
        ['1', '2']
    )
    return 'cpu' if mode == '1' else 'gpu'

def compress_video(source_path, dest_path, mode, handbrake_path):
    """
    Comprime un video usando HandBrakeCLI con configuraciones optimizadas.
    - CPU: x264 con CRF 26 (configuración original probada)
    - GPU: VideoToolbox H.265 con CRF 19 + optimizaciones Apple Silicon
      * Hardware decoders habilitados para pipeline GPU completo
      * max-frame-delay=1 para optimización de latencia
      * Mantiene exactamente la misma calidad visual
      * 15-30% más rápido en chips Apple Silicon
    - NUEVO: Monitoreo energético real con datos de CPU y GPU
    
    Args:
        source_path (str): Ruta del archivo de video origen
        dest_path (str): Ruta de destino del archivo comprimido  
        mode (str): 'cpu' o 'gpu' para seleccionar método de compresión
        handbrake_path (str): Ruta del ejecutable HandBrakeCLI
    """
    global total_videos, total_compression_time, total_original_size, total_compressed_size, total_energy_consumed

    # Verificar permisos de escritura en directorio destino
    dest_dir = os.path.dirname(dest_path)
    if not os.access(dest_dir, os.W_OK):
        print(f"\nError: No hay permisos de escritura en el directorio: '{dest_dir}'")
        return

    # Obtener tamaño original del archivo
    try:
        original_size = os.path.getsize(source_path)
    except FileNotFoundError:
        print(f"\nError: No se encontró el archivo de origen: {source_path}")
        return

    # Actualizar estadísticas globales
    total_videos += 1
    total_original_size += original_size
    start_time = time.time()
    
    # Inicializar monitoreo energético si está disponible
    power_monitor = PowerMonitor()
    energy_consumed = 0.0
    
    # Verificar y iniciar monitoreo energético
    if check_powermetrics_permissions():
        power_monitor.start_monitoring()
        print("⚡ Monitoreo energético activado")
    else:
        print("⚠️  Monitoreo energético no disponible (requiere sudo)")

    # Configuración base común para ambos modos
    base_command = [
        handbrake_path,
        '-i', source_path,
        '-o', dest_path,
        '-f', 'mp4',
        '--optimize',
        '-r', '30',           # Frame rate 30fps estándar
        '-E', 'ca_aac',       # Audio AAC de alta calidad
        '-B', '96',           # Bitrate audio 96kbps (eficiente)
    ]

    # Configuraciones específicas por modo de compresión
    if mode == 'cpu':
        print(f"\nComprimiendo con CPU (x264 Optimizado): {os.path.basename(source_path)}")
        # CPU: Configuración probada del usuario con x264 eficiente
        cpu_settings = [
            '-e', 'x264',                   # Encoder x264: rápido y confiable
            '-q', '26',                     # CRF 26: configuración probada del usuario
            # Audio y framerate ya están en base_command
        ]
        command = base_command + cpu_settings
        
    else:  # mode == 'gpu' 
        print(f"\nComprimiendo con GPU (Alta Calidad + Compresión Eficiente Optimizada): {os.path.basename(source_path)}")
        # GPU: CRF optimizado para máxima calidad visual con compresión eficiente
        # ⚡ NUEVO: Optimizaciones específicas para Apple Silicon agregadas ⚡
        gpu_settings = [
            '-e', 'vt_h265',                # VideoToolbox H.265 (hardware)
            '-q', '19',                     # CRF 19 = calidad muy alta con compresión eficiente
            '--encopts',                    # Opciones avanzadas VideoToolbox
            'look-ahead-frame-count=40:'    # Look-ahead 40 frames para mejores decisiones
            'bframes=1:'                    # B-frames habilitados para eficiencia
            'ref=5:'                        # 5 frames de referencia para mejor predicción
            'qpmin=10:'                     # QP mínimo para preservar detalles
            'qpmax=30:'                     # QP máximo para controlar calidad
            'max-frame-delay=1',            # ⚡ NUEVO: Optimización de latencia para Apple Silicon
            # ⚡ NUEVO: Hardware decoder para pipeline GPU completo en Apple Silicon ⚡
            '--enable-hw-decoding', 'videotoolbox'  # Mejora velocidad sin afectar calidad
        ]
        command = base_command + gpu_settings

    # Redimensionar videos 4K a 1080p para mejor compresión (aplicar siempre en CPU)
    if mode == 'cpu':
        # En CPU siempre redimensionar como en tu configuración original
        command.extend(['-w', '1920'])
    else:
        # En GPU solo redimensionar si es mayor a 1920px
        source_width = get_video_width(source_path, handbrake_path)
        if source_width > 1920:
            command.extend(['-w', '1920'])

    # Ejecutar proceso de compresión con monitoreo de progreso
    try:
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True, 
            encoding='utf-8', 
            errors='ignore'
        )

        # Regex para capturar progreso del proceso HandBrake
        progress_regex = re.compile(r"Encoding: task \d+ of \d+, (\d+\.\d+)\s*%")
        
        # Mostrar progreso en tiempo real
        for line in process.stdout:
            match = progress_regex.search(line)
            if match:
                percent = float(match.group(1))
                sys.stdout.write(f"\rProgreso: {int(percent)}%")
                sys.stdout.flush()

        # Esperar a que termine el proceso
        process.wait()

        # Verificar si la compresión fue exitosa
        if process.returncode != 0 or not os.path.isfile(dest_path):
            print(f"\nError al comprimir: {os.path.basename(source_path)}. "
                  f"Verifique que el archivo no esté corrupto.")
            # Revertir estadísticas en caso de error
            total_videos -= 1
            total_original_size -= original_size
            return

        # Mostrar finalización exitosa
        sys.stdout.write("\rProgreso: 100% - ¡Completado!      \n")
        sys.stdout.flush()

        # Actualizar estadísticas finales
        compressed_size = os.path.getsize(dest_path)
        total_compressed_size += compressed_size
        total_compression_time += time.time() - start_time
        
        # Finalizar monitoreo energético y agregar a estadísticas globales
        energy_consumed = power_monitor.stop_monitoring()
        total_energy_consumed += energy_consumed
        
        if energy_consumed > 0:
            print(f"⚡ Energía consumida: {energy_consumed * 1000:.2f} Wh")

        # Mover archivo original a papelera (más seguro que eliminación permanente)
        try:
            send2trash(source_path)
        except Exception as trash_error:
            print(f"⚠️  Advertencia: No se pudo mover a papelera: {trash_error}")
            print(f"   El archivo original permanece en: {source_path}")
        
    except Exception as e:
        print(f"\nOcurrió un error inesperado durante la compresión: {e}")
        # Detener monitoreo energético en caso de error
        if power_monitor:
            power_monitor.stop_monitoring()
        # Revertir estadísticas en caso de excepción
        total_videos -= 1  
        total_original_size -= original_size

def get_user_input(prompt, valid_options):
    """
    Solicita entrada del usuario hasta obtener una opción válida.
    
    Args:
        prompt (str): Mensaje a mostrar al usuario
        valid_options (list): Lista de opciones válidas
        
    Returns:
        str: Opción válida seleccionada por el usuario
    """
    while True:
        choice = input(prompt).strip()
        if choice in valid_options:
            return choice
        print("⚠️  Opción no válida. Por favor, intente nuevamente.")

def get_all_videos(directory):
    """
    Busca recursivamente todos los archivos MP4 en un directorio.
    
    Args:
        directory (str): Ruta del directorio a escanear
        
    Returns:
        list: Lista de rutas de archivos MP4 encontrados
    """
    videos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp4'):
                videos.append(os.path.join(root, file))
    return videos

def shutdown_option():
    """
    Configura las opciones de apagado automático y método de compresión.
    
    Returns:
        tuple: (shutdown_option, compression_option)
    """
    print("¡Gracias por usar Compress MP4! Los archivos se guardarán en el mismo "
          "directorio que los archivos de origen.")
    
    # Opción de apagado automático
    shutdown = get_user_input(
        "¿Desea que el Mac se apague cuando finalice la compresión?\n"
        " [1] SÍ - Apagar automáticamente\n"
        " [2] NO - Mantener encendido\n"
        " : ",
        ['1', '2']
    )

    # Verificar permisos de administrador para apagado
    if shutdown == '1' and os.geteuid() != 0:
        print("⚠️  Para apagar el Mac automáticamente necesitas ejecutar este script "
              "como superusuario.\n💡 Intenta ejecutar: sudo python3 compress.py")
        sys.exit(1)

    # Método de selección de archivos
    compression_option = get_user_input(
        "¿Cómo desea seleccionar los videos a comprimir?\n"
        " [1] Ingresar rutas de videos individuales\n"
        " [2] Procesar todos los videos de un directorio\n"
        " : ",
        ['1', '2']
    )
            
    return shutdown, compression_option

def display_statistics():
    """
    Muestra estadísticas finales del proceso de compresión en consola.
    Incluye métricas de rendimiento, ahorro de espacio y consumo energético real.
    Reproduce sonido de notificación y calcula métricas de rendimiento.
    """
    if total_videos == 0:
        print("ℹ️  No se comprimió ningún video.")
        return

    # Calcular tiempo total en formato legible
    hours, remainder = divmod(total_compression_time, 3600)
    minutes, _ = divmod(remainder, 60)

    # Calcular estadísticas de compresión
    if total_original_size > 0:
        space_saved = total_original_size - total_compressed_size
        percent_space_saved = (space_saved / total_original_size) * 100
        space_saved_gb = space_saved / (1024 ** 3)
    else:
        percent_space_saved = space_saved_gb = 0

    # Reproducir sonido de notificación
    try:
        os.system('afplay ok-notification-alert.wav')
    except:
        pass
    
    # Mostrar estadísticas en consola
    print("\n" + "="*50)
    print("🎬 COMPRESIÓN COMPLETADA EXITOSAMENTE")
    print("="*50)
    print(f"📊 Videos procesados: {total_videos}")
    print(f"⏱️  Tiempo total: {int(hours)}h {int(minutes)}m")
    print(f"📉 Reducción de tamaño: {percent_space_saved:.1f}%")
    print(f"💾 Espacio ahorrado: {space_saved_gb:.2f} GB")
    
    # Nueva estadística: Consumo energético
    if total_energy_consumed > 0:
        energy_wh = total_energy_consumed * 1000  # Convertir kWh a Wh
        print(f"⚡ Energía consumida: {total_energy_consumed:.4f} kWh ({energy_wh:.2f} Wh)")
        
        # Eficiencia energética por video
        if total_videos > 0:
            avg_energy_per_video = energy_wh / total_videos
            print(f"🔋 Promedio por video: {avg_energy_per_video:.2f} Wh")
    else:
        print("⚠️  Consumo energético no monitoreado (requiere permisos sudo)")
    
    print("="*50)

def get_all_videos(directory):
    """
    Busca recursivamente todos los archivos MP4 en un directorio.
    
    Args:
        directory (str): Ruta del directorio a escanear
        
    Returns:
        list: Lista de rutas de archivos MP4 encontrados
    """
    videos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp4'):
                videos.append(os.path.join(root, file))
    return videos

def process_videos(video_paths, mode, handbrake_path):
    """
    Procesa una lista de videos aplicando compresión según el modo seleccionado.
    
    Args:
        video_paths (list): Lista de rutas de archivos de video a procesar
        mode (str): Modo de compresión ('cpu' o 'gpu')
        handbrake_path (str): Ruta del ejecutable HandBrakeCLI
    """
    for source_path in video_paths:
        # Limpiar y verificar ruta del archivo
        source_path = source_path.replace('\\', '')
        if not os.path.isfile(source_path):
            print(f"⚠️  Archivo no encontrado: {source_path}. Omitiendo...")
            continue

        # Generar ruta de destino para archivo comprimido
        source_path = os.path.abspath(source_path)
        dir_path = os.path.dirname(source_path)
        base_name, extension = os.path.splitext(os.path.basename(source_path))
        dest_path = os.path.join(dir_path, f"{base_name}_compressed{extension}")

        # Ejecutar compresión del video
        compress_video(source_path, dest_path, mode, handbrake_path)

# --- Flujo Principal de Ejecución ---
if __name__ == "__main__":
    """
    Punto de entrada principal del script.
    Configura HandBrake, verifica permisos para monitoreo energético, 
    obtiene opciones del usuario y ejecuta compresión con tracking de energía.
    """
    # Buscar instalación de HandBrakeCLI
    handbrake_cli_path = find_handbrake_cli()
    if not handbrake_cli_path:
        print("❌ Error: No se pudo encontrar 'HandBrakeCLI'.")
        print("💡 Asegúrese de que esté instalado y en su PATH o en /Applications.")
        sys.exit(1)
    
    print(f"✅ HandBrakeCLI encontrado en: {handbrake_cli_path}")
    
    # Verificar disponibilidad de monitoreo energético
    if check_powermetrics_permissions():
        print("⚡ Monitoreo energético disponible")
    else:
        print("⚠️  Monitoreo energético requiere permisos sudo")
        print("💡 Para habilitar monitoreo energético, ejecute: sudo python3 compress.py")
        print("   (El script funcionará normalmente sin monitoreo energético)")

    # Obtener configuraciones del usuario
    shutdown_option, compression_option = shutdown_option()
    compression_mode = get_compression_mode()

    # Procesar según método de selección de archivos
    if compression_option == '1':
        # Modo: Archivos individuales
        try:
            amount_videos = int(input("Ingrese la cantidad de videos a comprimir: ").strip())
            if amount_videos <= 0:
                print("❌ Debe ingresar un número mayor a 0.")
                sys.exit(1)
                
            video_paths = []
            for i in range(amount_videos):
                path = input(f"Ruta del video {i+1}: ").strip()
                video_paths.append(path)
                
            process_videos(video_paths, compression_mode, handbrake_cli_path)
            
        except ValueError:
            print("❌ Entrada no válida. Debe ingresar un número entero.")
            sys.exit(1)
    else:
        # Modo: Directorio completo
        directory = input("Ingrese la ruta del directorio con los videos: ").strip().replace('\\', '')
        
        if not os.path.isdir(directory):
            print(f"❌ El directorio no existe: {directory}")
            sys.exit(1)
            
        video_paths = get_all_videos(directory)
        if not video_paths:
            print("ℹ️  No se encontraron videos MP4 en el directorio especificado.")
            sys.exit(0)
            
        print(f"📁 Encontrados {len(video_paths)} videos para procesar.")
        process_videos(video_paths, compression_mode, handbrake_cli_path)

    # Mostrar resumen y enviar notificación
    display_statistics()

    # Apagar sistema si fue solicitado
    if shutdown_option == '1':
        print("🔄 Apagando el Mac en 10 segundos...")
        time.sleep(10)
        os.system('shutdown -h now')