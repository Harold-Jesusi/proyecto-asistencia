# sistema_asistencias.py (versión mejorada)
import cv2
import face_recognition
import numpy as np
from database import DatabaseManager
from datetime import datetime
import time

class SistemaAsistencias:
    def __init__(self):
        self.db = DatabaseManager()
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.cargar_encodings()
        
        # Mejor control de frames
        self.frame_skip = 2  # Procesar cada 2 frames
        self.frame_count = 0
        
        # Suavizado para detecciones
        self.detection_history = {}
        self.history_length = 5
        
    def cargar_encodings(self):
        """Cargar encodings faciales desde la base de datos"""
        self.known_face_encodings, self.known_face_names, self.known_face_ids = self.db.cargar_encodings_faciales()
        print(f"🔍 Sistema listo con {len(self.known_face_encodings)} encodings de {len(set(self.known_face_ids))} estudiantes")
    
    def procesar_frame_mejorado(self, frame):
        """Procesar frame con mejor detección y suavizado"""
        self.frame_count += 1
        
        # Procesar solo cada X frames para mejor performance
        if self.frame_count % self.frame_skip != 0:
            return [], [], [], []
        
        # Reducir tamaño para procesamiento más rápido
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Usar modelo HOG (más rápido) o CNN (más preciso pero lento)
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        face_ids = []
        confianzas = []
        
        for face_encoding in face_encodings:
            # Comparar con rostros conocidos con tolerancia más estricta
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                best_distance = face_distances[best_match_index]
                
                # Convertir distancia a confianza (0-1)
                confianza = 1 - best_distance
                
                # Umbral más alto para mejor precisión
                if best_distance < 0.5:  # Más estricto que antes
                    name = self.known_face_names[best_match_index]
                    estudiante_id = self.known_face_ids[best_match_index]
                    
                    # Registrar asistencia solo si la confianza es alta
                    if confianza > 0.7:
                        self.registrar_asistencia_unica(estudiante_id, confianza)
                else:
                    name = "Desconocido"
                    estudiante_id = None
                    confianza = best_distance
            else:
                name = "Desconocido"
                estudiante_id = None
                confianza = 0.0
            
            face_names.append(name)
            face_ids.append(estudiante_id)
            confianzas.append(confianza)
        
        # Escalar coordenadas de vuelta al tamaño original
        face_locations = [(top * 2, right * 2, bottom * 2, left * 2) 
                         for (top, right, bottom, left) in face_locations]
        
        # Aplicar suavizado a las detecciones
        face_locations, face_names, face_ids, confianzas = self.aplicar_suavizado(
            face_locations, face_names, face_ids, confianzas
        )
        
        return face_locations, face_names, face_ids, confianzas
    
    def aplicar_suavizado(self, face_locations, face_names, face_ids, confianzas):
        """Aplicar suavizado para reducir parpadeo en detecciones"""
        current_time = time.time()
        
        # Limpiar detecciones antiguas
        to_remove = []
        for key in self.detection_history:
            if current_time - self.detection_history[key]['timestamp'] > 2.0:  # 2 segundos
                to_remove.append(key)
        
        for key in to_remove:
            del self.detection_history[key]
        
        # Actualizar historial con detecciones actuales
        for i, (location, name, face_id, confianza) in enumerate(zip(face_locations, face_names, face_ids, confianzas)):
            if face_id and name != "Desconocido":
                key = f"{face_id}_{i}"
                if key not in self.detection_history:
                    self.detection_history[key] = {
                        'locations': [],
                        'names': [],
                        'confianzas': [],
                        'timestamp': current_time
                    }
                
                self.detection_history[key]['locations'].append(location)
                self.detection_history[key]['names'].append(name)
                self.detection_history[key]['confianzas'].append(confianza)
                
                # Mantener solo el historial reciente
                if len(self.detection_history[key]['locations']) > self.history_length:
                    self.detection_history[key]['locations'].pop(0)
                    self.detection_history[key]['names'].pop(0)
                    self.detection_history[key]['confianzas'].pop(0)
        
        # Si no hay detecciones actuales pero hay historial, usar el historial
        if len(face_locations) == 0 and len(self.detection_history) > 0:
            for key, history in self.detection_history.items():
                if len(history['locations']) > 0:
                    # Usar la última ubicación conocida
                    avg_location = history['locations'][-1]
                    avg_name = max(set(history['names']), key=history['names'].count)
                    avg_confianza = np.mean(history['confianzas'])
                    
                    face_id = int(key.split('_')[0]) if '_' in key else None
                    
                    face_locations.append(avg_location)
                    face_names.append(avg_name)
                    face_ids.append(face_id)
                    confianzas.append(avg_confianza)
        
        return face_locations, face_names, face_ids, confianzas
    
    def dibujar_resultados_mejorados(self, frame, face_locations, face_names, confianzas):
        """Dibujar resultados mejorados en el frame"""
        for (top, right, bottom, left), name, confianza in zip(face_locations, face_names, confianzas):
            if name == "Desconocido":
                color = (0, 0, 255)  # Rojo para desconocidos
                texto_confianza = f"{confianza:.2f}"
            else:
                if confianza > 0.8:
                    color = (0, 255, 0)  # Verde para alta confianza
                elif confianza > 0.6:
                    color = (0, 255, 255)  # Amarillo para confianza media
                else:
                    color = (0, 165, 255)  # Naranja para confianza baja
                texto_confianza = f"{confianza:.2f}"
            
            # Dibujar rectángulo más grueso
            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            
            # Dibujar etiqueta con fondo
            label_height = 30
            cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), color, cv2.FILLED)
            
            font = cv2.FONT_HERSHEY_DUPLEX
            texto = f"{name} ({texto_confianza})"
            cv2.putText(frame, texto, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)
        
        # Mostrar estadísticas mejoradas
        rostros_totales = len(face_locations)
        rostros_reconocidos = sum(1 for name in face_names if name != "Desconocido")
        
        cv2.putText(frame, f"Estudiantes: {rostros_reconocidos}/{rostros_totales}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(frame, f"FPS: {self.calcular_fps()}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.putText(frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                   (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def calcular_fps(self):
        """Calcular FPS aproximado"""
        if not hasattr(self, 'last_time'):
            self.last_time = time.time()
            self.fps = 0
            return self.fps
        
        current_time = time.time()
        self.fps = 1 / (current_time - self.last_time)
        self.last_time = current_time
        return int(self.fps)
    
    def iniciar_monitoreo_mejorado(self):
        """Iniciar el sistema de monitoreo mejorado"""
        print("🚀 INICIANDO SISTEMA DE ASISTENCIAS MEJORADO")
        print("Presiona 'q' para salir")
        print("Presiona 'r' para recargar encodings")
        print("Presiona 'f' para cambiar modo de detección")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No se puede acceder a la cámara")
            return
        
        # Configurar cámara para mejor performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Error al capturar frame")
                    break
                
                # Procesar frame mejorado
                face_locations, face_names, face_ids, confianzas = self.procesar_frame_mejorado(frame)
                
                # Dibujar resultados mejorados
                frame = self.dibujar_resultados_mejorados(frame, face_locations, face_names, confianzas)
                
                # Mostrar frame
                cv2.imshow('Sistema de Asistencias - Reconocimiento Facial MEJORADO', frame)
                
                # Controles
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.cargar_encodings()
                    print("✅ Encodings recargados")
                elif key == ord('f'):
                    self.frame_skip = 1 if self.frame_skip == 2 else 2
                    print(f"✅ Modo frame skip: {self.frame_skip}")
                
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("✅ Sistema de monitoreo detenido")