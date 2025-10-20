#!/bin/bash

echo "🚀 INSTALADOR PARA UBUNTU - SISTEMA DE ASISTENCIAS"
echo "=============================================="

# Verificar si estamos en Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    echo "❌ Este script es solo para Ubuntu"
    exit 1
fi

echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

echo "📦 Instalando dependencias del sistema..."
sudo apt install -y python3-pip python3-venv cmake build-essential \
    libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev \
    libboost-all-dev libjpeg-dev libpng-dev libtiff-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libcanberra-gtk-module libcanberra-gtk3-module

echo "🐍 Creando entorno virtual..."
python3 -m venv venv_asistencias

echo "🔧 Activando entorno virtual e instalando dependencias Python..."
source venv_asistencias/bin/activate

pip install --upgrade pip
pip install cmake numpy dlib face_recognition opencv-python pillow pandas

echo "✅ Instalación completada!"
echo ""
echo "🚀 Para usar el sistema:"
echo "source venv_asistencias/bin/activate"
echo "python main.py"