import math
import sqlite3
import random
import os
import hashlib
import sys
import secrets
import shutil
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from recuperacion_pin import RecuperacionPIN

# ==================== SISTEMA DE LOGGING MEJORADO ====================

import logging
import json

def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sistema_asistencia.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()
try:
    from recuperacion_pin import RecuperacionPIN
    print("OK: módulo recuperacion_pin importado correctamente")
except Exception as e:
    print("ERROR al importar recuperacion_pin:", e)


try:
    from PIL import Image, ImageTk, ImageSequence, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception as e:
    print(f"PIL no disponible: {e}")
    PIL_AVAILABLE = False

DB = "asistencia.db"


# ==================== MANEJADOR DE BASE DE DATOS MEJORADO ====================

class DatabaseManager:
    """Manejador mejorado para operaciones de base de datos"""
    
    def __init__(self, db_path="asistencia.db"):
        self.db_path = db_path
        self.cache = {}
    
    def execute_query(self, query, params=(), fetch=False):
        """Ejecuta una consulta con manejo de errores"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
                conn.commit()
                conn.close()
                return result
            else:
                conn.commit()
                conn.close()
                return cursor.rowcount
                
        except sqlite3.Error as e:
            logger.error(f"Error en consulta: {e} - Query: {query}")
            conn.rollback()
            conn.close()
            return None

    def get_estudiantes(self, force_refresh=False):
        """Obtiene estudiantes con cache"""
        cache_key = "estudiantes"
        if not force_refresh and cache_key in self.cache:
            return self.cache[cache_key]
        
        query = "SELECT * FROM estudiantes ORDER BY id DESC"
        result = self.execute_query(query, fetch=True)
        if result:
            self.cache[cache_key] = result
        return result

    def clear_cache(self, key=None):
        """Limpia la cache"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()

# ==================== SISTEMA DE CONFIGURACIÓN ====================

class ConfigManager:
    """Manejador de configuración del sistema"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "database": {
                "name": "asistencia.db",
                "backup_auto": True,
                "backup_interval_hours": 24
            },
            "instituto": {
                "nombre": "Instituto Rubén Darío",
                "tolerancia_minutos": 15,
                "max_faltas_mes": 3
            },
            "seguridad": {
                "intentos_maximos": 3,
                "bloqueo_temporal_min": 30,
                "longitud_minima_password": 6
            },
            "ui": {
                "tema": "default",
                "mostrar_tooltips": True,
                "animaciones": True
            }
        }
        self.load_config()
    
    def load_config(self):
        """Carga la configuración desde archivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("Configuración cargada exitosamente")
            else:
                self.config = self.default_config
                self.save_config()
                logger.info("Configuración por defecto creada")
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self.config = self.default_config
    
    def save_config(self):
        """Guarda la configuración en archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("Configuración guardada exitosamente")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
    
    def get(self, key, default=None):
        """Obtiene un valor de configuración"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """Establece un valor de configuración"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()

# ==================== SISTEMA DE PERMISOS MEJORADO ====================

class PermisosManager:
    """Sistema de permisos granular"""
    
    PERMISOS = {
        'Administrador': {
            'gestion_usuarios': True,
            'gestion_docentes': True,
            'gestion_estudiantes': True,
            'control_asistencia': True,
            'ver_reportes': True,
            'exportar_datos': True,
            'configuracion_sistema': True,
            'backup_restore': True,
            'auditoria': True
        },
        'Docente': {
            'gestion_usuarios': False,
            'gestion_docentes': False,
            'gestion_estudiantes': False,
            'control_asistencia': True,
            'ver_reportes': True,
            'exportar_datos': True,
            'configuracion_sistema': False,
            'backup_restore': False,
            'auditoria': False
        },
        'Estudiante': {
            'gestion_usuarios': False,
            'gestion_docentes': False,
            'gestion_estudiantes': False,
            'control_asistencia': False,
            'ver_reportes': False,
            'exportar_datos': False,
            'configuracion_sistema': False,
            'backup_restore': False,
            'auditoria': False
        }
    }
    
    @classmethod
    def tiene_permiso(cls, rol, permiso):
        """Verifica si un rol tiene un permiso específico"""
        return cls.PERMISOS.get(rol, {}).get(permiso, False)
# ==================== VALIDACIONES ====================

import re

def validar_correo(correo):
    """
    Valida que el correo electrónico tenga un formato correcto
    Ejemplo: usuario@dominio.com
    """
    if not correo:
        return True  # Permitir campo vacío (opcional)
    
    # Patrón para validar correo electrónico
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(patron, correo):
        return True
    else:
        return False

def validar_telefono(telefono):
    """
    Valida que el teléfono tenga un formato correcto
    Ejemplo: 8888-8888 o 88888888
    """
    if not telefono:
        return True  # Permitir campo vacío
    
    # Patrón para validar teléfono (8 dígitos, con o sin guión)
    patron = r'^(\d{8}|\d{4}-\d{4})$'
    
    if re.match(patron, telefono):
        return True
    else:
        return False

def validar_cedula(cedula):
    """
    Valida que la cédula tenga un formato correcto
    Ejemplo: 001-080888-8888A o 0010808888888A
    """
    if not cedula:
        return False  # Cédula es obligatoria
    
    # Patrón para validar cédula nicaragüense (formato flexible)
    patron = r'^\d{3}[-]?\d{6}[-]?\d{4}[A-Za-z]?$'
    
    if re.match(patron, cedula):
        return True
    else:
        return False

def validar_solo_texto(texto):
    """
    Valida que el texto contenga solo letras y espacios
    """
    if not texto:
        return False
    
    patron = r'^[A-Za-záéíóúñÑ\s]+$'
    return bool(re.match(patron, texto))

def mostrar_error_correo():
    """Muestra un mensaje de error con ejemplo de formato correcto"""
    messagebox.showerror(
        "Error en formato de correo", 
        "❌ El formato del correo electrónico no es válido.\n\n"
        "📧 FORMATO REQUERIDO:\n"
        "   usuario@dominio.extensión\n\n"
        "📋 EJEMPLOS VÁLIDOS:\n"
        "   • juan.perez@gmail.com\n"
        "   • maria_rodriguez@instituto.edu.ni\n"
        "   • carlos123@hotmail.com\n\n"
        "⚠️  DEBE CONTENER:\n"
        "   • Un símbolo @\n"
        "   • Dominio después del @\n"
        "   • Extensión (.com, .edu, .org, etc.)"
    )

def mostrar_error_telefono():
    """Muestra un mensaje de error para teléfono"""
    messagebox.showerror(
        "Error en formato de teléfono", 
        "❌ El formato del teléfono no es válido.\n\n"
        "📞 FORMATOS ACEPTADOS:\n"
        "   • 88888888 (8 dígitos)\n"
        "   • 8888-8888 (con guión)\n\n"
        "📋 EJEMPLOS VÁLIDOS:\n"
        "   • 12345678\n"
        "   • 5555-1234\n"
        "   • 8888-8888"
    )

def mostrar_error_cedula():
    """Muestra un mensaje de error para cédula"""
    messagebox.showerror(
        "Error en formato de cédula", 
        "❌ El formato de la cédula no es válido.\n\n"
        "🆔 FORMATOS ACEPTADOS:\n"
        "   • 0010808888888A (13 dígitos + letra)\n"
        "   • 001-080888-8888A (con guiones)\n\n"
        "📋 EJEMPLOS VÁLIDOS:\n"
        "   • 0010808888888A\n"
        "   • 001-080888-8888A\n"
        "   • 123-456789-1234B"
    )

def mostrar_error_texto(campo):
    """Muestra un mensaje de error para campos de texto"""
    messagebox.showerror(
        f"Error en {campo}", 
        f"❌ El campo '{campo}' solo puede contener letras y espacios.\n\n"
        f"📝 EJEMPLOS VÁLIDOS:\n"
        f"   • María José\n"
        f"   • Carlos Antonio\n"
        f"   • Ana Lucía\n\n"
        f"⚠️  NO SE PERMITEN:\n"
        f"   • Números (123)\n"
        f"   • Símbolos especiales (@, #, $, etc.)"
    )

# ==================== SISTEMA DE MENSAJES MEJORADO ====================

class MessageManager:
    """Gestor mejorado de mensajes que mantiene el foco en las ventanas correctas"""
    
    @staticmethod
    def show_info(parent, title, message):
        """Muestra mensaje informativo manteniendo el foco"""
        parent.update_idletasks()  # Forzar actualización de la UI
        result = messagebox.showinfo(title, message, parent=parent)
        parent.focus_force()  # Recuperar el foco
        parent.lift()  # Traer al frente
        return result
    
    @staticmethod
    def show_warning(parent, title, message):
        """Muestra advertencia manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.showwarning(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result
    
    @staticmethod
    def show_error(parent, title, message):
        """Muestra error manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.showerror(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result
    
    @staticmethod
    def ask_yesno(parent, title, message):
        """Pregunta sí/no manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.askyesno(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result

# ==================== GESTOR DE VENTANAS ====================

class GestorVentanas:
    _ventanas_abiertas = {}
    _ventana_activa = None
    
    @classmethod
    def abrir_ventana(cls, root, clase_ventana, titulo, *args, **kwargs):
        """Abre una ventana si no está ya abierta - MEJORADO"""
        if titulo in cls._ventanas_abiertas:
            # Traer ventana existente al frente
            ventana_existente = cls._ventanas_abiertas[titulo]
            try:
                ventana_existente.lift()
                ventana_existente.focus_force()
                cls._ventana_activa = ventana_existente
                return ventana_existente
            except:
                cls._ventanas_abiertas.pop(titulo, None)
        
        # Crear nueva ventana
        nueva_ventana = Toplevel(root)
        nueva_ventana.title(titulo)
        nueva_ventana.geometry("900x600")
        nueva_ventana.transient(root)  # Hacerla dependiente de la principal
        nueva_ventana.grab_set()  # Modal
        
        # Configurar cierre
        nueva_ventana.protocol("WM_DELETE_WINDOW", 
                             lambda: cls.cerrar_ventana(titulo))
        
        # Centrar ventana
        cls._centrar_ventana(nueva_ventana, root)
        
        # Registrar ventana
        cls._ventanas_abiertas[titulo] = nueva_ventana
        cls._ventana_activa = nueva_ventana
        
        # Crear contenido
        try:
            clase_ventana(nueva_ventana, *args, **kwargs)
        except Exception as e:
            print(f"Error al crear ventana {titulo}: {e}")
            nueva_ventana.destroy()
            cls._ventanas_abiertas.pop(titulo, None)
        
        return nueva_ventana

    @classmethod
    def get_ventana_activa(cls):
        """Obtiene la ventana activa actual"""
        return cls._ventana_activa     



# ==================== FUNCIONES DE BASE DE DATOS Y SEGURIDAD ====================

def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def crear_db_y_schema():
    """Crea las tablas si no existen y realiza migraciones"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Tabla usuarios (con salt y hash)
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            pass_hash TEXT,
            salt TEXT,
            rol TEXT DEFAULT 'Administrador',
            clave TEXT
        )
    """)

    # Tabla docentes
    c.execute("""
        CREATE TABLE IF NOT EXISTS docentes (
            id_docente INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE,
            nombres TEXT,
            apellido TEXT,
            especialidad TEXT,
            email TEXT,
            telefono TEXT,
            estado TEXT DEFAULT 'ACTIVO',
            fecha_ingreso TEXT,
            genero TEXT,
            direccion TEXT
        )
    """)

    # Tabla estudiantes
    c.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT,
            nombres TEXT,
            apellidos TEXT,
            carrera TEXT,
            anio TEXT,
            seccion TEXT,
            telefono TEXT,
            direccion TEXT
        )
    """)

    # Carreras
    c.execute("""
        CREATE TABLE IF NOT EXISTS carreras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    # Asistencia (estudiantes) - CORREGIDO: FOREIGN KEY
    c.execute("""
        CREATE TABLE IF NOT EXISTS asistencia (
            id_asistencia INTEGER PRIMARY KEY AUTOINCREMENT,
            id_estudiante INTEGER,
            fecha TEXT,
            hora_entrada TEXT,
            hora_salida TEXT,
            estado TEXT,
            observaciones TEXT,
            FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id)
        )
    """)

    # NUEVAS TABLAS
    # Tabla de materias
    c.execute("""
        CREATE TABLE IF NOT EXISTS materias (
            id_materia INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            carrera_id INTEGER,
            creditos INTEGER,
            FOREIGN KEY (carrera_id) REFERENCES carreras(id)
        )
    """)
    
    # Tabla de horarios
    c.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id_horario INTEGER PRIMARY KEY AUTOINCREMENT,
            materia_id INTEGER,
            docente_id INTEGER,
            dia_semana TEXT,
            hora_inicio TIME,
            hora_fin TIME,
            aula TEXT,
            FOREIGN KEY (materia_id) REFERENCES materias(id_materia),
            FOREIGN KEY (docente_id) REFERENCES docentes(id_docente)
        )
    """)
    
    # Tabla de justificaciones
    c.execute("""
        CREATE TABLE IF NOT EXISTS justificaciones (
            id_justificacion INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER,
            fecha DATE,
            motivo TEXT,
            evidencia TEXT,
            estado TEXT DEFAULT 'Pendiente',
            fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
        )
    """)
    
    # Tabla de configuración del sistema
    c.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    conn.commit()

    # Migración de usuarios existentes
    try:
        c.execute("PRAGMA table_info(usuarios)")
        cols = [r[1] for r in c.fetchall()]
        if "clave" in cols and ("pass_hash" not in cols or "salt" not in cols):
            c.execute("SELECT id_usuario, clave FROM usuarios WHERE clave IS NOT NULL")
            rows = c.fetchall()
            for uid, clave in rows:
                salt = secrets.token_hex(8)
                h = hash_password(clave, salt)
                c.execute("UPDATE usuarios SET pass_hash=?, salt=? WHERE id_usuario=?", (h, salt, uid))
            conn.commit()
    except:
        pass

    # Insertar admin por defecto
    try:
        c.execute("SELECT id_usuario FROM usuarios WHERE usuario='admin'")
        if not c.fetchone():
            salt = secrets.token_hex(8)
            pass_hash = hash_password("1234", salt)
            c.execute("INSERT INTO usuarios (usuario, pass_hash, salt, rol) VALUES (?, ?, ?, ?)",
                      ('admin', pass_hash, salt, 'Administrador'))
            conn.commit()
    except:
        pass

    # Insertar carreras
    try:
        carreras = [
            ('Técnico en Informática',),
            ('Técnico en Electrónica',),
            ('Técnico en Mecánica',),
            ('Técnico en Administración',),
        ]
        c.executemany("INSERT OR IGNORE INTO carreras(nombre) VALUES (?)", carreras)
    except:
        pass
    
    # Insertar configuraciones por defecto
    try:
        configs = [
            ('tolerancia_minutos', '15'),
            ('max_faltas_por_mes', '3'),
            ('hora_entrada_obligatoria', '07:00:00'),
            ('institucion_nombre', 'Instituto Rubén Darío')
        ]
        c.executemany("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", configs)
    except:
        pass
    
    conn.commit()
    conn.close()
    print("✅ Base de datos creada/actualizada correctamente")

