# gestion_estudiantes.py (VERSIÓN CORREGIDA)
import face_recognition
import cv2
import os
import time
from database import DatabaseManager
from datetime import datetime
from camara_utils import capturar_rostros_interactivo

class GestorEstudiantes:
    def __init__(self):
        self.db = DatabaseManager()
        self.carpeta_imagenes = "imagenes_estudiantes"
        os.makedirs(self.carpeta_imagenes, exist_ok=True)
    
    def capturar_multiples_rostros(self, estudiante_id, nombre, apellido, num_capturas=5):
        """Capturar múltiples rostros - VERSIÓN CORREGIDA"""
        print(f"📸 Capturando {num_capturas} imágenes para: {nombre} {apellido}")
        print("Presiona ESPACIO para capturar, ESC para cancelar")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No se puede acceder a la cámara")
            return False
        
        # Configurar la cámara para mejor rendimiento
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        capturas_exitosas = 0
        encodings_guardados = 0
        ultima_captura = time.time()
        
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
                cv2.putText(frame, "ESPACIO: Capturar | ESC: Cancelar", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Detectar rostros en tiempo real
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")  # Usar HOG para más velocidad
                
                # Dibujar rectángulo alrededor del rostro detectado
                for top, right, bottom, left in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, "Rostro detectado - LISTO", (left, top-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                cv2.imshow('Capturar Rostros', frame)
                
                # MEJORA: Usar waitKey más largo y verificar mejor las teclas
                key = cv2.waitKey(100) & 0xFF  # 100ms en lugar de 1ms
                
                if key == 32:  # Tecla ESPACIO
                    if len(face_locations) > 0:
                        # Prevenir capturas demasiado rápidas
                        if time.time() - ultima_captura < 0.5:
                            continue
                            
                        # Guardar imagen
                        filename = f"{self.carpeta_imagenes}/{estudiante_id}_{nombre}_{apellido}_{capturas_exitosas + 1}.jpg"
                        success = cv2.imwrite(filename, frame)
                        
                        if success:
                            # Extraer encoding del rostro
                            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                            if len(face_encodings) > 0:
                                encoding = face_encodings[0]
                                self.db.guardar_encoding_facial(estudiante_id, encoding, filename)
                                encodings_guardados += 1
                                capturas_exitosas += 1
                                ultima_captura = time.time()
                                print(f"✅ Imagen {capturas_exitosas} capturada y guardada")
                                
                                # Pequeña pausa entre capturas
                                time.sleep(0.3)
                            else:
                                print("❌ No se pudo extraer encoding facial")
                        else:
                            print("❌ Error al guardar la imagen")
                    else:
                        print("❌ No se detectó ningún rostro")
                        
                elif key == 27:  # Tecla ESC
                    print("⏹️ Captura cancelada por el usuario")
                    break
                elif key == ord('q'):  # Tecla Q como alternativa
                    print("⏹️ Captura cancelada")
                    break
                    
        except Exception as e:
            print(f"❌ Error durante la captura: {e}")
        finally:
            # Liberar recursos SIEMPRE
            cap.release()
            cv2.destroyAllWindows()
            # Asegurarse de que todas las ventanas se cierren
            for i in range(5):
                cv2.waitKey(1)
        
        print(f"📊 Resumen: {capturas_exitosas}/{num_capturas} capturas exitosas")
        
        return capturas_exitosas > 0
    
    def capturar_fotos_primero(self, nombre, apellido):
        """Primero capturar fotos, luego registrar en BD - VERSIÓN MEJORADA"""
        print(f"🎯 Registrando: {nombre} {apellido}")
        print("Primero capturaremos las fotos, luego el registro en base de datos")
        
        # Crear un ID temporal para las fotos
        temp_id = f"temp_{int(time.time())}"
        
        # Capturar fotos primero usando la nueva función
        if capturar_rostros_interactivo(temp_id, nombre, apellido, self.db, num_capturas=5):
            # Si las fotos se capturaron bien, ahora registrar en BD
            edad = input("Edad (opcional): ").strip()
            seccion = input("Sección (opcional): ").strip()
            codigo = input("Código (opcional, se generará automático): ").strip()
            
            # Convertir edad a entero si se proporciona
            edad_int = int(edad) if edad and edad.isdigit() else None
            
            # Registrar en base de datos
            estudiante_id, codigo_asignado = self.db.agregar_estudiante(
                nombre, apellido, edad_int, seccion, codigo
            )
            
            if estudiante_id:
                print(f"🎯 Código asignado: {codigo_asignado}")
                
                # Actualizar los encodings con el ID real
                self.actualizar_encodings(temp_id, estudiante_id)
                
                print(f"🎉 Estudiante {nombre} {apellido} registrado EXITOSAMENTE!")
                return estudiante_id
            else:
                print("❌ Error al registrar en base de datos")
                return None
        else:
            print("❌ No se capturaron fotos. Registro cancelado.")
            return None
    
    def renombrar_fotos(self, temp_id, estudiante_id, nombre, apellido):
        """Renombrar fotos temporales al ID real"""
        import glob
        try:
            # Buscar todas las fotos temporales
            patron = f"{self.carpeta_imagenes}/{temp_id}_{nombre}_{apellido}_*.jpg"
            fotos_temp = glob.glob(patron)
            
            for foto_vieja in fotos_temp:
                # Extraer el número de la foto
                partes = foto_vieja.split('_')
                numero = partes[-1].replace('.jpg', '')
                
                # Nuevo nombre
                foto_nueva = f"{self.carpeta_imagenes}/{estudiante_id}_{nombre}_{apellido}_{numero}.jpg"
                os.rename(foto_vieja, foto_nueva)
                print(f"✅ Renombrado: {foto_nueva}")
                
        except Exception as e:
            print(f"⚠️ Error renombrando fotos: {e}")
    
    def actualizar_encodings(self, temp_id, estudiante_id):
        """Actualizar encodings con el ID real del estudiante"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE encodings_faciales SET estudiante_id = ? WHERE estudiante_id = ?",
                (estudiante_id, temp_id)
            )
            conn.commit()
            print(f"✅ Encodings actualizados al ID real: {estudiante_id}")
        except Exception as e:
            print(f"⚠️ Error actualizando encodings: {e}")
        finally:
            conn.close()
    
    def eliminar_fotos_temp(self, temp_id):
        """Eliminar fotos temporales si hay error"""
        import glob
        try:
            patron = f"{self.carpeta_imagenes}/{temp_id}_*.jpg"
            fotos_temp = glob.glob(patron)
            
            for foto in fotos_temp:
                os.remove(foto)
                print(f"🗑️ Eliminada foto temporal: {foto}")
                
        except Exception as e:
            print(f"⚠️ Error eliminando fotos temporales: {e}")
    
    def registrar_nuevo_estudiante(self):
        """Registrar nuevo estudiante - VERSIÓN MEJORADA"""
        print("\n📝 REGISTRO DE NUEVO ESTUDIANTE")
        print("=" * 40)
        
        nombre = input("Nombre: ").strip()
        apellido = input("Apellido: ").strip()
        
        if not nombre or not apellido:
            print("❌ Nombre y apellido son obligatorios")
            return None
        
        # PRIMERO capturar fotos, LUEGO datos adicionales
        return self.capturar_fotos_primero(nombre, apellido)

    def listar_estudiantes(self):
        """Listar todos los estudiantes registrados"""
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
        
        estudiantes_con_fotos = len(set(ids)) if ids else 0
        print(f"Estudiantes con rostro registrado: {estudiantes_con_fotos}")
        
        if nombres:
            print("\n👤 Estudiantes con reconocimiento facial:")
            for nombre in set(nombres):
                count = nombres.count(nombre)
                print(f"  - {nombre} ({count} encodings)")