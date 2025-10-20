# gestion_estudiantes.py (versión mejorada)
import face_recognition
import cv2
import os
import time
from database import DatabaseManager
from datetime import datetime

class GestorEstudiantes:
    def __init__(self):
        self.db = DatabaseManager()
        self.carpeta_imagenes = "imagenes_estudiantes"
        os.makedirs(self.carpeta_imagenes, exist_ok=True)
    
    def capturar_multiples_rostros(self, estudiante_id, nombre, apellido, num_capturas=10):
        print(f"📸 Capturando {num_capturas} imágenes para: {nombre} {apellido}")
        print("Presiona ESPACIO para capturar cada imagen, ESC para terminar/cancelar")
        print("Mueve la cabeza ligeramente entre cada captura para mejor entrenamiento")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No se puede acceder a la cámara")
            return False
        
        capturas_exitosas = 0
        encodings_guardados = 0
        
        try:
            while capturas_exitosas < num_capturas:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Error al capturar frame")
                    break
                
                # Mostrar instrucciones
                cv2.putText(frame, f"Capturando: {nombre} {apellido}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Imagen {capturas_exitosas + 1}/{num_capturas}", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, "Mueve la cabeza ligeramente entre capturas", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, "ESPACIO: Capturar | ESC: Terminar", (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Detectar rostros en tiempo real
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                
                # Dibujar rectángulo alrededor del rostro detectado
                for top, right, bottom, left in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, "Rostro detectado - LISTO", (left, top-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                cv2.imshow('Capturar Rostros Múltiples', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 32:  # Tecla ESPACIO
                    if len(face_locations) > 0:
                        # Guardar imagen
                        filename = f"{self.carpeta_imagenes}/{estudiante_id}_{nombre}_{apellido}_{capturas_exitosas + 1}.jpg"
                        cv2.imwrite(filename, frame)
                        
                        # Extraer encoding del rostro
                        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                        if len(face_encodings) > 0:
                            encoding = face_encodings[0]
                            self.db.guardar_encoding_facial(estudiante_id, encoding, filename)
                            encodings_guardados += 1
                            capturas_exitosas += 1
                            print(f"✅ Imagen {capturas_exitosas} capturada y guardada")
                            
                            # Pequeña pausa entre capturas
                            time.sleep(0.3)
                        else:
                            print("❌ No se pudo extraer encoding facial")
                    else:
                        print("❌ No se detectó ningún rostro. Asegúrate de estar frente a la cámara.")
                elif key == 27:  # Tecla ESC
                    print("⏹️  Captura terminada")
                    break
        except Exception as e:
            print(f"❌ Error durante la captura: {e}")
        finally:
            # Liberar recursos
            cap.release()
            cv2.destroyAllWindows()
        
        print(f"✅ Capturas completadas: {capturas_exitosas}/{num_capturas}")
        print(f"✅ Encodings guardados: {encodings_guardados}")
        
        return capturas_exitosas > 0
    
    def registrar_nuevo_estudiante(self):

        """Registrar un nuevo estudiante en el sistema"""
        print("\n📝 REGISTRO DE NUEVO ESTUDIANTE")
        print("=" * 40)
        
        nombre = input("Nombre: ").strip()
        apellido = input("Apellido: ").strip()
        
        if not nombre or not apellido:
            print("❌ Nombre y apellido son obligatorios")
            return None
        
        edad = input("Edad (opcional): ").strip()
        seccion = input("Sección (opcional): ").strip()
        codigo = input("Código (opcional, se generará automático): ").strip()
        
        # Convertir edad a entero si se proporciona
        edad_int = int(edad) if edad and edad.isdigit() else None
        
        # Si el código está vacío, se generará automáticamente
        codigo = codigo if codigo else None
        
        # Agregar a la base de datos
        estudiante_id, codigo_asignado = self.db.agregar_estudiante(
            nombre, apellido, edad_int, seccion, codigo
        )
        
        if estudiante_id:
            print(f"🎯 Código asignado: {codigo_asignado}")
            
            # Capturar múltiples rostros
            if self.capturar_multiples_rostros(estudiante_id, nombre, apellido, num_capturas=10):
                print(f"🎉 Estudiante {nombre} {apellido} registrado exitosamente!")
            else:
                print("⚠️ Estudiante registrado pero sin rostros capturados")
        
        return estudiante_id

    def listar_estudiantes(self):
        estudiantes = self.db.obtener_estudiantes()
    
        print("\n📋 LISTA DE ESTUDIANTES REGISTRADOS")
        print("=" * 60)
        print(f"{'ID':<4} {'Código':<10} {'Nombre':<15} {'Apellido':<15} {'Edad':<4} {'Sección':<10}")
        print("-" * 60)
        
        for est in estudiantes:
            id, codigo, nombre, apellido, edad, seccion, fecha_reg = est
            edad_str = str(edad) if edad else "N/A"
            seccion_str = seccion if seccion else "N/A"
            print(f"{id:<4} {codigo:<10} {nombre:<15} {apellido:<15} {edad_str:<4} {seccion_str:<10}")
        
        print(f"\nTotal: {len(estudiantes)} estudiantes")

    def verificar_estado_sistema(self):
        """Verificar el estado actual del sistema"""
        encodings, nombres, ids = self.db.cargar_encodings_faciales()
        
        print("\n🔍 ESTADO DEL SISTEMA")
        print("=" * 40)
        print(f"Estudiantes registrados: {len(self.db.obtener_estudiantes())}")
        print(f"Encodings faciales cargados: {len(encodings)}")
        print(f"Estudiantes con rostro registrado: {len(set(ids))}")
        
        if len(nombres) > 0:
            print("\n👤 Estudiantes con reconocimiento facial:")
            for nombre in set(nombres):
                count = nombres.count(nombre)
                print(f"  - {nombre} ({count} encodings)")