def create_user(usuario: str, password: str, rol='Usuario'):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    salt = secrets.token_hex(8)
    h = hash_password(password, salt)
    try:
        c.execute("INSERT INTO usuarios (usuario, pass_hash, salt, rol) VALUES (?, ?, ?, ?)",
                  (usuario, h, salt, rol))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False, "El usuario ya existe"
    conn.close()
    return True, "Usuario creado"

def verificar_usuario(usuario, clave):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT pass_hash, salt, rol FROM usuarios WHERE usuario=?", (usuario,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None
    pass_hash, salt, rol = row
    if not pass_hash or not salt:
        return None
    hashed_input = hashlib.sha256((salt + clave).encode()).hexdigest()
    if hashed_input == pass_hash:
        return (usuario, rol)
    else:
        return None

# ==================== SISTEMA DE BACKUP ====================

class BackupManager:
    def __init__(self):
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def crear_backup(self):
        """Crea un backup de la base de datos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"asistencia_backup_{timestamp}.db")
        
        try:
            shutil.copy2(DB, backup_file)
            return True, f"Backup creado: {backup_file}"
        except Exception as e:
            return False, f"Error creando backup: {e}"
    
    def restaurar_backup(self, backup_file):
        """Restaura un backup"""
        try:
            shutil.copy2(backup_file, DB)
            return True, "Backup restaurado exitosamente"
        except Exception as e:
            return False, f"Error restaurando backup: {e}"
    
    def listar_backups(self):
        """Lista todos los backups disponibles"""
        if os.path.exists(self.backup_dir):
            archivos = sorted(os.listdir(self.backup_dir))
            return [archivo for archivo in archivos if archivo.endswith('.db')]
        return []

# ==================== SISTEMA DE AUDITORÍA ====================

class Auditoria:
    """Sistema de auditoría para registrar acciones"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.crear_tabla_auditoria()
    
    def crear_tabla_auditoria(self):
        """Crea la tabla de auditoría si no existe"""
        query = """
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                accion TEXT NOT NULL,
                detalles TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip TEXT
            )
        """
        self.db_manager.execute_query(query)
    
    def registrar_evento(self, usuario, accion, detalles="", ip="localhost"):
        """Registra un evento en la auditoría"""
        query = """
            INSERT INTO auditoria (usuario, accion, detalles, ip)
            VALUES (?, ?, ?, ?)
        """
        self.db_manager.execute_query(query, (usuario, accion, detalles, ip))
        logger.info(f"AUDITORIA - Usuario: {usuario}, Acción: {accion}, Detalles: {detalles}")

# ==================== SISTEMA DE NOTIFICACIONES MEJORADO ====================

class SistemaNotificaciones:
    """Sistema de notificaciones mejorado"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.notificaciones = []
    
    def verificar_notificaciones_pendientes(self):
        """Verifica y genera notificaciones automáticas"""
        self.notificaciones.clear()
        
        # Verificar estudiantes sin asistencia hoy
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        query = """
            SELECT COUNT(*) as faltantes 
            FROM estudiantes e
            LEFT JOIN asistencia a ON e.id = a.id_estudiante AND a.fecha = ?
            WHERE a.id_asistencia IS NULL
        """
        result = self.db_manager.execute_query(query, (fecha_hoy,), fetch=True)
        
        if result and result[0]['faltantes'] > 0:
            self.notificaciones.append({
                'tipo': 'advertencia',
                'titulo': 'Estudiantes sin asistencia',
                'mensaje': f'{result[0]["faltantes"]} estudiantes no tienen asistencia registrada hoy',
                'fecha': datetime.now()
            })
        
        # Verificar backup automático
        if not os.path.exists("backups"):
            self.notificaciones.append({
                'tipo': 'info',
                'titulo': 'Carpeta de backups',
                'mensaje': 'La carpeta de backups no existe',
                'fecha': datetime.now()
            })
    
    def mostrar_notificaciones(self, parent):
        """Muestra las notificaciones pendientes"""
        if not self.notificaciones:
            return
        
        ventana_notificaciones = Toplevel(parent)
        ventana_notificaciones.title("Notificaciones del Sistema")
        ventana_notificaciones.geometry("500x400")
        ventana_notificaciones.configure(bg='white')
        
        Label(ventana_notificaciones, text="🔔 Notificaciones", 
              font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        frame_lista = Frame(ventana_notificaciones, bg="white")
        frame_lista.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        for notif in self.notificaciones:
            color_fondo = {
                'advertencia': '#fff3cd',
                'peligro': '#f8d7da', 
                'info': '#d1ecf1',
                'exito': '#d4edda'
            }.get(notif['tipo'], '#ffffff')
            
            frame_notif = Frame(frame_lista, bg=color_fondo, relief='raised', bd=1)
            frame_notif.pack(fill=X, pady=5)
            
            Label(frame_notif, text=notif['titulo'], font=("Arial", 10, "bold"),
                  bg=color_fondo).pack(anchor='w', padx=10, pady=(10, 0))
            Label(frame_notif, text=notif['mensaje'], font=("Arial", 9),
                  bg=color_fondo, wraplength=400).pack(anchor='w', padx=10, pady=(0, 10))
        
        Button(ventana_notificaciones, text="Cerrar", command=ventana_notificaciones.destroy).pack(pady=10)
# ==================== SISTEMA DE ALERTAS ====================

class ExportadorAvanzado:
    """Sistema de exportación mejorado"""
    
    @staticmethod
    def exportar_csv(datos, nombre_archivo, encabezados=None):
        """Exporta datos a CSV"""
        try:
            with open(f"{nombre_archivo}.csv", 'w', encoding='utf-8') as f:
                if encabezados:
                    f.write(','.join(encabezados) + '\n')
                for fila in datos:
                    linea = ','.join(str(x) for x in fila)
                    f.write(linea + '\n')
            return True, f"Archivo {nombre_archivo}.csv exportado exitosamente"
        except Exception as e:
            return False, f"Error exportando CSV: {e}"
    
    @staticmethod
    def exportar_html(datos, nombre_archivo, titulo="Reporte", encabezados=None):
        """Exporta datos a HTML"""
        try:
            with open(f"{nombre_archivo}.html", 'w', encoding='utf-8') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{titulo}</title>
                    <style>
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    </style>
                </head>
                <body>
                    <h1>{titulo}</h1>
                    <table>
                """)
                
                if encabezados:
                    f.write("<tr>")
                    for enc in encabezados:
                        f.write(f"<th>{enc}</th>")
                    f.write("</tr>")
                
                for fila in datos:
                    f.write("<tr>")
                    for celda in fila:
                        f.write(f"<td>{celda}</td>")
                    f.write("</tr>")
                
                f.write("""
                    </table>
                </body>
                </html>
                """)
            return True, f"Archivo {nombre_archivo}.html exportado exitosamente"
        except Exception as e:
            return False, f"Error exportando HTML: {e}"

# ==================== BUSCADOR AVANZADO ====================

