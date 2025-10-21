# database.py
import sqlite3
import json
import numpy as np
from datetime import datetime
import cv2
import os

class DatabaseManager:
    def __init__(self, db_path='asistencias.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar la base de datos con las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de estudiantes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                edad INTEGER,
                seccion TEXT,
                fecha_registro DATE,
                activo BOOLEAN DEFAULT 1,
                qr_code TEXT UNIQUE
            )
        ''')
        
        # Tabla de encodings faciales (separada para mejor normalización)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encodings_faciales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante_id INTEGER,
                encoding_data BLOB,
                imagen_path TEXT,
                fecha_creacion DATE,
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE
            )
        ''')
        
        # Tabla de asistencias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante_id INTEGER,
                fecha DATE NOT NULL,
                hora TIME NOT NULL,
                metodo_deteccion TEXT CHECK(metodo_deteccion IN ('rostro', 'qr')),
                estado TEXT CHECK(estado IN ('presente', 'tardanza', 'ausente')),
                confianza REAL,
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id)
            )
        ''')
        
        # Tabla de configuración
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                hora_entrada TIME DEFAULT '08:00:00',
                tolerancia_minutos INTEGER DEFAULT 15,
                ultima_actualizacion TIMESTAMP
            )
        ''')
        
        # Insertar configuración por defecto si no existe
        cursor.execute('''
            INSERT OR IGNORE INTO configuracion (id, hora_entrada, tolerancia_minutos, ultima_actualizacion)
            VALUES (1, '08:00:00', 15, CURRENT_TIMESTAMP)
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")
    
    def agregar_estudiante(self, nombre, apellido, edad=None, seccion=None, codigo=None, qr_code=None):
        """Agregar un nuevo estudiante a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Generar código automático si no se proporciona
            if not codigo:
                cursor.execute("SELECT COALESCE(MAX(CAST(codigo AS INTEGER)), 0) FROM estudiantes WHERE codigo GLOB '[0-9]*'")
                max_codigo = cursor.fetchone()[0]
                codigo = str(int(max_codigo) + 1)
            
            cursor.execute('''
                INSERT INTO estudiantes (codigo, nombre, apellido, edad, seccion, fecha_registro, qr_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (codigo, nombre, apellido, edad, seccion, datetime.now().date(), qr_code))
            
            estudiante_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Estudiante {nombre} {apellido} agregado con código: {codigo}")
            return estudiante_id, codigo
            
        except sqlite3.IntegrityError as e:
            print(f"❌ Error: {e}")
            return None, None
        finally:
            conn.close()
    
    def guardar_encoding_facial(self, estudiante_id, encoding):
        """Guardar el encoding facial de un estudiante"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convertir numpy array a bytes
        encoding_bytes = encoding.tobytes()
        
        cursor.execute('''
            INSERT INTO encodings_faciales (estudiante_id, encoding_data, fecha_creacion)
            VALUES (?, ?, ?)
        ''', (estudiante_id, encoding_bytes, datetime.now().date()))
        
        conn.commit()
        conn.close()
        print(f"✅ Encoding facial guardado para estudiante ID: {estudiante_id}")
    
    def cargar_encodings_faciales(self):
        """Cargar todos los encodings faciales de la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.estudiante_id, est.nombre, est.apellido, e.encoding_data
            FROM encodings_faciales e
            JOIN estudiantes est ON e.estudiante_id = est.id
            WHERE est.activo = 1
        ''')
        
        encodings = []
        nombres = []
        ids = []
        
        for row in cursor.fetchall():
            estudiante_id, nombre, apellido, encoding_bytes = row
            # Convertir bytes a numpy array
            encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
            encodings.append(encoding)
            nombres.append(f"{nombre} {apellido}")
            ids.append(estudiante_id)
        
        conn.close()
        print(f"✅ Cargados {len(encodings)} encodings faciales")
        return encodings, nombres, ids
    
    def registrar_asistencia(self, estudiante_id, metodo_deteccion, confianza=1.0):
        """Registrar una asistencia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        ahora = datetime.now()
        fecha = ahora.date()
        hora = ahora.time().strftime('%H:%M:%S')  # CONVERTIR A STRING
        
        # Determinar estado basado en la hora
        cursor.execute('SELECT hora_entrada, tolerancia_minutos FROM configuracion WHERE id = 1')
        config = cursor.fetchone()
        
        if config:
            hora_entrada_str = config[0]
            tolerancia = config[1]
            
            # Convertir hora_entrada a datetime para comparación
            hora_entrada = datetime.strptime(hora_entrada_str, '%H:%M:%S').time()
            
            # Calcular si es tardanza
            hora_actual = ahora.time()
            hora_limite = datetime.combine(ahora.date(), hora_entrada)
            hora_limite = hora_limite.replace(minute=hora_limite.minute + tolerancia)
            
            if ahora > hora_limite:
                estado = 'tardanza'
            else:
                estado = 'presente'
        else:
            estado = 'presente'  # Default si no hay configuración
        
        cursor.execute('''
            INSERT INTO asistencias (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Asistencia registrada: Estudiante {estudiante_id} - {estado}")
        return estado
    
    def obtener_estudiantes(self):
        """Obtener lista de todos los estudiantes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, codigo, nombre, apellido, edad, seccion, fecha_registro
            FROM estudiantes 
            WHERE activo = 1
            ORDER BY nombre, apellido
        ''')
        
        estudiantes = cursor.fetchall()
        conn.close()
        return estudiantes
    
    def buscar_estudiante_por_codigo(self, codigo):
        """Buscar estudiante por código"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, nombre, apellido FROM estudiantes WHERE codigo = ? AND activo = 1', (codigo,))
        estudiante = cursor.fetchone()
        conn.close()
        
        return estudiante
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        