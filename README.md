# 🚀 Script de Compresión de Video MP4 con Aceleración Hardware

[![Python](https://img.shields.io/badge/Python-yellow?style=for-the-badge&logo=python&logoColor=white&labelColor=101010)](https://www.python.org)
[![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-Optimized-blue?style=for-the-badge&logo=apple&logoColor=white&labelColor=101010)](https://developer.apple.com/documentation/apple-silicon)
[![HandBrake](https://img.shields.io/badge/HandBrake-CLI-orange?style=for-the-badge&logo=handbrake&logoColor=white&labelColor=101010)](https://handbrake.fr)

Script avanzado de Python diseñado para comprimir múltiples videos utilizando HandBrakeCLI en macOS. **Versión 1.1** incluye optimizaciones específicas para **Apple Silicon (M1, M2, M3, M4)** con doble modo de compresión para máximo rendimiento y flexibilidad.

## ✨ Características Principales

### 🎯 **Doble Modo de Compresión**

- **🖥️ Modo CPU**: Compresión con x264 (CRF 26) - Probado y confiable
- **⚡ Modo GPU**: VideoToolbox H.265 optimizado para Apple Silicon
  - **Hardware decoders habilitados** para pipeline GPU completo
  - **15-30% más rápido** en chips Apple Silicon
  - **Calidad superior** con CRF 19
  - **Optimización de latencia** (max-frame-delay=1)

### 📊 **Rendimiento Optimizado**

- **Alta tasa de compresión**: Reducción del 60-80% del tamaño original
- **Calidad preservada**: Configuraciones probadas para óptima calidad visual
- **Estadísticas completas**: Tiempo, espacio ahorrado y métricas detalladas
- **Sonido de finalización**: Notificación auditiva al completar el proceso

## 🛠️ Instalación y Requisitos

### Requisitos del Sistema

- 🍎 **macOS** (optimizado para Apple Silicon M1/M2/M3/M4)
- 🐍 **Python 3.x**
- 🎬 **HandBrakeCLI** (instalado via Homebrew)

### Instalación Rápida

```bash
# Instalar HandBrakeCLI
brew install handbrake

# Clonar repositorio
git clone https://github.com/CodeGeekR/compress_mp4.git
cd compress-mp4
```

## 🎮 Guía de Uso

### Ejecución del Script

```bash
python3 compress.py
```

### Selección de Modo

El script te presentará un menú interactivo:

```
🎬 Bienvenido al Compresor de Videos v1.1

Selecciona el modo de compresión:
1. 🖥️  CPU Mode (x264) - Estable y confiable
2. ⚡ GPU Mode (VideoToolbox) - Optimizado para Apple Silicon

Ingresa tu opción (1 o 2):
```

### Flujo de Trabajo

1. **Selecciona la carpeta** con tus videos (.mp4, .mov, .avi, .mkv)
2. **Define la carpeta de salida** para videos comprimidos
3. **Elige el modo de compresión** (CPU o GPU)
4. **Confirma la configuración** y ¡deja que el script haga su magia! ✨

## ⚙️ Especificaciones Técnicas

### Modo CPU (x264)

```
Codec: H.264 (x264)
CRF: 26
Preset: very fast
Tune: film
Resolución: Preservada (máx. 1080p)
```

### Modo GPU (VideoToolbox - Apple Silicon)

```
Codec: H.265 (VideoToolbox)
CRF: 19
Preset: speed
Hardware Decoders: Habilitados
Max Frame Delay: 1 (ultra-baja latencia)
Look-ahead: 40 frames
Reference frames: 5
QP Range: 10-30
Resolución: Preservada (máx. 1080p)
```

## 📈 Métricas de Rendimiento

| Característica      | Modo CPU           | Modo GPU (Apple Silicon) |
| ------------------- | ------------------ | ------------------------ |
| **Velocidad**       | Baseline           | **+15-30% más rápido**   |
| **Calidad**         | Excelente (CRF 26) | **Superior (CRF 19)**    |
| **Compresión**      | 60-70%             | **70-80%**               |
| **Uso de Hardware** | Solo CPU           | **CPU + GPU optimizado** |
| **Codec**           | H.264              | **H.265 (HEVC)**         |
| **Compatibilidad**  | Universal          | Apple Silicon nativo     |

## 🎯 Características Avanzadas

### � **Estadísticas Detalladas de Compresión**

<p align="center">
  <img src="https://github.com/CodeGeekR/compress_mp4/blob/main/images/stadists_release_mac.png?raw=true" alt="Estadísticas de Compresión en Consola" width="700">
</p>

### 🗑️ **Gestión Automática de Archivos**

- Archivos originales enviados automáticamente a la papelera
- Nombres de archivo optimizados con sufijo "\_compressed"
- Preservación de metadatos importantes

### ⚡ **Optimizaciones de Productividad**

- Detección automática de tipo de archivo
- Manejo robusto de errores
- Estadísticas en tiempo real
- Opción de apagado automático del Mac al finalizar

## 🤝 Contribuir

¡Contribuciones son bienvenidas! 🚀

### Cómo Contribuir

1. **Fork** este repositorio
2. **Crea** una rama: `git checkout -b feature/nueva-funcionalidad`
3. **Commit** tus cambios: `git commit -m "Añade nueva funcionalidad"`
4. **Push** a la rama: `git push origin feature/nueva-funcionalidad`
5. **Abre** un Pull Request

### Reportar Issues

- 🐛 **Bugs**: Reporta errores con detalles específicos
- 💡 **Ideas**: Sugiere nuevas funcionalidades
- 📖 **Documentación**: Mejoras en la documentación

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **HandBrake Team** por su excelente CLI
- **Apple** por las optimizaciones de VideoToolbox
- **Comunidad Open Source** por el feedback continuo

---

<div align="center">

**¿Te gusta este proyecto?** ⭐ ¡Danos una estrella!

[![GitHub stars](https://img.shields.io/github/stars/CodeGeekR/compress-mp4-hardware-acceleration?style=social)](https://github.com/CodeGeekR/compress-mp4-hardware-acceleration/stargazers)

</div>