class BuscadorAvanzado:
    """Sistema de búsqueda avanzada"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def buscar_estudiantes(self, criterios):
        """Búsqueda avanzada de estudiantes"""
        query = "SELECT * FROM estudiantes WHERE 1=1"
        params = []
        
        if criterios.get('nombre'):
            query += " AND (nombres LIKE ? OR apellidos LIKE ?)"
            params.extend([f"%{criterios['nombre']}%", f"%{criterios['nombre']}%"])
        
        if criterios.get('carrera'):
            query += " AND carrera = ?"
            params.append(criterios['carrera'])
        
        if criterios.get('cedula'):
            query += " AND cedula LIKE ?"
            params.append(f"%{criterios['cedula']}%")
        
        if criterios.get('anio'):
            query += " AND anio = ?"
            params.append(criterios['anio'])
        
        query += " ORDER BY id DESC"
        
        return self.db_manager.execute_query(query, params, fetch=True)
            # ==================== GESTIÓN ESTUDIANTES ====================

class GestionEstudiantes:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Estudiantes Técnicos")
        self.root.geometry("1150x750")
        self.root.configure(bg="#f9fafb")
        self.root.minsize(1000, 700)  # Tamaño mínimo

        # Configurar para mantener el foco
        self.root.focus_force()
        self.root.grab_set()

        # Aplicar fondo temático
        self.fondo_manager = FondoManager(root, "gestion_estudiantes")
        self.fondo_manager.aplicar_fondo()

        # Panel principal semi-transparente
        self.panel_principal = Frame(root, bg='white', bd=3, relief='raised')
        self.panel_principal.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Prevenir múltiples instancias
        self.root.focus_set()
        self.root.grab_set()

        header = Frame(self.panel_principal, bg="white", pady=10)
        header.pack(fill='x')
        
        Label(header, text="🎓 Gestión de Estudiantes Técnicos - Instituto Rubén Darío",
              font=("Arial", 18, "bold"), bg="white", fg="#2563eb").pack()
        
        # Botón cerrar en header
        Button(header, text="✖ Cerrar", bg="#dc2626", fg="white", 
               command=self.root.destroy, font=("Arial", 10)).pack(side=RIGHT, padx=20)

        # Contenedor principal
        main_container = Frame(self.root, bg="#f9fafb")
        main_container.pack(fill=BOTH, expand=True, padx=25, pady=15)

        # Frame del formulario
        form_container = Frame(main_container, bg="#f9fafb")
        form_container.pack(fill=X, pady=10)

        form = Frame(form_container, bg="#f9fafb", padx=20, pady=20)
        form.pack(fill=X)

        # Fila 1 - Cédula y Nombres
        Label(form, text="Cédula:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=12, pady=10, sticky=E)
        self.txt_cedula = Entry(form, width=22, font=("Arial", 10))
        self.txt_cedula.grid(row=0, column=1, padx=12, pady=10, sticky=W)
        self.txt_cedula.bind('<Return>', lambda event: self.txt_nombres.focus_set())
        
        Label(form, text="Ejemplo: 001-080888-8888A", font=("Arial", 9), fg="gray", bg="#f9fafb", wraplength=200).grid(row=0, column=2, sticky=W, padx=5)
        
        Label(form, text="Nombres:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=12, pady=10, sticky=E)
        self.txt_nombres = Entry(form, width=25, font=("Arial", 10))
        self.txt_nombres.grid(row=0, column=4, padx=12, pady=10, sticky=W)
        self.txt_nombres.bind('<Return>', lambda event: self.txt_apellidos.focus_set())
        
        Label(form, text="Solo letras y espacios", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=0, column=5, sticky=W, padx=5)

        # Fila 2 - Apellidos y Carrera
        Label(form, text="Apellidos:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=12, pady=10, sticky=E)
        self.txt_apellidos = Entry(form, width=22, font=("Arial", 10))
        self.txt_apellidos.grid(row=1, column=1, padx=12, pady=10, sticky=W)
        self.txt_apellidos.bind('<Return>', lambda event: self.cmb_carrera.focus_set())
        
        Label(form, text="Solo letras y espacios", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=1, column=2, sticky=W, padx=5)
        
        Label(form, text="Carrera Técnica:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=1, column=3, padx=12, pady=10, sticky=E)
        self.cmb_carrera = ttk.Combobox(form, width=23, font=("Arial", 10), state="readonly")
        self.cmb_carrera.grid(row=1, column=4, padx=12, pady=10, sticky=W)
        self.cmb_carrera.bind('<Return>', lambda event: self.txt_anio.focus_set())
        
        Label(form, text="Seleccione una carrera", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=1, column=5, sticky=W, padx=5)

        # Fila 3 - Año y Sección
        Label(form, text="Año:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=12, pady=10, sticky=E)
        self.txt_anio = Entry(form, width=22, font=("Arial", 10))
        self.txt_anio.grid(row=2, column=1, padx=12, pady=10, sticky=W)
        self.txt_anio.bind('<Return>', lambda event: self.txt_seccion.focus_set())
        
        Label(form, text="Ejemplo: 2024, 1er Año", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=2, column=2, sticky=W, padx=5)
        
        Label(form, text="Sección:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=2, column=3, padx=12, pady=10, sticky=E)
        self.txt_seccion = Entry(form, width=25, font=("Arial", 10))
        self.txt_seccion.grid(row=2, column=4, padx=12, pady=10, sticky=W)
        self.txt_seccion.bind('<Return>', lambda event: self.txt_telefono.focus_set())
        
        Label(form, text="Ejemplo: A, B, Matutina", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=2, column=5, sticky=W, padx=5)

        # Fila 4 - Teléfono y Dirección
        Label(form, text="Teléfono:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=12, pady=10, sticky=E)
        self.txt_telefono = Entry(form, width=22, font=("Arial", 10))
        self.txt_telefono.grid(row=3, column=1, padx=12, pady=10, sticky=W)
        self.txt_telefono.bind('<Return>', lambda event: self.txt_direccion.focus_set())
        
        Label(form, text="Ejemplo: 8888-8888", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=3, column=2, sticky=W, padx=5)
        
        Label(form, text="Dirección:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=3, column=3, padx=12, pady=10, sticky=E)
        self.txt_direccion = Entry(form, width=45, font=("Arial", 10))
        self.txt_direccion.grid(row=3, column=4, columnspan=2, padx=12, pady=10, sticky=W)
        self.txt_direccion.bind('<Return>', lambda event: self.guardar_estudiante())
        
        Label(form, text="Ejemplo: Managua, Barrio X", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=3, column=6, sticky=W, padx=5)

        # Separador
        separator = Frame(form_container, height=2, bg="#e5e7eb")
        separator.pack(fill=X, pady=20)

        # Botones de acción
        acciones = Frame(form_container, bg="#f9fafb", pady=15)
        acciones.pack()
        
        Button(acciones, text="💾 Guardar Estudiante", bg="#2563eb", fg="white", 
               font=("Arial", 11, "bold"), padx=20, pady=10, command=self.guardar_estudiante).grid(row=0, column=0, padx=12)
        Button(acciones, text="✏️ Actualizar", bg="#16a34a", fg="white", 
               font=("Arial", 11), padx=20, pady=10, command=self.actualizar_estudiante).grid(row=0, column=1, padx=12)
        Button(acciones, text="🗑️ Eliminar", bg="#dc2626", fg="white", 
               font=("Arial", 11), padx=20, pady=10, command=self.eliminar_estudiante).grid(row=0, column=2, padx=12)
        Button(acciones, text="🧹 Limpiar", bg="#f59e0b", fg="white", 
               font=("Arial", 11), padx=20, pady=10, command=self.limpiar_campos).grid(row=0, column=3, padx=12)

        # Validaciones en tiempo real
        self.txt_cedula.bind("<FocusOut>", self.validar_cedula_tiempo_real)
        self.txt_nombres.bind("<FocusOut>", self.validar_nombres_tiempo_real)
        self.txt_apellidos.bind("<FocusOut>", self.validar_apellidos_tiempo_real)
        self.txt_telefono.bind("<FocusOut>", self.validar_telefono_tiempo_real)

        # Treeview con scroll
        tree_frame = Frame(main_container, bg="#f9fafb")
        tree_frame.pack(fill=BOTH, expand=True, pady=15)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        cols = ("id", "cedula", "nombres", "apellidos", "carrera", "anio", "seccion", "telefono", "direccion")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=16, yscrollcommand=scrollbar.set)
        
        headers = {
            "id": "ID", "cedula": "Cédula", "nombres": "Nombres", "apellidos": "Apellidos",
            "carrera": "Carrera", "anio": "Año", "seccion": "Sección", 
            "telefono": "Teléfono", "direccion": "Dirección"
        }
        
        # Configurar columnas más anchas
        column_widths = {
            "id": 60, "cedula": 140, "nombres": 150, "apellidos": 150,
            "carrera": 180, "anio": 80, "seccion": 100, 
            "telefono": 120, "direccion": 200
        }
        
        for col in cols:
            self.tree.heading(col, text=headers.get(col, col.capitalize()))
            self.tree.column(col, width=column_widths.get(col, 120))
        
        self.tree.pack(fill=BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_estudiante)

        # Leyenda
        leyenda = Frame(main_container, bg="#f9fafb")
        leyenda.pack(fill=X, pady=8)
        Label(leyenda, text="* Campos obligatorios", font=("Arial", 9, "italic"), 
              fg="red", bg="#f9fafb").pack(side=LEFT)

        # inicializar datos
        self.cargar_carreras()
        self.llenar_tabla()
        
        # Poner foco en el primer campo
        self.txt_cedula.focus_set()

    def cargar_carreras(self):
        """Cargar carreras disponibles desde la base de datos"""
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("SELECT nombre FROM carreras ORDER BY nombre")
            carreras = [row[0] for row in c.fetchall()]
            self.cmb_carrera['values'] = carreras
            if carreras:
                self.cmb_carrera.current(0)
        except Exception as e:
            print(f"Error cargando carreras: {e}")
            # Si hay error, cargar algunas carreras por defecto
            carreras_default = [
                "Técnico en Informática",
                "Técnico en Electrónica", 
                "Técnico en Mecánica",
                "Técnico en Administración"
            ]
            self.cmb_carrera['values'] = carreras_default
            if carreras_default:
                self.cmb_carrera.current(0)
        finally:
            conn.close()

    def llenar_tabla(self):
        """Llenar la tabla con datos de estudiantes"""
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                SELECT id, cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion 
                FROM estudiantes 
                ORDER BY id DESC
            """)
            for row in c.fetchall():
                self.tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error llenando tabla: {e}")
            messagebox.showerror("Error", f"Error al cargar estudiantes: {e}")
        finally:
            conn.close()

    def guardar_estudiante(self):
        """Guardar nuevo estudiante - MEJORADO"""
        # Obtener datos del formulario
        cedula = self.txt_cedula.get().strip()
        nombres = self.txt_nombres.get().strip()
        apellidos = self.txt_apellidos.get().strip()
        carrera = self.cmb_carrera.get().strip()
        anio = self.txt_anio.get().strip()
        seccion = self.txt_seccion.get().strip()
        telefono = self.txt_telefono.get().strip()
        direccion = self.txt_direccion.get().strip()
        
        # Validaciones básicas
        if not cedula:
            MessageManager.show_warning(self.root, "Atención", "La cédula es obligatoria")
            self.txt_cedula.focus_set()
            return
            
        if not nombres:
            MessageManager.show_warning(self.root, "Atención", "Los nombres son obligatorios")
            self.txt_nombres.focus_set()
            return
            
        if not apellidos:
            MessageManager.show_warning(self.root, "Atención", "Los apellidos son obligatorios")
            self.txt_apellidos.focus_set()
            return
            
        if not carrera:
            MessageManager.show_warning(self.root, "Atención", "La carrera es obligatoria")
            self.cmb_carrera.focus_set()
            return
        
        # Validación de cédula
        if not validar_cedula(cedula):
            MessageManager.show_error(self.root, "Error en formato de cédula", 
                                    "❌ El formato de la cédula no es válido.\n\n"
                                    "🆔 FORMATOS ACEPTADOS:\n"
                                    "   • 0010808888888A (13 dígitos + letra)\n"
                                    "   • 001-080888-8888A (con guiones)")
            self.txt_cedula.focus_set()
            return
        
        # Validación de nombres (solo texto)
        if not validar_solo_texto(nombres):
            mostrar_error_texto("nombres")
            self.txt_nombres.focus_set()
            return
        
        # Validación de apellidos (solo texto)
        if not validar_solo_texto(apellidos):
            mostrar_error_texto("apellidos")
            self.txt_apellidos.focus_set()
            return
        
        # Validación de teléfono
        if telefono and not validar_telefono(telefono):
            mostrar_error_telefono()
            self.txt_telefono.focus_set()
            return
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO estudiantes (cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion))
            conn.commit()
            
            # MENSAJE MEJORADO - Mantiene el foco
            MessageManager.show_info(self.root, "Éxito", "✅ Estudiante guardado correctamente")
            
            self.limpiar_campos()
            self.llenar_tabla()
            
        except sqlite3.IntegrityError:
            MessageManager.show_error(self.root, "Error", "❌ La cédula ya existe en el sistema")
            self.txt_cedula.focus_set()
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al guardar: {str(e)}")
        finally:
            conn.close()

    def actualizar_estudiante(self):
        """Actualizar estudiante seleccionado - MEJORADO"""
        selection = self.tree.selection()
        if not selection:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un estudiante para actualizar")
            return
            
        item = self.tree.item(selection[0])
        values = item['values']
        
        if not values:
            return
            
        # Limpiar campos primero
        self.limpiar_campos()
        
        # Llenar campos con datos del estudiante seleccionado
        self.txt_cedula.insert(0, str(values[1]) if len(values) > 1 and values[1] else "")
        self.txt_nombres.insert(0, str(values[2]) if len(values) > 2 and values[2] else "")
        self.txt_apellidos.insert(0, str(values[3]) if len(values) > 3 and values[3] else "")
        
        # Buscar y seleccionar la carrera en el combobox
        if len(values) > 4 and values[4]:
            carrera_valor = str(values[4])
            carreras = list(self.cmb_carrera['values'])
            if carrera_valor in carreras:
                self.cmb_carrera.set(carrera_valor)
            else:
                # Si la carrera no está en la lista, la agregamos temporalmente
                nuevas_carreras = list(carreras) + [carrera_valor]
                self.cmb_carrera['values'] = nuevas_carreras
                self.cmb_carrera.set(carrera_valor)
        
        self.txt_anio.insert(0, str(values[5]) if len(values) > 5 and values[5] else "")
        self.txt_seccion.insert(0, str(values[6]) if len(values) > 6 and values[6] else "")
        self.txt_telefono.insert(0, str(values[7]) if len(values) > 7 and values[7] else "")
        self.txt_direccion.insert(0, str(values[8]) if len(values) > 8 and values[8] else "")

    def actualizar_estudiante(self):
        """Actualizar estudiante seleccionado"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Atención", "Seleccione un estudiante para actualizar")
            return
            
        item = self.tree.item(selection[0])
        values = item['values']
        
        if not values or len(values) == 0:
            messagebox.showwarning("Atención", "No hay datos del estudiante seleccionado")
            return
            
        estudiante_id = values[0]
        
        # Obtener datos actualizados del formulario
        cedula = self.txt_cedula.get().strip()
        nombres = self.txt_nombres.get().strip()
        apellidos = self.txt_apellidos.get().strip()
        carrera = self.cmb_carrera.get().strip()
        anio = self.txt_anio.get().strip()
        seccion = self.txt_seccion.get().strip()
        telefono = self.txt_telefono.get().strip()
        direccion = self.txt_direccion.get().strip()
        
        # Validaciones
        if not cedula or not nombres or not apellidos or not carrera:
            messagebox.showwarning("Atención", "Complete los campos obligatorios")
            return
        
        # Validación de cédula
        if not validar_cedula(cedula):
            mostrar_error_cedula()
            return
        
        # Validación de nombres (solo texto)
        if not validar_solo_texto(nombres):
            mostrar_error_texto("nombres")
            return
        
        # Validación de apellidos (solo texto)
        if not validar_solo_texto(apellidos):
            mostrar_error_texto("apellidos")
            return
        
        # Validación de teléfono
        if telefono and not validar_telefono(telefono):
            mostrar_error_telefono()
            return
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                UPDATE estudiantes 
                SET cedula=?, nombres=?, apellidos=?, carrera=?, anio=?, seccion=?, telefono=?, direccion=?
                WHERE id=?
            """, (cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion, estudiante_id))
            
            if c.rowcount > 0:
                conn.commit()
                MessageManager.show_info(self.root, "Éxito", "✅ Estudiante actualizado correctamente")
                self.limpiar_campos()
                self.llenar_tabla()
            else:
                MessageManager.show_error(self.root, "Error", "❌ No se pudo actualizar el estudiante")
                
        except sqlite3.IntegrityError:
            MessageManager.show_error(self.root, "Error", "❌ La cédula ya existe en el sistema")
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al actualizar: {str(e)}")
        finally:
            conn.close()

    def eliminar_estudiante(self):
        """Eliminar estudiante seleccionado - MEJORADO"""
        selection = self.tree.selection()
        if not selection:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un estudiante para eliminar")
            return
            
        item = self.tree.item(selection[0])
        values = item['values']
        
        if not values or len(values) == 0:
            MessageManager.show_warning(self.root, "Atención", "No hay datos del estudiante seleccionado")
            return
            
        estudiante_id = values[0]
        nombre_completo = f"{values[2]} {values[3]}" if len(values) > 3 else "Estudiante"
        
        # Confirmar eliminación - MEJORADO
        respuesta = MessageManager.ask_yesno(
            self.root,
            "Confirmar Eliminación", 
            f"¿Está seguro de eliminar al estudiante:\n{nombre_completo}?\n\nEsta acción no se puede deshacer."
        )
        
        if not respuesta:
            return
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("DELETE FROM estudiantes WHERE id=?", (estudiante_id,))
            conn.commit()
            MessageManager.show_info(self.root, "Éxito", "✅ Estudiante eliminado correctamente")
            self.limpiar_campos()
            self.llenar_tabla()
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al eliminar: {str(e)}")
        finally:
            conn.close()

    def limpiar_campos(self):
        """Limpiar todos los campos del formulario"""
        self.txt_cedula.delete(0, END)
        self.txt_nombres.delete(0, END)
        self.txt_apellidos.delete(0, END)
        self.cmb_carrera.set('')
        self.txt_anio.delete(0, END)
        self.txt_seccion.delete(0, END)
        self.txt_telefono.delete(0, END)
        self.txt_direccion.delete(0, END)
        
        # Restablecer colores de fondo
        self.txt_cedula.config(bg="white")
        self.txt_nombres.config(bg="white")
        self.txt_apellidos.config(bg="white")
        self.txt_telefono.config(bg="white")
        
        # Poner foco en el primer campo
        self.txt_cedula.focus_set()

    # Métodos de validación en tiempo real
    def validar_cedula_tiempo_real(self, event=None):
        cedula = self.txt_cedula.get().strip()
        if cedula:
            if validar_cedula(cedula):
                self.txt_cedula.config(bg="#f0fff4")  # Verde claro
            else:
                self.txt_cedula.config(bg="#fff0f0")  # Rojo claro
        else:
            self.txt_cedula.config(bg="white")

    def validar_nombres_tiempo_real(self, event=None):
        nombres = self.txt_nombres.get().strip()
        if nombres:
            if validar_solo_texto(nombres):
                self.txt_nombres.config(bg="#f0fff4")
            else:
                self.txt_nombres.config(bg="#fff0f0")
        else:
            self.txt_nombres.config(bg="white")

    def validar_apellidos_tiempo_real(self, event=None):
        apellidos = self.txt_apellidos.get().strip()
        if apellidos:
            if validar_solo_texto(apellidos):
                self.txt_apellidos.config(bg="#f0fff4")
            else:
                self.txt_apellidos.config(bg="#fff0f0")
        else:
            self.txt_apellidos.config(bg="white")

    def validar_telefono_tiempo_real(self, event=None):
        telefono = self.txt_telefono.get().strip()
        if telefono:
            if validar_telefono(telefono):
                self.txt_telefono.config(bg="#f0fff4")
            else:
                self.txt_telefono.config(bg="#fff0f0")
        else:
            self.txt_telefono.config(bg="white")

# ==================== VENTANA: LOGIN ====================

# ==================== VENTANA: LOGIN ====================

