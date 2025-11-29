"""
Configuración y creación de la base de datos
"""

import sqlite3
import secrets
import hashlib
import os

DB = "asistencia.db"

def hash_password(password: str, salt: str) -> str:
    """Hashea una contraseña con salt"""
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

    # Asistencia
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
