# app_web.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import sqlite3
import os
import sys


# Agregar el directorio actual al path para importar nuestros módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from gestion_estudiantes import GestorEstudiantes
from sistema_asistencias import SistemaAsistencias

# Configurar la página
st.set_page_config(
    page_title="Sistema de Asistencias Escolares",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🎓 Sistema de Control de Asistencias Escolares")
st.markdown("---")

class InterfazWeb:
    def __init__(self):
        self.db = DatabaseManager()
        self.gestor = GestorEstudiantes()
    
    def mostrar_sidebar(self):
        """Mostrar menú lateral"""
        st.sidebar.title("Navegación")
        
        opcion = st.sidebar.radio(
            "Selecciona una opción:",
            [
                "📊 Dashboard",
                "👥 Gestión de Estudiantes", 
                "📝 Registrar Asistencias",
                "📈 Reportes y Estadísticas",
                "⚙️ Configuración"
            ]
        )
        
        return opcion
    
    def mostrar_dashboard(self):
        """Mostrar dashboard principal"""
        st.header("📊 Dashboard Principal")
        
        # Obtener estadísticas
        total_estudiantes = len(self.db.obtener_estudiantes())
        encodings, nombres, ids = self.db.cargar_encodings_faciales()
        estudiantes_con_rostro = len(set(ids))
        
        hoy = date.today()
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(DISTINCT estudiante_id) 
            FROM asistencias 
            WHERE fecha = ?
        ''', (hoy,))
        asistencias_hoy = cursor.fetchone()[0]
        conn.close()
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Estudiantes", total_estudiantes)
        
        with col2:
            st.metric("Con Rostro Registrado", estudiantes_con_rostro)
        
        with col3:
            st.metric("Asistencias Hoy", asistencias_hoy)
        
        with col4:
            st.metric("Porcentaje Hoy", f"{(asistencias_hoy/total_estudiantes*100 if total_estudiantes > 0 else 0):.1f}%")
        
        # Gráfico de asistencias de la semana
        st.subheader("Asistencias de la Última Semana")
        self.mostrar_grafico_semanal()
        
        # Últimas asistencias
        st.subheader("Últimas Asistencias Registradas")
        self.mostrar_ultimas_asistencias()
    
    def mostrar_grafico_semanal(self):
        """Mostrar gráfico de asistencias de la semana"""
        conn = self.db._get_connection()
        
        # Obtener asistencias de los últimos 7 días
        query = '''
            SELECT fecha, COUNT(DISTINCT estudiante_id) as asistencias
            FROM asistencias 
            WHERE fecha >= date('now', '-7 days')
            GROUP BY fecha
            ORDER BY fecha
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            fig = px.line(
                df, 
                x='fecha', 
                y='asistencias',
                title="Asistencias por Día",
                markers=True
            )
            fig.update_layout(xaxis_title="Fecha", yaxis_title="Número de Asistencias")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de asistencias para mostrar.")
    
    def mostrar_ultimas_asistencias(self):
        """Mostrar tabla de últimas asistencias"""
        conn = self.db._get_connection()
        
        query = '''
            SELECT a.fecha, a.hora, e.nombre, e.apellido, a.estado, a.metodo_deteccion
            FROM asistencias a
            JOIN estudiantes e ON a.estudiante_id = e.id
            ORDER BY a.fecha DESC, a.hora DESC
            LIMIT 10
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            # Mejorar formato de la tabla
            df['Nombre Completo'] = df['nombre'] + ' ' + df['apellido']
            df['Estado'] = df['estado'].map({
                'presente': '✅ Presente',
                'tardanza': '⚠️ Tardanza', 
                'ausente': '❌ Ausente'
            })
            
            st.dataframe(
                df[['fecha', 'hora', 'Nombre Completo', 'Estado', 'metodo_deteccion']],
                use_container_width=True
            )
        else:
            st.info("No hay asistencias registradas.")
    
    def gestion_estudiantes(self):
        """Interfaz de gestión de estudiantes"""
        st.header("👥 Gestión de Estudiantes")
        
        # Pestañas para diferentes operaciones
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Lista de Estudiantes", 
            "➕ Registrar Nuevo",
            "✏️ Editar Estudiante", 
            "📷 Capturar Rostros"
        ])
        
        with tab1:
            self.mostrar_lista_estudiantes()
        
        with tab2:
            self.registrar_nuevo_estudiante()
        
        with tab3:
            self.editar_estudiante()
        
        with tab4:
            self.capturar_rostros_existente()
    
    def mostrar_lista_estudiantes(self):
        """Mostrar lista de estudiantes"""
        estudiantes = self.db.obtener_estudiantes()
        
        if estudiantes:
            # Convertir a DataFrame para mejor visualización
            df = pd.DataFrame(estudiantes, columns=[
                'ID', 'Código', 'Nombre', 'Apellido', 'Edad', 'Sección', 'Fecha Registro'
            ])
            
            # Mostrar tabla con opciones
            st.dataframe(df, use_container_width=True)
            
            # Opciones de exportación
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Exportar a CSV"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Descargar CSV",
                        csv,
                        "estudiantes.csv",
                        "text/csv"
                    )
        else:
            st.info("No hay estudiantes registrados.")
    
    def registrar_nuevo_estudiante(self):
        """Formulario para registrar nuevo estudiante"""
        st.subheader("Registrar Nuevo Estudiante")
        
        with st.form("nuevo_estudiante"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre *")
                edad = st.number_input("Edad", min_value=5, max_value=30, value=15)
                codigo = st.text_input("Código (opcional)")
            
            with col2:
                apellido = st.text_input("Apellido *")
                seccion = st.text_input("Sección")
            
            submitted = st.form_submit_button("Registrar Estudiante")
            
            if submitted:
                if nombre and apellido:
                    estudiante_id, codigo_asignado = self.db.agregar_estudiante(
                        nombre, apellido, int(edad) if edad else None, 
                        seccion, codigo
                    )
                    
                    if estudiante_id:
                        st.success(f"✅ Estudiante {nombre} {apellido} registrado con código: {codigo_asignado}")
                        st.info("Ahora puedes capturar sus rostros en la pestaña 'Capturar Rostros'")
                    else:
                        st.error("❌ Error al registrar estudiante")
                else:
                    st.error("❌ Nombre y apellido son obligatorios")
    
    def editar_estudiante(self):
        """Interfaz para editar estudiantes"""
        st.subheader("Editar Información de Estudiante")
        
        estudiantes = self.db.obtener_estudiantes()
        if not estudiantes:
            st.info("No hay estudiantes para editar.")
            return
        
        # Selector de estudiante
        opciones_estudiantes = [f"{e[1]} - {e[2]} {e[3]}" for e in estudiantes]
        estudiante_seleccionado = st.selectbox("Seleccionar Estudiante", opciones_estudiantes)
        
        if estudiante_seleccionado:
            # Obtener ID del estudiante seleccionado
            estudiante_id = estudiantes[opciones_estudiantes.index(estudiante_seleccionado)][0]
            
            # Cargar datos actuales
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM estudiantes WHERE id = ?', (estudiante_id,))
            estudiante = cursor.fetchone()
            conn.close()
            
            if estudiante:
                with st.form("editar_estudiante"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nuevo_nombre = st.text_input("Nombre", value=estudiante[2])
                        nueva_edad = st.number_input("Edad", value=estudiante[4] if estudiante[4] else 15)
                    
                    with col2:
                        nuevo_apellido = st.text_input("Apellido", value=estudiante[3])
                        nueva_seccion = st.text_input("Sección", value=estudiante[5] or "")
                    
                    submitted = st.form_submit_button("Actualizar Información")
                    
                    if submitted:
                        conn = self.db._get_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE estudiantes 
                            SET nombre=?, apellido=?, edad=?, seccion=?
                            WHERE id=?
                        ''', (nuevo_nombre, nuevo_apellido, nueva_edad, nueva_seccion, estudiante_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ Información actualizada correctamente")
    
    def capturar_rostros_existente(self):
        """Interfaz para capturar rostros de estudiantes existentes"""
        st.subheader("Capturar Rostros para Estudiantes Existentes")
        
        estudiantes = self.db.obtener_estudiantes()
        if not estudiantes:
            st.info("No hay estudiantes registrados.")
            return
        
        # Selector de estudiante
        opciones_estudiantes = [f"{e[1]} - {e[2]} {e[3]}" for e in estudiantes]
        estudiante_seleccionado = st.selectbox("Seleccionar Estudiante para Capturar Rostros", opciones_estudiantes)
        
        if estudiante_seleccionado:
            estudiante_idx = opciones_estudiantes.index(estudiante_seleccionado)
            estudiante_id = estudiantes[estudiante_idx][0]
            nombre = estudiantes[estudiante_idx][2]
            apellido = estudiantes[estudiante_idx][3]
            
            st.info(f"Preparado para capturar rostros de: {nombre} {apellido}")
            
            if st.button("🎥 Iniciar Captura de Rostros"):
                st.warning("🔴 Esta función abrirá la cámara. Asegúrate de tener permisos de cámara.")
                st.info("Presiona ESPACIO para capturar cada imagen, ESC para terminar")
                
                # Aquí podrías integrar la captura de rostros
                # Por ahora mostramos un mensaje
                st.success("✅ Función de captura de rostros - Para implementar con la cámara")
    
    def registrar_asistencias(self):
        """Interfaz para registro manual de asistencias"""
        st.header("📝 Registro Manual de Asistencias")
        
        # Selector de fecha
        fecha = st.date_input("Fecha", value=date.today())
        
        estudiantes = self.db.obtener_estudiantes()
        if not estudiantes:
            st.info("No hay estudiantes registrados.")
            return
        
        # Tabla para marcar asistencias
        st.subheader("Marcar Asistencias")
        
        with st.form("asistencias_form"):
            asistencias_data = []
            
            for estudiante in estudiantes:
                id_est, codigo, nombre, apellido, edad, seccion, _ = estudiante
                nombre_completo = f"{nombre} {apellido}"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{nombre_completo}** - {seccion or 'Sin sección'}")
                with col2:
                    presente = st.checkbox(f"Presente", key=f"p_{id_est}")
                with col3:
                    tardanza = st.checkbox(f"Tardanza", key=f"t_{id_est}")
                
                if presente or tardanza:
                    estado = "presente" if presente else "tardanza"
                    asistencias_data.append((id_est, estado))
            
            submitted = st.form_submit_button("💾 Guardar Asistencias")
            
            if submitted:
                conn = self.db._get_connection()
                cursor = conn.cursor()
                
                for id_est, estado in asistencias_data:
                    cursor.execute('''
                        INSERT OR REPLACE INTO asistencias 
                        (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (id_est, fecha, datetime.now().time().strftime('%H:%M:%S'), 
                          'manual', estado, 1.0))
                
                conn.commit()
                conn.close()
                st.success(f"✅ {len(asistencias_data)} asistencias guardadas correctamente")
    
    def mostrar_reportes(self):
        """Mostrar reportes y estadísticas"""
        st.header("📈 Reportes y Estadísticas")
        
        tab1, tab2, tab3 = st.tabs(["📊 Estadísticas Generales", "📅 Por Período", "👤 Por Estudiante"])
        
        with tab1:
            self.reportes_generales()
        
        with tab2:
            self.reportes_por_periodo()
        
        with tab3:
            self.reportes_por_estudiante()
    
    def reportes_generales(self):
        """Reportes generales del sistema"""
        st.subheader("Estadísticas Generales")
        
        # Aquí puedes agregar más gráficos y estadísticas
        conn = self.db._get_connection()
        
        # Porcentaje de asistencias por estado
        query = '''
            SELECT estado, COUNT(*) as count
            FROM asistencias
            GROUP BY estado
        '''
        df_estados = pd.read_sql_query(query, conn)
        
        if not df_estados.empty:
            fig = px.pie(df_estados, values='count', names='estado', 
                        title="Distribución de Asistencias por Estado")
            st.plotly_chart(fig, use_container_width=True)
        
        conn.close()
    
    def configuracion(self):
        """Interfaz de configuración"""
        st.header("⚙️ Configuración del Sistema")
        
        st.subheader("Configuración de Horarios")
        
        with st.form("config_form"):
            hora_entrada = st.time_input("Hora de entrada", value=datetime.strptime("08:00", "%H:%M").time())
            tolerancia = st.number_input("Tolerancia en minutos", min_value=0, max_value=60, value=15)
            
            if st.form_submit_button("💾 Guardar Configuración"):
                conn = self.db._get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE configuracion 
                    SET hora_entrada=?, tolerancia_minutos=?, ultima_actualizacion=CURRENT_TIMESTAMP
                    WHERE id=1
                ''', (hora_entrada.strftime('%H:%M:%S'), tolerancia))
                conn.commit()
                conn.close()
                st.success("✅ Configuración guardada correctamente")


def main():
    interfaz = InterfazWeb()
    
    opcion = interfaz.mostrar_sidebar()
    
    if opcion == "📊 Dashboard":
        interfaz.mostrar_dashboard()
    
    elif opcion == "👥 Gestión de Estudiantes":
        interfaz.gestion_estudiantes()
    
    elif opcion == "📝 Registrar Asistencias":
        interfaz.registrar_asistencias()
    
    elif opcion == "📈 Reportes y Estadísticas":
        interfaz.mostrar_reportes()
    
    elif opcion == "⚙️ Configuración":
        interfaz.configuracion()

if __name__ == "__main__":
    main()