class Login:
    def __init__(self, root):
        self.root = root
        self.root.title("Inicio de Sesión - Instituto Rubén Darío")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e3a8a")
        self.root.minsize(900, 600)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"1000x700+{x}+{y}")
        
        # Inicializar FondoManager
        try:
            self.fondo_manager = FondoManager(root, "login")
            self.fondo_manager.aplicar_fondo()
        except Exception as e:
            print(f"Error al cargar fondo: {e}")

        # ⌨️ Activar login con ENTER
        self.root.bind('<Return>', lambda event: self.login())

        # ==================== DISEÑO PRINCIPAL ====================
        
        # Panel principal
        self.panel_principal = Frame(root, bg='white', bd=0, relief='flat')
        self.panel_principal.place(relx=0.5, rely=0.5, anchor='center', width=500, height=620)

        # ==================== ENCABEZADO INSTITUCIONAL ====================
        
        # Logo/Icono institucional
        self.frame_logo = Frame(self.panel_principal, bg='white', height=120)
        self.frame_logo.pack(fill='x', pady=(40, 20))
        
        Label(self.frame_logo, text="🏫", font=("Arial", 40),
              bg='white', fg="#1e3a8a").pack(pady=(0, 10))
        
        Label(self.frame_logo, text="INSTITUTO RUBÉN DARÍO", 
              font=("Arial", 18, "bold"), bg='white', fg="#1e3a8a").pack()
        
        Label(self.frame_logo, text="Sistema de Gestión Académica", 
              font=("Arial", 12), bg='white', fg="#64748b").pack(pady=(5, 0))

        # Separador
        separator = Frame(self.panel_principal, height=2, bg="#e2e8f0")
        separator.pack(fill='x', padx=40, pady=25)

        # ==================== FORMULARIO DE LOGIN ====================
        
        self.frame_formulario = Frame(self.panel_principal, bg='white')
        self.frame_formulario.pack(fill='x', padx=50, pady=15)

        # Campo Usuario
        Label(self.frame_formulario, text="USUARIO:", 
              font=("Arial", 12, "bold"), bg='white', fg="#374151").pack(anchor='w', pady=(15, 8))
        
        self.usuario = Entry(self.frame_formulario, 
                           font=("Arial", 14),
                           bd=2, 
                           relief='solid',
                           highlightthickness=1,
                           highlightcolor="#2563eb",
                           highlightbackground="#d1d5db")
        self.usuario.pack(fill='x', pady=(0, 20), ipady=12)
        self.usuario.bind('<FocusIn>', lambda e: self.usuario.config(highlightbackground="#2563eb"))
        self.usuario.bind('<FocusOut>', lambda e: self.usuario.config(highlightbackground="#d1d5db"))

        # Campo Contraseña
        Label(self.frame_formulario, text="CONTRASEÑA:", 
              font=("Arial", 12, "bold"), bg='white', fg="#374151").pack(anchor='w', pady=(10, 8))
        
        self.frame_password = Frame(self.frame_formulario, bg='white')
        self.frame_password.pack(fill='x', pady=(0, 20))
        
        self.clave = Entry(self.frame_password, 
                         font=("Arial", 14),
                         show="•", 
                         bd=2, 
                         relief='solid',
                         highlightthickness=1,
                         highlightcolor="#2563eb",
                         highlightbackground="#d1d5db")
        self.clave.pack(side='left', fill='x', expand=True, ipady=12)
        self.clave.bind('<FocusIn>', lambda e: self.clave.config(highlightbackground="#2563eb"))
        self.clave.bind('<FocusOut>', lambda e: self.clave.config(highlightbackground="#d1d5db"))

        # Botón mostrar/ocultar contraseña
        self.show_pw = False
        self.btn_toggle = Button(self.frame_password, 
                               text="👁️", 
                               command=self.toggle_password,
                               font=("Arial", 12),
                               bg="#f8fafc",
                               fg="#64748b",
                               bd=2,
                               relief='solid',
                               width=4,
                               height=1)
        self.btn_toggle.pack(side='right', padx=(8, 0))

        # ==================== BOTÓN INGRESAR ====================
        
        self.btn_ingresar = Button(self.frame_formulario, 
                                 text="🎯 INGRESAR AL SISTEMA", 
                                 command=self.login,
                                 font=("Arial", 14, "bold"),
                                 bg="#2563eb",
                                 fg="white",
                                 bd=0,
                                 relief='flat',
                                 height=2,
                                 cursor="hand2")
        self.btn_ingresar.pack(fill='x', pady=(25, 20), ipady=8)
        
        # Efecto hover
        self.btn_ingresar.bind("<Enter>", lambda e: self.btn_ingresar.config(bg="#1d4ed8"))
        self.btn_ingresar.bind("<Leave>", lambda e: self.btn_ingresar.config(bg="#2563eb"))


        # ==================== BOTONES ADICIONALES ====================
        
        self.frame_botones = Frame(self.frame_formulario, bg='white')
        self.frame_botones.pack(fill='x', pady=(10, 5))

        # Botón Recuperar Contraseña
        self.btn_recuperar = Button(self.frame_botones, 
                                  text="🔐 Recuperar Contraseña", 
                                  command=self.recuperar_contrasena,
                                  font=("Arial", 10, "bold"),
                                  bg="#f59e0b",
                                  fg="white",
                                  bd=0,
                                  relief='flat',
                                  padx=15,
                                  pady=8,
                                  cursor="hand2")
        self.btn_recuperar.pack(side='left')
        
        self.btn_recuperar.bind("<Enter>", lambda e: self.btn_recuperar.config(bg="#e58e0b"))
        self.btn_recuperar.bind("<Leave>", lambda e: self.btn_recuperar.config(bg="#f59e0b"))
        
        # Botón Demo Confeti
        self.btn_confeti = Button(self.frame_botones, 
                                text="🎉 Demo", 
                                command=lambda: self.disparar_confeti(cantidad=50),
                                font=("Arial", 10, "bold"),
                                bg="#22c55e",
                                fg="white",
                                bd=0,
                                relief='flat',
                                padx=15,
                                pady=8,
                                cursor="hand2")
        self.btn_confeti.pack(side='right')
        
        self.btn_confeti.bind("<Enter>", lambda e: self.btn_confeti.config(bg="#1db34f"))
        self.btn_confeti.bind("<Leave>", lambda e: self.btn_confeti.config(bg="#22c55e"))

        # ==================== FOOTER ====================
        
        self.frame_footer = Frame(self.panel_principal, bg='white')
        self.frame_footer.pack(side='bottom', fill='x', pady=20)
        
        Label(self.frame_footer, 
              text="Sistema desarrollado para el Instituto Rubén Darío", 
              font=("Arial", 9), bg='white', fg="#94a3b8").pack()
        
        Label(self.frame_footer, 
              text="© 2024 - Todos los derechos reservados", 
              font=("Arial", 8), bg='white', fg="#cbd5e1").pack(pady=(5, 0))

        # ==================== INICIALIZACIÓN ====================
        
        # Poner foco en usuario al inicio
        self.usuario.focus_set()
        
        # Confeti de bienvenida
        self.root.after(800, lambda: self.disparar_confeti(cantidad=25))

    def toggle_password(self):
        self.show_pw = not self.show_pw
        self.clave.config(show="" if self.show_pw else "•")
        self.btn_toggle.config(text="🙈" if self.show_pw else "👁️")

    def login(self):
        usuario = self.usuario.get().strip()
        clave = self.clave.get().strip()
        
        if not usuario or not clave:
            messagebox.showwarning("Acceso al Sistema", 
                                "❌ Por favor ingrese usuario y contraseña")
            self.usuario.focus_set()
            return
        
        # Verificar credenciales
        ok = verificar_usuario(usuario, clave)
        if ok:
            usuario, rol = ok
            self.disparar_confeti(cantidad=80)
            messagebox.showinfo("Bienvenido", 
                              f"✅ ¡Bienvenido {usuario}!\n\n"
                              f"Rol: {rol}\n"
                              f"Acceso concedido al Sistema de Gestión")
            
            self.root.after(1500, self._transicion_a_menu_principal)
        else:
            messagebox.showerror("Error de Acceso", 
                               "❌ Usuario o contraseña incorrectos\n\n"
                               "Por favor verifique sus credenciales")
            self.clave.delete(0, END)
            self.usuario.focus_set()

    def _transicion_a_menu_principal(self):
        try:
            if hasattr(self, 'fondo_manager'):
                self.fondo_manager.limpiar()
            if hasattr(self, 'canvas_confeti'):
                try: self.canvas_confeti.destroy()
                except: pass
            
            usuario_actual = self.usuario.get().strip()
            self.root.withdraw()
            
            root_menu = Tk()
            # Centrar nueva ventana
            x = (root_menu.winfo_screenwidth() // 2) - (1000 // 2)
            y = (root_menu.winfo_screenheight() // 2) - (600 // 2)
            root_menu.geometry(f"1000x600+{x}+{y}")
            
            # Obtener rol real de la DB para pasar al menú
            rol_actual = "Usuario"
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("SELECT rol FROM usuarios WHERE usuario=?", (usuario_actual,))
            row = c.fetchone()
            if row:
                rol_actual = row[0]
            conn.close()
            
            app_menu = MainMenu(root_menu, usuario_actual, rol_actual)
            
            def on_closing_menu():
                try:
                    if hasattr(app_menu, 'fondo_manager'):
                        app_menu.fondo_manager.limpiar()
                    root_menu.destroy()
                except: pass
                finally:
                    import sys
                    sys.exit(0)
            
            root_menu.protocol("WM_DELETE_WINDOW", on_closing_menu)
            self.root.destroy()
            root_menu.mainloop()
            
        except Exception as e:
            print(f"Error en transición: {e}")
            sys.exit(1)

    def recuperar_contrasena(self):
        try:
           RecuperacionPIN(self.root)
        except Exception as e:
           messagebox.showerror("Error", f"No se pudo abrir recuperación: {e}")
    
    def disparar_confeti(self, cantidad=80):
        try:
            if not hasattr(self, 'canvas_confeti'):
                self.canvas_confeti = Canvas(self.root, highlightthickness=0)
                self.canvas_confeti.place(x=0, y=0, relwidth=1, relheight=1)
            self.canvas_confeti.lower(self.panel_principal)
            ancho = self.root.winfo_width() or 1000
            
            # Limpiar anterior
            for pid in getattr(self, "_confeti_particulas", []):
                try: self.canvas_confeti.delete(pid)
                except: pass
            self._confeti_particulas = []
            
            colores = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#f97316"]
            for _ in range(cantidad):
                x = random.randint(0, ancho)
                y = random.randint(-100, -20)
                sz = random.randint(10, 18)
                color = random.choice(colores)
                
                shape = random.choice(["circle", "rect", "triangle"])
                if shape == "circle":
                    pid = self.canvas_confeti.create_oval(x, y, x+sz, y+sz, fill=color, outline="")
                elif shape == "rect":
                    pid = self.canvas_confeti.create_rectangle(x, y, x+sz, y+sz, fill=color, outline="")
                else:
                    points = [x+sz/2, y, x+sz, y+sz, x, y+sz]
                    pid = self.canvas_confeti.create_polygon(points, fill=color, outline="")
                
                vx = random.uniform(-2.5, 2.5)
                vy = random.uniform(4, 8)
                self._confeti_particulas.append([pid, vx, vy])
            
            self._animar_confeti()
        except Exception as e:
            print(f"Error en confeti: {e}")

    def _animar_confeti(self):
        if not hasattr(self, '_confeti_particulas') or not self._confeti_particulas:
            return
        vivos = []
        alto = self.root.winfo_height() or 700
        for item in self._confeti_particulas:
            pid, vx, vy = item
            try:
                self.canvas_confeti.move(pid, vx, vy)
                coords = self.canvas_confeti.coords(pid)
                if coords and coords[1] < alto:
                    vivos.append([pid, vx, vy])
                else:
                    self.canvas_confeti.delete(pid)
            except: pass
        self._confeti_particulas = vivos
        if vivos:
            self.root.after(25, self._animar_confeti)
        else:
            self.root.after(1000, self._limpiar_confeti)

    def _limpiar_confeti(self):
        if hasattr(self, 'canvas_confeti'):
            try:
                self.canvas_confeti.destroy()
                del self.canvas_confeti
            except: pass


class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard - Estadísticas")
        self.root.geometry("1100x750")
        self.root.configure(bg="#f8fafc")

        self.crear_widgets()
        self.cargar_estadisticas()
    
    def crear_widgets(self):
        # Frame principal
        main_frame = Frame(self.root, bg="#f8fafc")
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Título
        Label(main_frame, text="📊 Dashboard - Estadísticas del Sistema", 
              font=("Arial", 18, "bold"), bg="#f8fafc", fg="#2563eb").pack(pady=10)
        
        # Tarjetas de estadísticas
        cards_frame = Frame(main_frame, bg="#f8fafc")
        cards_frame.pack(fill=X, pady=10)
        
        self.tarjetas = {}
        
        # Tarjeta 1: Total Estudiantes
        card1 = Frame(cards_frame, relief=RAISED, borderwidth=2, bg="#e3f2fd")
        card1.pack(side=LEFT, padx=10, ipadx=20, ipady=15)
        Label(card1, text="🎓 Total Estudiantes", bg="#e3f2fd", font=("Arial", 12, "bold")).pack()
        self.tarjetas['estudiantes'] = Label(card1, text="0", bg="#e3f2fd", font=("Arial", 24, "bold"))
        self.tarjetas['estudiantes'].pack()
        
        # Tarjeta 2: Asistencias Hoy
        card2 = Frame(cards_frame, relief=RAISED, borderwidth=2, bg="#e8f5e9")
        card2.pack(side=LEFT, padx=10, ipadx=20, ipady=15)
        Label(card2, text="✅ Asistencias Hoy", bg="#e8f5e9", font=("Arial", 12, "bold")).pack()
        self.tarjetas['asistencias_hoy'] = Label(card2, text="0", bg="#e8f5e9", font=("Arial", 24, "bold"))
        self.tarjetas['asistencias_hoy'].pack()
        
        # Tarjeta 3: Faltas Hoy
        card3 = Frame(cards_frame, relief=RAISED, borderwidth=2, bg="#ffebee")
        card3.pack(side=LEFT, padx=10, ipadx=20, ipady=15)
        Label(card3, text="❌ Faltas Hoy", bg="#ffebee", font=("Arial", 12, "bold")).pack()
        self.tarjetas['faltas_hoy'] = Label(card3, text="0", bg="#ffebee", font=("Arial", 24, "bold"))
        self.tarjetas['faltas_hoy'].pack()
        
        # Tarjeta 4: Total Docentes
        card4 = Frame(cards_frame, relief=RAISED, borderwidth=2, bg="#fff3e0")
        card4.pack(side=LEFT, padx=10, ipadx=20, ipady=15)
        Label(card4, text="👨‍🏫 Total Docentes", bg="#fff3e0", font=("Arial", 12, "bold")).pack()
        self.tarjetas['docentes'] = Label(card4, text="0", bg="#fff3e0", font=("Arial", 24, "bold"))
        self.tarjetas['docentes'].pack()
        
        # Botón actualizar
        Button(main_frame, text="🔄 Actualizar Estadísticas", 
               command=self.cargar_estadisticas, bg="#2563eb", fg="white").pack(pady=10)
        
        # Tabla de últimas asistencias
        Label(main_frame, text="Últimas Asistencias Registradas", 
              font=("Arial", 14, "bold"), bg="#f8fafc").pack(pady=10)
        
        cols = ("id", "estudiante", "fecha", "hora_entrada", "estado")
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings", height=12)
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=150)
        self.tree.pack(fill=BOTH, expand=True)
    
    def cargar_estadisticas(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        # Total estudiantes
        c.execute("SELECT COUNT(*) FROM estudiantes")
        total_estudiantes = c.fetchone()[0]
        
        # Asistencias hoy
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM asistencia WHERE fecha = ?", (fecha_hoy,))
        asistencias_hoy = c.fetchone()[0]
        
        # Faltas hoy (estimado)
        faltas_hoy = total_estudiantes - asistencias_hoy
        
        # Total docentes
        c.execute("SELECT COUNT(*) FROM docentes WHERE estado = 'ACTIVO'")
        total_docentes = c.fetchone()[0]
        
        # Últimas asistencias
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        c.execute("""
            SELECT a.id_asistencia, e.nombres || ' ' || e.apellidos, a.fecha, a.hora_entrada, a.estado
            FROM asistencia a
            LEFT JOIN estudiantes e ON a.id_estudiante = e.id
            ORDER BY a.id_asistencia DESC LIMIT 20
        """)
        
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        
        conn.close()
        
        # Actualizar tarjetas
        self.tarjetas['estudiantes'].config(text=str(total_estudiantes))
        self.tarjetas['asistencias_hoy'].config(text=str(asistencias_hoy))
        self.tarjetas['faltas_hoy'].config(text=str(faltas_hoy))
        self.tarjetas['docentes'].config(text=str(total_docentes))

# ==================== GESTIÓN DE BACKUP ====================

class GestionBackup:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Backup")
        self.root.geometry("500x400")
        self.root.configure(bg="#f9fafb")
        
        self.backup_manager = BackupManager()
        
        Label(self.root, text="💾 Gestión de Backup", 
              font=("Arial", 16, "bold"), bg="#f9fafb").pack(pady=10)
        
        # Botones principales
        btn_frame = Frame(self.root, bg="#f9fafb")
        btn_frame.pack(pady=10)
        
        Button(btn_frame, text="Crear Backup Ahora", 
               command=self.crear_backup, width=20, bg="#2563eb", fg="white").pack(pady=5)
        
        Button(btn_frame, text="Listar Backups", 
               command=self.listar_backups, width=20, bg="#16a34a", fg="white").pack(pady=5)
        
        # Lista de backups
        Label(self.root, text="Backups Disponibles:", bg="#f9fafb").pack(pady=5)
        self.lista_backups = Listbox(self.root, width=60, height=8)
        self.lista_backups.pack(pady=10, padx=20)
        
        # Botones de acción
        action_frame = Frame(self.root, bg="#f9fafb")
        action_frame.pack(pady=10)
        
        Button(action_frame, text="Restaurar Backup Seleccionado", 
               command=self.restaurar_backup, width=25, bg="#f59e0b", fg="white").pack(side=LEFT, padx=5)
        
        Button(action_frame, text="Eliminar Backup", 
               command=self.eliminar_backup, width=15, bg="#dc2626", fg="white").pack(side=LEFT, padx=5)
        
        # Cargar backups al iniciar
        self.listar_backups()
    
    def crear_backup(self):
        success, message = self.backup_manager.crear_backup()
        if success:
            messagebox.showinfo("Éxito", message)
            self.listar_backups()
        else:
            messagebox.showerror("Error", message)
    
    def listar_backups(self):
        self.lista_backups.delete(0, END)
        backups = self.backup_manager.listar_backups()
        for backup in backups:
            self.lista_backups.insert(END, backup)
    
    def restaurar_backup(self):
        seleccion = self.lista_backups.curselection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un backup de la lista")
            return
        
        backup_file = self.lista_backups.get(seleccion[0])
        backup_path = os.path.join(self.backup_manager.backup_dir, backup_file)
        
        if messagebox.askyesno("Confirmar", f"¿Restaurar backup {backup_file}? Se sobreescribirán los datos actuales."):
            success, message = self.backup_manager.restaurar_backup(backup_path)
            if success:
                messagebox.showinfo("Éxito", message)
            else:
                messagebox.showerror("Error", message)
    
    def eliminar_backup(self):
        seleccion = self.lista_backups.curselection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un backup de la lista")
            return
        
        backup_file = self.lista_backups.get(seleccion[0])
        backup_path = os.path.join(self.backup_manager.backup_dir, backup_file)
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar backup {backup_file}?"):
            try:
                os.remove(backup_path)
                messagebox.showinfo("Éxito", "Backup eliminado")
                self.listar_backups()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")

# ==================== MENÚ PRINCIPAL ====================

class MainMenu:
    def __init__(self, root, usuario, rol):
        self.root = root
        self.usuario = usuario
        self.rol = rol
        
        # Inicializar managers
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.auditoria = Auditoria(self.db_manager)
        self.notificaciones = SistemaNotificaciones(self.db_manager)
        
        # Registrar login en auditoría
        self.auditoria.registrar_evento(usuario, "LOGIN", f"Inicio de sesión exitoso - Rol: {rol}")
        
        # CONFIGURAR LA VENTANA PRIMERO
        root.title("Instituto Rubén Darío - Menú Principal")
        root.geometry("1000x600")
        root.resizable(True, True)
        
        # Centrar ventana
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (root.winfo_screenheight() // 2) - (600 // 2)
        root.geometry(f"1000x600+{x}+{y}")

        # Aplicar fondo temático DESPUÉS de configurar la ventana
        self.fondo_manager = FondoManager(root, "menu_principal")
        self.fondo_manager.aplicar_fondo()

        # Panel principal semi-transparente
        self.panel_principal = Frame(root, bg='white', bd=4, relief='ridge')
        self.panel_principal.place(relx=0.5, rely=0.5, anchor='center', width=900, height=500)

        # Encabezado con diseño institucional
        header = Frame(self.panel_principal, bg='white', pady=15)
        header.pack(fill='x', padx=20)
        
        Label(header, text="🏫 Instituto Rubén Darío", 
              font=("Arial", 20, "bold"), bg="white", fg="#1e3a8a").pack()
        
        Label(header, text="Sistema Integral de Gestión Académica", 
              font=("Arial", 12), bg="white", fg="#64748b").pack(pady=2)
        
        Label(header, text=f"Usuario: {self.usuario} | Rol: {self.rol}", 
              font=("Arial", 10, "bold"), bg="white", fg="#2563eb").pack(pady=5)

        # Contenedor para los botones de gestión y reportes
        wrap = Frame(self.panel_principal, bg="white")
        wrap.pack(fill='both', expand=True, padx=20, pady=20)

        # Frame para las gestiones
        gestion = LabelFrame(wrap, text="📊 Gestiones del Sistema", 
                           font=("Arial", 11, "bold"), bg="white", fg="#1f2937")
        gestion.grid(row=0, column=0, padx=12, pady=8, sticky='nsew')

        # Frame para los reportes
        reportes = LabelFrame(wrap, text="📈 Reportes y Estadísticas", 
                            font=("Arial", 11, "bold"), bg="white", fg="#1f2937")
        reportes.grid(row=0, column=1, padx=12, pady=8, sticky='nsew')

        # Configurar grid para expandirse
        wrap.columnconfigure(0, weight=1)
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(0, weight=1)

        # Opciones por permisos (no por rol directamente)
        if PermisosManager.tiene_permiso(self.rol, 'gestion_docentes'):
            Button(gestion, text="Gestión de Docentes", width=28,
                   bg="#2563eb", fg="white", command=self.abrir_docentes).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'gestion_estudiantes'):
            Button(gestion, text="Gestión de Estudiantes", width=28,
                   bg="#0ea5e9", fg="white", command=self.abrir_estudiantes).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'control_asistencia'):
            Button(gestion, text="Control de Asistencia (Estudiantes)", width=28,
                   bg="#22c55e", fg="white", command=self.abrir_asistencia).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'gestion_usuarios'):
            Button(gestion, text="Usuarios y Roles", width=28,
                   bg="#64748b", fg="white", command=self.abrir_usuarios).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'ver_reportes'):
            Button(gestion, text="Dashboard Estadísticas", width=28,
                   bg="#8b5cf6", fg="white", command=self.abrir_dashboard).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'backup_restore'):
            Button(gestion, text="Backup del Sistema", width=28,
                   bg="#f59e0b", fg="white", command=self.abrir_backup).pack(padx=12, pady=6)

        # Reportes visibles para todos con permiso
        if PermisosManager.tiene_permiso(self.rol, 'ver_reportes'):
            Button(reportes, text="Reporte General", width=30,
                   bg="#16a34a", fg="white", command=self.reporte_general).pack(padx=12, pady=6)
            Button(reportes, text="Reporte por Fecha", width=30,
                   bg="#f59e0b", fg="white", command=self.reporte_por_fecha).pack(padx=12, pady=6)
            Button(reportes, text="Búsqueda Avanzada", width=30,
                   bg="#8b5cf6", fg="white", command=self.busqueda_avanzada).pack(padx=12, pady=6)

        # Mostrar notificaciones al inicio
        self.root.after(1000, self.mostrar_notificaciones)

        # Botón salir
        Button(self.panel_principal, text="🚪 Salir del Sistema", width=18, 
               bg="#dc2626", fg="white", font=("Arial", 10, "bold"),
               command=self.salir_sistema).pack(pady=14)

    def abrir_docentes(self):
        GestorVentanas.abrir_ventana(self.root, GestionDocentes, "Gestión de Docentes")

    def abrir_estudiantes(self):
        GestorVentanas.abrir_ventana(self.root, GestionEstudiantes, "Gestión de Estudiantes Técnicos")

    def abrir_asistencia(self):
        GestorVentanas.abrir_ventana(self.root, GestionAsistencia, "Control de Asistencia - Estudiantes")

    def abrir_usuarios(self):
        GestorVentanas.abrir_ventana(self.root, GestionUsuarios, "Usuarios y Roles")

    def abrir_dashboard(self):
        GestorVentanas.abrir_ventana(self.root, Dashboard, "Dashboard - Estadísticas")

    def abrir_backup(self):
        GestorVentanas.abrir_ventana(self.root, GestionBackup, "Gestión de Backup")

    def reporte_general(self):
        GestorVentanas.abrir_ventana(self.root, ReporteGeneral, "Reporte General de Asistencia")

    def reporte_por_fecha(self):
        GestorVentanas.abrir_ventana(self.root, ReportePorFecha, "Reporte de Asistencia por Fecha") 

    def _on_close(self):
        """Manejar cierre de ventana""" 
        try:
            if hasattr(self, 'fondo_manager'):
                self.fondo_manager.limpiar()
            self.root.destroy()
        except:
            pass

    def mostrar_notificaciones(self):
        """Verifica y muestra notificaciones pendientes al iniciar sesión"""
        self.notificaciones.verificar_notificaciones_pendientes()
        if self.notificaciones.notificaciones:
            self.notificaciones.mostrar_notificaciones(self.root)

    def busqueda_avanzada(self):
        """Abre la ventana de búsqueda avanzada"""
        ventana_busqueda = Toplevel(self.root)
        ventana_busqueda.title("Búsqueda Avanzada - Estudiantes")
        ventana_busqueda.geometry("500x400")
        
        buscador = BuscadorAvanzado(self.db_manager)
        
        Label(ventana_busqueda, text="🔍 Búsqueda Avanzada", font=("Arial", 14, "bold")).pack(pady=10)
        
        frame_campos = Frame(ventana_busqueda)
        frame_campos.pack(pady=10, padx=20, fill='x')
        
        # Campos de búsqueda
        Label(frame_campos, text="Nombre:").grid(row=0, column=0, sticky='w', pady=5)
        entry_nombre = Entry(frame_campos, width=30)
        entry_nombre.grid(row=0, column=1, pady=5, padx=5)
        
        Label(frame_campos, text="Cédula:").grid(row=1, column=0, sticky='w', pady=5)
        entry_cedula = Entry(frame_campos, width=30)
        entry_cedula.grid(row=1, column=1, pady=5, padx=5)
        
        Label(frame_campos, text="Carrera:").grid(row=2, column=0, sticky='w', pady=5)
        entry_carrera = Entry(frame_campos, width=30)
        entry_carrera.grid(row=2, column=1, pady=5, padx=5)
        
        Label(frame_campos, text="Año:").grid(row=3, column=0, sticky='w', pady=5)
        entry_anio = Entry(frame_campos, width=30)
        entry_anio.grid(row=3, column=1, pady=5, padx=5)
        
        def realizar_busqueda():
            criterios = {
                'nombre': entry_nombre.get().strip(),
                'cedula': entry_cedula.get().strip(),
                'carrera': entry_carrera.get().strip(),
                'anio': entry_anio.get().strip()
            }
            
            resultados = buscador.buscar_estudiantes(criterios)
            
            # Mostrar resultados
            ventana_resultados = Toplevel(ventana_busqueda)
            ventana_resultados.title("Resultados de Búsqueda")
            ventana_resultados.geometry("800x400")
            
            tree = ttk.Treeview(ventana_resultados, columns=("id", "cedula", "nombres", "apellidos", "carrera", "anio"), show="headings")
            tree.heading("id", text="ID")
            tree.heading("cedula", text="Cédula")
            tree.heading("nombres", text="Nombres")
            tree.heading("apellidos", text="Apellidos")
            tree.heading("carrera", text="Carrera")
            tree.heading("anio", text="Año")
            
            for resultado in resultados:
                tree.insert("", "end", values=(
                    resultado['id'],
                    resultado['cedula'],
                    resultado['nombres'],
                    resultado['apellidos'],
                    resultado['carrera'],
                    resultado['anio']
                ))
            
            tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Botón exportar
            def exportar_resultados():
                success, message = ExportadorAvanzado.exportar_csv(
                    [tree.item(item)['values'] for item in tree.get_children()],
                    "resultados_busqueda",
                    ["ID", "Cédula", "Nombres", "Apellidos", "Carrera", "Año"]
                )
                if success:
                    messagebox.showinfo("Éxito", message)
                else:
                    messagebox.showerror("Error", message)
            
            Button(ventana_resultados, text="Exportar a CSV", command=exportar_resultados).pack(pady=10)
        
        Button(ventana_busqueda, text="Buscar", command=realizar_busqueda, bg="#2563eb", fg="white").pack(pady=10)
        
        self.auditoria.registrar_evento(self.usuario, "BUSQUEDA_AVANZADA", "Acceso a búsqueda avanzada")

    def salir_sistema(self):
        """Cierra el sistema de manera segura"""
        self.auditoria.registrar_evento(self.usuario, "LOGOUT", "Cierre de sesión")
        self.root.destroy()



