# main.py (versión mejorada)
from gestion_estudiantes import GestorEstudiantes
from sistema_asistencias import SistemaAsistencias
import os

def mostrar_menu():
    print("\n🎓 SISTEMA DE CONTROL DE ASISTENCIAS ESCOLARES - MEJORADO")
    print("=" * 60)
    print("1. Registrar nuevo estudiante")
    print("2. Listar estudiantes registrados")
    print("3. Verificar estado del sistema")
    print("4. Iniciar monitoreo MEJORADO de asistencias")
    print("5. Salir")
    print("-" * 60)

def main():
    gestor = GestorEstudiantes()
    sistema = None
    
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()
        
        if opcion == '1':
            gestor.registrar_nuevo_estudiante()
        
        elif opcion == '2':
            gestor.listar_estudiantes()
        
        elif opcion == '3':
            gestor.verificar_estado_sistema()
        
        elif opcion == '4':
            if sistema is None:
                sistema = SistemaAsistencias()
            sistema.iniciar_monitoreo_mejorado()
        
        elif opcion == '5':
            print("👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida. Por favor, selecciona 1-5.")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    # Crear estructura de carpetas
    os.makedirs("imagenes_estudiantes", exist_ok=True)
    main()