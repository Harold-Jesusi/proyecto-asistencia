import subprocess
import sys

def ejecutar_comando(comando):
    """Ejecutar comando y mostrar resultado"""
    print(f"Ejecutando: {comando}")
    resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
    
    if resultado.returncode == 0:
        print(f"✅ {comando} - EXITOSO")
        return True
    else:
        print(f"❌ {comando} - FALLADO")
        print(f"   Error: {resultado.stderr}")
        return False

def main():
    print("🔧 INSTALADOR DE DEPENDENCIAS PARA RECONOCIMIENTO FACIAL")
    print("=" * 60)
    
    # Lista de comandos de instalación
    comandos = [
        "pip install --upgrade pip",
        "pip install cmake",
        "pip install dlib",
        "pip install git+https://github.com/ageitgey/face_recognition_models",
        "pip install face_recognition",
        "pip install opencv-python",
        "pip install numpy",
        "pip install pillow"
    ]
    
    exitosos = 0
    for comando in comandos:
        if ejecutar_comando(comando):
            exitosos += 1
    
    print(f"\n📊 Resumen: {exitosos}/{len(comandos)} instalaciones exitosas")
    
    if exitosos == len(comandos):
        print("🎉 ¡Todas las dependencias se instalaron correctamente!")
        print("🚀 Ahora puedes ejecutar: python prueba_corregida.py")
    else:
        print("⚠️ Algunas instalaciones fallaron. Revisa los errores.")

if __name__ == "__main__":
    main()