# ==================== GESTIÓN DOCENTES ====================

class GestionDocentes:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Docentes")
        self.root.geometry("1100x700")  # ✅ Más ancho y alto
        self.root.configure (bg="#f9fafb")
        self.root.minsize(1000, 650)  # Tamaño mínimo)


# Aplicar fondo temático
        self.fondo_manager = FondoManager(root, "gestion_docentes")
        self.fondo_manager.aplicar_fondo()

        # Panel principal semi-transparente
        self.panel_principal = Frame(root, bg='white', bd=3, relief='raised')
        self.panel_principal.pack(fill=BOTH, expand=True, padx=20, pady=20)
 
         # Prevenir múltiples instancias
        self.root.focus_set()
        self.root.grab_set()

        header = Frame(self.root, bg="#f9fafb")
        header.pack(fill='x', pady=10)
        Label(header, text="📘 GESTIÓN DE DOCENTES", font=('Arial', 18, 'bold'), bg="#f9fafb", fg="#2563eb").pack(side=LEFT, padx=15)
        Button(header, text="Cerrar", bg="#64748b", fg="white", command=root.destroy).pack(side=RIGHT, padx=15)

    

        # Contenedor principal con scroll
        main_container = Frame(self.root, bg="#f9fafb")
        main_container.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Frame del formulario
        form_container = Frame(main_container, bg="#f9fafb")
        form_container.pack(fill=X, pady=10)

        # Crear un frame para el formulario con más espacio
        form = Frame(form_container, bg="#f9fafb", padx=20, pady=15)
        form.pack(fill=X)

        # Fila 1 - Cédula y Nombres
        Label(form, text="Cédula/ID:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=8, sticky=E)
        self.txt_cedula = Entry(form, width=25, font=("Arial", 10))
        self.txt_cedula.grid(row=0, column=1, padx=10, pady=8, sticky=W)
        Label(form, text="Ejemplo: 001-080888-8888A", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=0, column=2, sticky=W, padx=10)
        
        Label(form, text="Nombres:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=10, pady=8, sticky=E)
        self.txt_nombres = Entry(form, width=30, font=("Arial", 10))
        self.txt_nombres.grid(row=0, column=4, padx=10, pady=8, sticky=W)
        Label(form, text="Solo letras y espacios", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=0, column=5, sticky=W, padx=10)

        # Fila 2 - Apellidos y Especialidad
        Label(form, text="Apellidos:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=8, sticky=E)
        self.txt_apellido = Entry(form, width=25, font=("Arial", 10))
        self.txt_apellido.grid(row=1, column=1, padx=10, pady=8, sticky=W)
        Label(form, text="Solo letras y espacios", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=1, column=2, sticky=W, padx=10)
        
        Label(form, text="Especialidad:*", bg="#f9fafb", fg="red", font=("Arial", 10, "bold")).grid(row=1, column=3, padx=10, pady=8, sticky=E)
        self.txt_especialidad = Entry(form, width=30, font=("Arial", 10))
        self.txt_especialidad.grid(row=1, column=4, padx=10, pady=8, sticky=W)
        Label(form, text="Ejemplo: Matemáticas, Informática", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=1, column=5, sticky=W, padx=10)

        # Fila 3 - Correo
        Label(form, text="Correo Electrónico:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=10, pady=8, sticky=E)
        self.txt_email = Entry(form, width=25, font=("Arial", 10))
        self.txt_email.grid(row=2, column=1, padx=10, pady=8, sticky=W)
        Label(form, text="Ejemplo: juan.perez@instituto.edu.ni", font=("Arial", 9), fg="gray", bg="#f9fafb", wraplength=250).grid(row=2, column=2, columnspan=2, sticky=W, padx=10)
        
        # Fila 3 - Teléfono
        Label(form, text="Teléfono:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=2, column=3, padx=10, pady=8, sticky=E)
        self.txt_telefono = Entry(form, width=30, font=("Arial", 10))
        self.txt_telefono.grid(row=2, column=4, padx=10, pady=8, sticky=W)
        Label(form, text="Ejemplo: 8888-8888 o 12345678", font=("Arial", 9), fg="gray", bg="#f9fafb").grid(row=2, column=5, sticky=W, padx=10)

        # Separador
        separator = Frame(form_container, height=2, bg="#e5e7eb")
        separator.pack(fill=X, pady=15)

        # Botones de acción
        acciones = Frame(form_container, bg="#f9fafb", pady=10)
        acciones.pack()
        
        Button(acciones, text="➕ Agregar Docente", bg="#2563eb", fg="white", 
               font=("Arial", 11, "bold"), padx=15, pady=8, command=self.agregar_docente).grid(row=0, column=0, padx=10)
        Button(acciones, text="🔄 Actualizar Lista", bg="#16a34a", fg="white", 
               font=("Arial", 11), padx=15, pady=8, command=self.llenar_docentes).grid(row=0, column=1, padx=10)
        Button(acciones, text="❌ Desactivar", bg="#dc2626", fg="white", 
               font=("Arial", 11), padx=15, pady=8, command=self.desactivar_docente).grid(row=0, column=2, padx=10)
        Button(acciones, text="🧹 Limpiar Campos", bg="#f59e0b", fg="white", 
               font=("Arial", 11), padx=15, pady=8, command=self.limpiar_campos).grid(row=0, column=3, padx=10)

        # Validación en tiempo real
        self.txt_cedula.bind("<FocusOut>", self.validar_cedula_tiempo_real)
        self.txt_nombres.bind("<FocusOut>", self.validar_nombres_tiempo_real)
        self.txt_apellido.bind("<FocusOut>", self.validar_apellido_tiempo_real)
        self.txt_email.bind("<FocusOut>", self.validar_correo_tiempo_real)
        self.txt_telefono.bind("<FocusOut>", self.validar_telefono_tiempo_real)

        # Treeview con scroll
        tree_frame = Frame(main_container, bg="#f9fafb")
        tree_frame.pack(fill=BOTH, expand=True, pady=10)

        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        cols = ("id_docente", "cedula", "nombres", "apellido", "especialidad", "email", "telefono", "estado")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15, yscrollcommand=scrollbar.set)
        
        headers = {
            "id_docente": "ID", "cedula": "Cédula", "nombres": "Nombres", 
            "apellido": "Apellidos", "especialidad": "Especialidad", 
            "email": "Correo", "telefono": "Teléfono", "estado": "Estado"
        }
        
        # Configurar columnas más anchas
        for col in cols:
            self.tree.heading(col, text=headers.get(col, col.capitalize()))
            if col == "id_docente":
                self.tree.column(col, width=60, anchor=CENTER)
            elif col in ["nombres", "apellido", "especialidad", "email"]:
                self.tree.column(col, width=180)
            else:
                self.tree.column(col, width=120)
        
        self.tree.pack(fill=BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)


        # Agregar estos bindings después de crear los campos:
        self.txt_cedula.bind('<Return>', lambda event: self.txt_nombres.focus_set())
        self.txt_nombres.bind('<Return>', lambda event: self.txt_apellido.focus_set())
        self.txt_apellido.bind('<Return>', lambda event: self.txt_especialidad.focus_set())
        self.txt_especialidad.bind('<Return>', lambda event: self.txt_email.focus_set())
        self.txt_email.bind('<Return>', lambda event: self.txt_telefono.focus_set())
        self.txt_telefono.bind('<Return>', lambda event: self.agregar_docente())


        # Leyenda de campos obligatorios
        leyenda = Frame(main_container, bg="#f9fafb")
        leyenda.pack(fill=X, pady=5)
        Label(leyenda, text="* Campos obligatorios", font=("Arial", 9, "italic"), 
              fg="red", bg="#f9fafb").pack(side=LEFT)

        self.llenar_docentes()

    # ==================== VALIDACIONES EN TIEMPO REAL ====================

    def validar_cedula_tiempo_real(self, event=None):
        cedula = self.txt_cedula.get().strip()
        if cedula:
            if validar_cedula(cedula):
                self.txt_cedula.config(bg="#f0fff4")  # Verde claro
            else:
                self.txt_cedula.config(bg="#fff0f0")  # Rojo claro
        else:
            self.txt_cedula.config(bg="white")

    def validar_nombres_tiempo_real(self, event=None):
        nombres = self.txt_nombres.get().strip()
        if nombres:
            if validar_solo_texto(nombres):
                self.txt_nombres.config(bg="#f0fff4")
            else:
                self.txt_nombres.config(bg="#fff0f0")
        else:
            self.txt_nombres.config(bg="white")

    def validar_apellido_tiempo_real(self, event=None):
        apellido = self.txt_apellido.get().strip()
        if apellido:
            if validar_solo_texto(apellido):
                self.txt_apellido.config(bg="#f0fff4")
            else:
                self.txt_apellido.config(bg="#fff0f0")
        else:
            self.txt_apellido.config(bg="white")

    def validar_correo_tiempo_real(self, event=None):
        email = self.txt_email.get().strip()
        if email:
            if validar_correo(email):
                self.txt_email.config(bg="#f0fff4")
            else:
                self.txt_email.config(bg="#fff0f0")
        else:
            self.txt_email.config(bg="white")

    def validar_telefono_tiempo_real(self, event=None):
        telefono = self.txt_telefono.get().strip()
        if telefono:
            if validar_telefono(telefono):
                self.txt_telefono.config(bg="#f0fff4")
            else:
                self.txt_telefono.config(bg="#fff0f0")
        else:
            self.txt_telefono.config(bg="white")

    # ==================== FUNCIÓN PRINCIPAL AGREGAR ====================

    def agregar_docente(self):
        ced = self.txt_cedula.get().strip()
        nom = self.txt_nombres.get().strip()
        ape = self.txt_apellido.get().strip()
        esp = self.txt_especialidad.get().strip()
        email = self.txt_email.get().strip()
        tel = self.txt_telefono.get().strip()
        
        # Validaciones obligatorias
        if not (ced and nom and ape and esp):
            messagebox.showwarning("Atención", "Complete los campos obligatorios (*).")
            return
        
        # Validación de cédula
        if not validar_cedula(ced):
            mostrar_error_cedula()
            self.txt_cedula.focus_set()
            return
        
        # Validación de nombres (solo texto)
        if not validar_solo_texto(nom):
            mostrar_error_texto("nombres")
            self.txt_nombres.focus_set()
            return
        
        # Validación de apellidos (solo texto)
        if not validar_solo_texto(ape):
            mostrar_error_texto("apellidos")
            self.txt_apellido.focus_set()
            return
        
        # Validación de correo
        if email and not validar_correo(email):
            mostrar_error_correo()
            self.txt_email.focus_set()
            return
        
        # Validación de teléfono
        if tel and not validar_telefono(tel):
            mostrar_error_telefono()
            self.txt_telefono.focus_set()
            return
        
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO docentes (cedula, nombres, apellido, especialidad, email, telefono) VALUES (?, ?, ?, ?, ?, ?)",
                      (ced, nom, ape, esp, email, tel))
            conn.commit()
            messagebox.showinfo("Éxito", "Docente agregado correctamente.")
            self.llenar_docentes()
            self.limpiar_campos()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "La cédula ya existe en el sistema.")
        finally:
            conn.close()

    def limpiar_campos(self):
        """Limpia todos los campos y restablece colores"""
        campos = [self.txt_cedula, self.txt_nombres, self.txt_apellido, 
                 self.txt_especialidad, self.txt_email, self.txt_telefono]
        for campo in campos:
            campo.delete(0, END)
            campo.config(bg="white")

    def llenar_docentes(self):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT id_docente, cedula, nombres, apellido, especialidad, email, telefono, estado FROM docentes ORDER BY id_docente DESC")
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    def desactivar_docente(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un docente.")
            return
        id_doc = self.tree.item(sel[0])["values"][0]
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE docentes SET estado='INACTIVO' WHERE id_docente=?", (id_doc,))
        conn.commit()
        conn.close()
        self.llenar_docentes()
        messagebox.showinfo("Actualizado", "Docente desactivado.")

class GestionAsistencia:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Asistencia - Estudiantes")
        self.root.geometry("1200x700")
        self.root.configure(bg="#dbeafe")

        # Aplicar fondo temático
        self.fondo_manager = FondoManager(root, "gestion_asistencia", "Educación Clásica")
        self.fondo_manager.aplicar_fondo()

        # Panel principal semi-transparente
        self.panel_principal = Frame(root, bg='white', bd=3, relief='raised')
        self.panel_principal.pack(fill=BOTH, expand=True, padx=20, pady=20)

        Label(self.panel_principal, text="📋 Control de Asistencia - Estudiantes", font=("Arial", 16, "bold"), bg="white", fg="#1e3a8a").pack(pady=10)
        frm = Frame(self.panel_principal, bg="white"); frm.pack(pady=6)

        Label(frm, text="Estudiante:", bg="#dbeafe").grid(row=0, column=0, sticky=E, padx=6, pady=6)
        self.cmb_estudiante = ttk.Combobox(frm, width=40, state="readonly"); self.cmb_estudiante.grid(row=0, column=1, padx=6, pady=6)
        Label(frm, text="Fecha:", bg="#dbeafe").grid(row=0, column=2, sticky=E, padx=6, pady=6)
        self.fecha_var = StringVar(); self.fecha_var.set(datetime.now().strftime("%Y-%m-%d"))
        Entry(frm, textvariable=self.fecha_var, width=18, state='readonly').grid(row=0, column=3, padx=6, pady=6)

        Label(frm, text="Estado:", bg="#dbeafe").grid(row=1, column=0, sticky=E, padx=6, pady=6)
        self.cmb_estado = ttk.Combobox(frm, values=["Presente", "Tarde", "Ausente", "Justificado"], width=20, state='readonly'); self.cmb_estado.grid(row=1, column=1, padx=6, pady=6)
        self.cmb_estado.set("Presente")
        Label(frm, text="Observaciones:", bg="#dbeafe").grid(row=1, column=2, sticky=E, padx=6, pady=6)
        self.txt_obs = Entry(frm, width=30); self.txt_obs.grid(row=1, column=3, padx=6, pady=6)

        btns = Frame(self.root, bg="#dbeafe"); btns.pack(pady=6)
        Button(btns, text="Registrar Entrada", bg="#2563eb", fg="white", command=self.registrar_entrada).grid(row=0, column=0, padx=6)
        Button(btns, text="Registrar Salida (selección)", bg="#16a34a", fg="white", command=self.registrar_salida).grid(row=0, column=1, padx=6)
        Button(btns, text="Actualizar Lista", bg="#64748b", fg="white", command=self.llenar_tabla).grid(row=0, column=2, padx=6)

        cols = ("id_asistencia", "estudiante", "fecha", "hora_entrada", "hora_salida", "estado", "observaciones")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        headers = {"id_asistencia":"ID","estudiante":"Estudiante","fecha":"Fecha","hora_entrada":"Hora Entrada","hora_salida":"Hora Salida","estado":"Estado","observaciones":"Observaciones"}
        for col in cols:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=130)
        self.tree.column("id_asistencia", width=50)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

        self.cargar_estudiantes()
        self.crear_tabla()
        self.llenar_tabla()

    def crear_tabla(self):
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS asistencia (
                id_asistencia INTEGER PRIMARY KEY AUTOINCREMENT,
                id_estudiante INTEGER,
                fecha TEXT,
                hora_entrada TEXT,
                hora_salida TEXT,
                estado TEXT,
                observaciones TEXT,
                FOREIGN KEY(id_estudiante) REFERENCES estudiantes(id)
            )
        """)
        conn.commit(); conn.close()

    def cargar_estudiantes(self):
        conn = sqlite3.connect(DB); c = conn.cursor()
        # si la tabla no existe o está vacía, la combobox quedará vacía
        try:
            c.execute("SELECT id, nombres || ' ' || apellidos FROM estudiantes ORDER BY nombres")
            rows = c.fetchall()
        except Exception:
            rows = []
        conn.close()
        self.estudiantes_map = {nombre: id_ for id_, nombre in rows}
        self.cmb_estudiante['values'] = list(self.estudiantes_map.keys())
        if rows:
            self.cmb_estudiante.current(0)

    def registrar_entrada(self):
        estudiante = self.cmb_estudiante.get()
        if not estudiante:
            messagebox.showwarning("Atención", "Seleccione un estudiante.")
            return
        id_est = self.estudiantes_map.get(estudiante)
        fecha = self.fecha_var.get()
        hora = datetime.now().strftime("%H:%M:%S")
        estado = self.cmb_estado.get()
        obs = self.txt_obs.get().strip()
        conn = sqlite3.connect(DB); c = conn.cursor()
        # evitar duplicados: si ya hay entrada hoy para ese estudiante
        c.execute("SELECT id_asistencia FROM asistencia WHERE id_estudiante=? AND fecha=?", (id_est, fecha))
        if c.fetchone():
            messagebox.showinfo("Información", "Ya existe una entrada para este estudiante hoy.")
            conn.close(); return
        c.execute("INSERT INTO asistencia (id_estudiante, fecha, hora_entrada, estado, observaciones) VALUES (?, ?, ?, ?, ?)",
                  (id_est, fecha, hora, estado, obs))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Entrada registrada correctamente.")
        self.llenar_tabla()

    def registrar_salida(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un registro en la tabla para marcar salida.")
            return
        id_asist = self.tree.item(sel[0])['values'][0]
        hora_salida = datetime.now().strftime("%H:%M:%S")
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE asistencia SET hora_salida=? WHERE id_asistencia=?", (hora_salida, id_asist))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Salida registrada correctamente.")
        self.llenar_tabla()

    def llenar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("""
            SELECT a.id_asistencia,
                   e.nombres || ' ' || e.apellidos as estudiante,
                   a.fecha,
                   IFNULL(a.hora_entrada, '-') as hora_entrada,
                   IFNULL(a.hora_salida, '-') as hora_salida,
                   a.estado,
                   IFNULL(a.observaciones, '') as observaciones
            FROM asistencia a
            LEFT JOIN estudiantes e ON a.id_estudiante = e.id
            ORDER BY a.id_asistencia DESC
        """)
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

# ==================== GESTIÓN USUARIOS ====================

class GestionUsuarios:
    def __init__(self, root):
        self.root = root
        self.root.title("Usuarios y Roles")
        self.root.geometry("800x550")
        self.root.configure(bg="#f9fafb")
        Label(self.root, text="👥 Usuarios y Roles", font=("Arial", 16, "bold"), bg="#f9fafb", fg="#2563eb").pack(pady=8)

        frm = Frame(self.root, bg="#f9fafb"); frm.pack(pady=6)
        Label(frm, text="Usuario:").grid(row=0, column=0, padx=6, pady=4, sticky=E)
        self.txt_usuario = Entry(frm, width=24); self.txt_usuario.grid(row=0, column=1, padx=6, pady=4)
        Label(frm, text="Contraseña:").grid(row=1, column=0, padx=6, pady=4, sticky=E)
        self.txt_password = Entry(frm, width=24, show="*"); self.txt_password.grid(row=1, column=1, padx=6, pady=4)
        Label(frm, text="Rol:").grid(row=2, column=0, padx=6, pady=4, sticky=E)
        self.cmb_rol = ttk.Combobox(frm, values=["Administrador", "Docente", "Estudiante"], width=20, state="readonly"); self.cmb_rol.grid(row=2, column=1, padx=6, pady=4); self.cmb_rol.current(2)

        botones = Frame(self.root, bg="#f9fafb"); botones.pack(pady=6)
        Button(botones, text="Crear usuario", bg="#2563eb", fg="white", command=self.crear_usuario).grid(row=0, column=0, padx=6)
        Button(botones, text="Actualizar lista", bg="#16a34a", fg="white", command=self.llenar_tabla).grid(row=0, column=1, padx=6)

        self.tree = ttk.Treeview(self.root, columns=("id","usuario","rol"), show="headings")
        for col in ("id","usuario","rol"):
            self.tree.heading(col, text=col.capitalize()); self.tree.column(col, width=200)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

        self.llenar_tabla()

    def crear_usuario(self):
        u = self.txt_usuario.get().strip()
        p = self.txt_password.get().strip()
        rol = self.cmb_rol.get().strip()
        if not (u and p):
            messagebox.showwarning("Atención", "Complete usuario y contraseña.")
            return
        ok, msg = create_user(u, p, rol)
        if not ok:
            messagebox.showerror("Error", msg)
            return
        messagebox.showinfo("Éxito", "Usuario creado.")
        self.txt_usuario.delete(0, END); self.txt_password.delete(0, END)
        self.llenar_tabla()

    def llenar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("SELECT id_usuario, usuario, rol FROM usuarios ORDER BY id_usuario DESC")
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

# ==================== REPORTES ====================

class ReporteGeneral:
    def __init__(self, root):
        self.root = root
        self.root.title("Reporte General")
        self.root.geometry("900x520")
        Label(self.root, text="Reporte General de Asistencia", font=("Arial", 14, "bold")).pack(pady=12)
        tree = ttk.Treeview(self.root, columns=("id","estudiante","fecha","hora_entrada","hora_salida","estado"), show="headings")
        for col in ("id","estudiante","fecha","hora_entrada","hora_salida","estado"):
            tree.heading(col, text=col.capitalize()); tree.column(col, width=140)
        tree.pack(fill="both", expand=True, padx=10, pady=8)
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("""
            SELECT a.id_asistencia, e.nombres || ' ' || e.apellidos, a.fecha, a.hora_entrada, IFNULL(a.hora_salida, '-'), a.estado
            FROM asistencia a
            LEFT JOIN estudiantes e ON a.id_estudiante = e.id
            ORDER BY a.id_asistencia DESC
        """)
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

class ReportePorFecha:
    def __init__(self, root):
        self.root = root
        self.root.title("Reporte por Fecha")
        self.root.geometry("900x520")
        frm = Frame(self.root); frm.pack(pady=8)
        Label(frm, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, padx=6, pady=6)
        self.txt_fecha = Entry(frm); self.txt_fecha.grid(row=0, column=1, padx=6, pady=6); self.txt_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        Button(frm, text="Buscar", command=self.buscar).grid(row=0, column=2, padx=6)
        self.tree = ttk.Treeview(self.root, columns=("id","estudiante","fecha","entrada","salida","estado"), show="headings")
        for col in ("id","estudiante","fecha","entrada","salida","estado"):
            self.tree.heading(col, text=col.capitalize()); self.tree.column(col, width=140)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

    def buscar(self):
        fecha = self.txt_fecha.get().strip()
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("""
            SELECT a.id_asistencia, e.nombres || ' ' || e.apellidos, a.fecha, a.hora_entrada, IFNULL(a.hora_salida,'-'), a.estado
            FROM asistencia a
            LEFT JOIN estudiantes e ON a.id_estudiante = e.id
            WHERE a.fecha=?
            ORDER BY a.id_asistencia DESC
        """, (fecha,))
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()
# ==================== CONFIGURACIÓN DE FONDOS PERSONALIZADOS ====================

def configurar_fondos_personalizados():
    """Guía para agregar fondos personalizados"""
    instrucciones = """
    🎨 CONFIGURACIÓN DE FONDOS PERSONALIZADOS
    
    Para agregar tus propios fondos:
    
    1. Crea una carpeta llamada 'fondos' en el mismo directorio del programa
    2. Agrega imágenes con estos nombres preferidos:
    
       FONDOS PARA LOGIN:
       - fondo_rdario1.jpg (Recomendado: 720x460)
       - fondo_rdario2.jpg
       - fondo_rdario3.jpg
       
       FONDOS PARA MENÚ PRINCIPAL:
       - fondo_aula.jpg (Recomendado: 920x520)
       - fondo_biblioteca.jpg
       
       FONDOS PARA GESTIONES:
       - fondo_libros.jpg
       - fondo_graduacion.jpg
       - fondo_estudiantes.jpg
    
    3. Formatos soportados: JPG, PNG, GIF (animados)
    4. Tamaño recomendado: Igual o mayor al tamaño de la ventana
    
    Los GIFs animados se reproducirán automáticamente como fondo.
    """
    print(instrucciones)

# ==================== INICIALIZACIÓN MEJORADA ====================

def insertar_datos_prueba():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    nombres = ["Juan", "Carlos", "Ana", "Pedro", "Luis", "María", "Sofía", "Jorge", "Elena", "Andrés"]
    apellidos = ["Martínez", "López", "García", "Hernández", "Torres", "Gómez", "Ramírez", "Castillo", "Rivas"]

    # Insertar 20 estudiantes aleatorios
    for _ in range(20):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        cedula = f"{random.randint(100_000, 900_000)}-{random.randint(1000, 9999)}"
        carrera = random.choice(["Técnico en Informática", "Técnico en Electrónica", "Técnico en Administración"])
        anio = random.choice(["1", "2", "3"])
        seccion = random.choice(["A", "B", "C"])

        c.execute("""
            INSERT INTO estudiantes (cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cedula, nombre, apellido, carrera, anio, seccion, "8888-0000", "Managua"))

    # Insertar 10 docentes aleatorios
    especialidades = ["Informática", "Matemática", "Electrónica", "Inglés", "Física"]

    for _ in range(10):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        cedula = f"{random.randint(100_000, 900_000)}-{random.randint(1000, 9999)}"
        esp = random.choice(especialidades)

        c.execute("""
            INSERT INTO docentes (cedula, nombres, apellido, especialidad, email, telefono, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cedula, nombre, apellido, esp, f"{nombre.lower()}@gmail.com", "8888-2222", "ACTIVO"))

    conn.commit()
    conn.close()
    print("📌 Datos de prueba insertados correctamente")


    # ==================== INICIALIZACIÓN DEL SISTEMA ====================

def mostrar_instrucciones_fondos():
    """Muestra instrucciones para personalizar fondos"""
    instrucciones = """
    🎨 SISTEMA DE FONDOS PERSONALIZADOS - INSTITUTO RUBÉN DARÍO
    
    📁 CARPETA DE FONDOS: 'fondos_instituto'
    
    Para personalizar los fondos del sistema:
    
    1. 📸 AGREGAR TUS PROPIAS IMÁGENES:
       - Coloca tus imágenes en la carpeta 'fondos_instituto'
       - Formatos soportados: JPG, PNG, GIF
       - Tamaño recomendado: 800x600 o superior
       
    2. 🏫 FONDOS RECOMENDADOS:
       - Logo del Instituto Rubén Darío
       - Fotos del campus y aulas
       - Imágenes de actividades estudiantiles
       - Fondos con los colores institucionales
       
    3. 🎭 TEMAS DISPONIBLES:
       - Instituto Rubén Darío
       - Educación Nicaragüense  
       - Fondos Animados
       - Colores Institucionales
       
    4. ⚙️ CONFIGURACIÓN AUTOMÁTICA:
       - El sistema crea fondos por defecto al iniciar
       - Se pueden reemplazar con tus propias imágenes
       - Los GIFs se animan automáticamente
       
    ¡Personaliza tu sistema con la identidad de tu instituto!
    """
    print(instrucciones)

# ==================== SISTEMA DE FONDOS SIMPLIFICADO Y FUNCIONAL ====================

class SistemaFondos:
    @staticmethod
    def inicializar_fondos():
        """Inicializa el sistema de fondos de manera simple"""
        directorio_fondos = "fondos_instituto"
        if not os.path.exists(directorio_fondos):
            os.makedirs(directorio_fondos)
            print("✅ Carpeta de fondos creada: 'fondos_instituto'")
            
            # Crear archivo de instrucciones
            with open(os.path.join(directorio_fondos, "INSTRUCCIONES.txt"), "w", encoding="utf-8") as f:
                f.write("""INSTRUCCIONES PARA FONDOS PERSONALIZADOS - INSTITUTO RUBÉN DARÍO

1. AGREGA TUS IMÁGENES: Coloca archivos JPG, PNG o GIF en esta carpeta
2. NOMBRES SUGERIDOS:
   - fondo_login.jpg
   - fondo_menu_principal.jpg  
   - fondo_estudiantes.jpg
   - fondo_docentes.jpg
3. TAMAÑO RECOMENDADO: 800x600 o mayor
4. Los GIFs se animarán automáticamente

¡Personaliza tu sistema con imágenes de tu instituto!
                """)
            
            messagebox.showinfo("Sistema de Fondos", 
                              "🎨 Se ha creado la carpeta 'fondos_instituto'\n\n" +
                              "📸 Puedes agregar tus propias imágenes:\n" +
                              "   - fondo_login.jpg\n" +
                              "   - fondo_menu_principal.jpg\n" +
                              "   - fondo_estudiantes.jpg\n" +
                              "   - fondo_docentes.jpg\n\n" +
                              "Los GIFs se animarán automáticamente.")
        
        return directorio_fondos

    @staticmethod
    def obtener_fondo(tipo_ventana):
        """Obtiene la ruta del fondo para un tipo de ventana"""
        directorio = "fondos_instituto"
        
        # Mapeo de nombres de archivo por tipo de ventana
        mapeo_fondos = {
            "login": ["fondo_login.jpg", "fondo_principal.jpg", "fondo_rdario.jpg"],
            "menu_principal": ["fondo_menu_principal.jpg", "fondo_aula.jpg", "fondo_instituto.jpg"],
            "gestion_estudiantes": ["fondo_estudiantes.jpg", "fondo_libros.jpg", "fondo_educacion.jpg"],
            "gestion_docentes": ["fondo_docentes.jpg", "fondo_graduacion.jpg", "fondo_biblioteca.jpg"]
        }
        
        # Buscar archivos para este tipo de ventana
        if tipo_ventana in mapeo_fondos:
            for nombre_archivo in mapeo_fondos[tipo_ventana]:
                ruta = os.path.join(directorio, nombre_archivo)
                if os.path.exists(ruta):
                    return ruta
        
        # Si no se encuentra ningún archivo específico, buscar cualquier imagen
        if os.path.exists(directorio):
            for archivo in os.listdir(directorio):
                if archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    return os.path.join(directorio, archivo)
        
        return None

class FondoManager:
    def __init__(self, ventana, tipo_ventana, tema="default"):
        self.ventana = ventana
        self.tipo_ventana = tipo_ventana
        self.tema = tema
        self.canvas = None
        self.imagen_fondo = None
        self.gif_frames = []
        self.gif_index = 0
        self.animacion_activa = False
        
    def aplicar_fondo(self):
        """Aplica el fondo a la ventana - MEJORADO PARA GIFs"""
        if not PIL_AVAILABLE:
            self._aplicar_fondo_color()
            return
            
        ruta_fondo = self._obtener_ruta_fondo()
        
        if not ruta_fondo:
            self._aplicar_fondo_color()
            return
        
        try:
            if ruta_fondo.lower().endswith('.gif'):
                self._aplicar_fondo_gif(ruta_fondo)
            else:
                self._aplicar_fondo_imagen(ruta_fondo)
                
            # Asegurar que el fondo esté detrás de todo
            self._configurar_capas()
            
        except Exception as e:
            print(f"❌ Error cargando fondo {ruta_fondo}: {e}")
            self._aplicar_fondo_color()
    
    def _obtener_ruta_fondo(self):
        """Obtiene la ruta del fondo para el tipo de ventana"""
        directorio = "fondos_instituto"
        
        if not os.path.exists(directorio):
            return None
            
        # Mapeo de nombres de archivo por tipo de ventana
        mapeo_fondos = {
            "login": ["fondo_login.gif", "fondo_login.jpg", "fondo_principal.gif"],
            "menu_principal": ["fondo_menu.gif", "fondo_aula.gif", "fondo_instituto.gif"],
            "gestion_estudiantes": ["fondo_estudiantes.gif", "fondo_libros.gif"],
            "gestion_docentes": ["fondo_docentes.gif", "fondo_graduacion.gif"],
            "gestion_asistencia": ["fondo_asistencia.gif", "fondo_reloj.gif"]
        }
        
        # Buscar archivos para este tipo de ventana
        if self.tipo_ventana in mapeo_fondos:
            for nombre_archivo in mapeo_fondos[self.tipo_ventana]:
                ruta = os.path.join(directorio, nombre_archivo)
                if os.path.exists(ruta):
                    return ruta
        
        # Buscar cualquier GIF o imagen en el directorio
        for archivo in os.listdir(directorio):
            if archivo.lower().endswith(('.gif', '.jpg', '.jpeg', '.png')):
                return os.path.join(directorio, archivo)
        
        return None
    
    def _aplicar_fondo_color(self):
        """Aplica fondo de color sólido"""
        colores = {
            "login": "#1e3a8a",
            "menu_principal": "#2563eb", 
            "gestion_estudiantes": "#1e40af",
            "gestion_docentes": "#3730a3",
            "gestion_asistencia": "#1e3a8a"
        }
        color = colores.get(self.tipo_ventana, "#1e40af")
        self.ventana.configure(bg=color)
    
    def _aplicar_fondo_gif(self, ruta_gif):
        """Aplica GIF animado como fondo - MEJORADO"""
        try:
            # Crear canvas para el fondo
            self.canvas = Canvas(self.ventana, highlightthickness=0, bg='white')
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Cargar frames del GIF
            gif = Image.open(ruta_gif)
            self.gif_frames = []
            
            for frame in ImageSequence.Iterator(gif):
                # Convertir a RGB si es necesario
                if frame.mode != 'RGB':
                    frame = frame.convert('RGB')
                self.gif_frames.append(frame)
            
            self.gif_index = 0
            self.animacion_activa = True
            
            # Iniciar animación
            self._animar_gif()
            
            print(f"✅ GIF cargado: {ruta_gif} - {len(self.gif_frames)} frames")
            
        except Exception as e:
            print(f"❌ Error cargando GIF: {e}")
            self._aplicar_fondo_color()
    
    def _animar_gif(self):
        """Anima el GIF - MEJORADO"""
        if not self.animacion_activa or not self.gif_frames:
            return
            
        try:
            # Obtener frame actual
            frame_actual = self.gif_frames[self.gif_index]
            
            # Redimensionar al tamaño de la ventana
            ancho = self.ventana.winfo_width()
            alto = self.ventana.winfo_height()
            
            if ancho > 1 and alto > 1:
                frame_redim = frame_actual.resize((ancho, alto), Image.LANCZOS)
                self.imagen_fondo = ImageTk.PhotoImage(frame_redim)
                
                # Limpiar y dibujar
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, image=self.imagen_fondo, anchor="nw")
            
            # Siguiente frame
            self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
            
            # Programar próximo frame (velocidad ajustable)
            delay = 100  # ms entre frames
            self.ventana.after(delay, self._animar_gif)
            
        except Exception as e:
            print(f"Error en animación GIF: {e}")
            self.animacion_activa = False
    
    def _aplicar_fondo_imagen(self, ruta_imagen):
        """Aplica imagen de fondo estática"""
        try:
            self.canvas = Canvas(self.ventana, highlightthickness=0)
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            
            imagen = Image.open(ruta_imagen)
            self._actualizar_fondo_imagen(imagen)
            
            # Redimensionar cuando cambie el tamaño
            self.ventana.bind('<Configure>', lambda e: self._actualizar_fondo_imagen(imagen))
            
        except Exception as e:
            print(f"Error aplicando fondo imagen: {e}")
            self._aplicar_fondo_color()
    
    def _actualizar_fondo_imagen(self, imagen):
        """Actualiza imagen de fondo estática"""
        if not self.canvas:
            return
            
        try:
            ancho = self.ventana.winfo_width()
            alto = self.ventana.winfo_height()
            
            if ancho > 1 and alto > 1:
                # Redimensionar manteniendo aspecto
                ratio_orig = imagen.width / imagen.height
                ratio_nuevo = ancho / alto
                
                if ratio_orig > ratio_nuevo:
                    nuevo_ancho = ancho
                    nuevo_alto = int(ancho / ratio_orig)
                else:
                    nuevo_alto = alto
                    nuevo_ancho = int(alto * ratio_orig)
                
                imagen_redim = imagen.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
                self.imagen_fondo = ImageTk.PhotoImage(imagen_redim)
                
                self.canvas.delete("all")
                self.canvas.create_image(ancho//2, alto//2, image=self.imagen_fondo, anchor="center")
                
        except Exception as e:
            print(f"Error actualizando fondo: {e}")
    
    def _configurar_capas(self):
        """Asegura que el fondo esté en la capa inferior"""
        if self.canvas:
            self.canvas.lower()  # Mover a la capa más baja
    
    def limpiar(self):
        """Limpia recursos de animación"""
        self.animacion_activa = False
        if self.canvas:
            try:
                self.canvas.destroy()
            except:
                pass
# ==================== CREADOR DE GIFs DE EJEMPLO ====================

class CreadorGifsEjemplo:
    @staticmethod
    def crear_gifs_ejemplo():
        """Crea GIFs animados de ejemplo para el sistema"""
        directorio = "fondos_instituto"
        os.makedirs(directorio, exist_ok=True)
        
        gifs_creados = []
        
        # GIF para login - Animación suave de colores
        if not os.path.exists(os.path.join(directorio, "fondo_login.gif")):
            try:
                CreadorGifsEjemplo._crear_gif_login()
                gifs_creados.append("fondo_login.gif")
            except Exception as e:
                print(f"❌ No se pudo crear GIF de login: {e}")
        
        # GIF para menú principal - Efecto de partículas
        if not os.path.exists(os.path.join(directorio, "fondo_menu.gif")):
            try:
                CreadorGifsEjemplo._crear_gif_menu()
                gifs_creados.append("fondo_menu.gif")
            except Exception as e:
                print(f"❌ No se pudo crear GIF de menú: {e}")
        
        if gifs_creados:
            print(f"✅ GIFs creados: {', '.join(gifs_creados)}")
        else:
            print("📁 GIFs de ejemplo ya existen")
    
    @staticmethod
    def _crear_gif_login():
        """Crea un GIF animado para el login"""
        from PIL import ImageDraw, ImageFont
        
        frames = []
        width, height = 800, 600
        
        # Crear frames con gradiente animado
        for i in range(10):
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Gradiente azul animado
            for y in range(height):
                # Color que cambia con el frame
                r = int(30 + (i * 2))
                g = int(64 + (i * 3))
                b = int(138 + (i * 4))
                color = (r, g, b)
                draw.line([(0, y), (width, y)], fill=color)
            
            # Añadir texto institucional semi-transparente
            try:
                # Intentar cargar fuente por defecto
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except:
                    try:
                        font = ImageFont.truetype("Arial", 36)
                    except:
                        font = ImageFont.load_default()
                
                text = "Instituto Rubén Darío"
                # Calcular posición del texto
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                # Texto con efecto de aparición
                alpha_color = (255, 255, 255, int(50 + (i * 20)))
                draw.text((x, y), text, fill=alpha_color[:3], font=font)
            except Exception as e:
                print(f"⚠️  Error con texto en GIF: {e}")
                # Continuar sin texto si hay error
            
            frames.append(img)
        
        # Guardar como GIF
        frames[0].save(
            os.path.join("fondos_instituto", "fondo_login.gif"),
            save_all=True,
            append_images=frames[1:],
            duration=150,  # ms entre frames
            loop=0,  # loop infinito
            optimize=True
        )
    
    @staticmethod
    def _crear_gif_menu():
        """Crea un GIF animado para el menú principal"""
        from PIL import ImageDraw
        
        frames = []
        width, height = 900, 600
        
        for i in range(15):
            img = Image.new('RGB', (width, height), color=(30, 64, 138))
            draw = ImageDraw.Draw(img)
            
            # Efecto de partículas flotantes
            for j in range(20):
                x = (j * 50 + i * 10) % width
                y = (j * 30 + i * 5) % height
                size = 5 + (i % 3)
                color = (255, 255, 255)  # Blanco
                draw.ellipse([x, y, x+size, y+size], fill=color)
            
            # Patrón de líneas animado
            for j in range(0, width, 30):
                x1 = (j + i * 2) % width
                draw.line([(x1, 0), (x1, height)], fill=(255, 255, 255, 100), width=1)
            
            frames.append(img)
        
        # Guardar como GIF
        frames[0].save(
            os.path.join("fondos_instituto", "fondo_menu.gif"),
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
            optimize=True
        )

# ==================== INSTRUCCIONES MEJORADAS PARA GIFs ====================

def mostrar_instrucciones_gifs():
    """Muestra instrucciones completas para GIFs"""
    instrucciones = """
    🎨 SISTEMA DE GIFs ANIMADOS - INSTITUTO RUBÉN DARÍO
    
    📁 CARPETA DE GIFs: 'fondos_instituto'
    
    Para usar GIFs animados en el sistema:
    
    1. 📸 AGREGAR TUS PROPIOS GIFs:
       - Coloca archivos GIF en la carpeta 'fondos_instituto'
       - Nombres recomendados:
         • fondo_login.gif
         • fondo_menu.gif  
         • fondo_estudiantes.gif
         • fondo_docentes.gif
         • fondo_asistencia.gif
       
    2. ⚙️ CONFIGURACIÓN AUTOMÁTICA:
       - El sistema crea GIFs de ejemplo al iniciar
       - Los GIFs se animan automáticamente
       - Velocidad ajustable (actual: 100ms por frame)
       - Loop infinito
       
    3. 🎭 EFECTOS DISPONIBLES:
       - Gradientes animados
       - Partículas flotantes  
       - Texto institucional
       - Patrones en movimiento
       
    4. 📏 TAMAÑOS RECOMENDADOS:
       - Login: 800x600 px
       - Menú principal: 900x600 px
       - Gestiones: 1000x700 px
       
    5. 💡 CONSEJOS:
       - Usa GIFs optimizados para mejor rendimiento
       - Mantén pocos frames si la animación es constante
       - Prueba diferentes velocidades de animación
       
    ¡Dale vida a tu sistema con animaciones profesionales!
    """
    print(instrucciones)

        
        # ==================== INICIALIZACIÓN MEJORADA CON GIFs ====================

if __name__ == "__main__":
    try:
        logger.info("🚀 Iniciando Sistema de Gestión Académica con GIFs")
        
        # Crear base de datos y esquema
        crear_db_y_schema()
        
        # Inicializar configuración
        config_manager = ConfigManager()
        
        # Crear GIFs de ejemplo si no existen
        if PIL_AVAILABLE:
            CreadorGifsEjemplo.crear_gifs_ejemplo()
            mostrar_instrucciones_gifs()
        else:
            print("⚠️  PIL no disponible - Los GIFs no funcionarán")
        
        # Mostrar información del sistema
        logger.info(f"📋 Sistema: {config_manager.get('instituto.nombre')}")
        logger.info(f"🎯 Versión: {config_manager.get('database.version_sistema', '2.0.0')}")
        logger.info(f"🖼️  Soporte GIFs: {'✅ Activado' if PIL_AVAILABLE else '❌ Desactivado'}")
        
        # Iniciar aplicación
        root = Tk()
        app = Login(root)
        
        # Configurar cierre seguro
        def on_closing():
            try:
                if hasattr(app, 'fondo_manager'):
                    app.fondo_manager.limpiar()
                root.destroy()
            except Exception as e:
                logger.error(f"Error en cierre: {e}")
            finally:
                logger.info("👋 Sistema cerrado")
                import sys
                sys.exit(0)
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"❌ Error fatal iniciando sistema: {e}")
        messagebox.showerror("Error Crítico", 
                           f"No se pudo iniciar el sistema:\n{str(e)}\n\n"
                           "Contacte al administrador del sistema.")
           