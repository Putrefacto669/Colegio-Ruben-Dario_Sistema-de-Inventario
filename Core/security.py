"""
Sistema de autenticación y seguridad
"""

import sqlite3
import hashlib
import secrets
from typing import Optional, Tuple

from config.database import DB

def hash_password(password: str, salt: str) -> str:
    """Hashea una contraseña con salt"""
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def create_user(usuario: str, password: str, rol: str = 'Usuario') -> Tuple[bool, str]:
    """Crea un nuevo usuario en el sistema"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    salt = secrets.token_hex(8)
    h = hash_password(password, salt)
    try:
        c.execute(
            "INSERT INTO usuarios (usuario, pass_hash, salt, rol) VALUES (?, ?, ?, ?)",
            (usuario, h, salt, rol)
        )
        conn.commit()
        conn.close()
        return True, "Usuario creado exitosamente"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "El usuario ya existe"
    except Exception as e:
        conn.close()
        return False, f"Error creando usuario: {str(e)}"

def verificar_usuario(usuario: str, clave: str) -> Optional[Tuple[str, str]]:
    """Verifica las credenciales de un usuario"""
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
    
    hashed_input = hash_password(clave, salt)
    if hashed_input == pass_hash:
        return (usuario, rol)
    else:
        return None

def cambiar_password(usuario: str, nueva_clave: str) -> bool:
    """Cambia la contraseña de un usuario"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    salt = secrets.token_hex(8)
    nuevo_hash = hash_password(nueva_clave, salt)
    
    try:
        c.execute(
            "UPDATE usuarios SET pass_hash=?, salt=? WHERE usuario=?",
            (nuevo_hash, salt, usuario)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def usuario_existe(usuario: str) -> bool:
    """Verifica si un usuario existe"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id_usuario FROM usuarios WHERE usuario=?", (usuario,))
    existe = c.fetchone() is not None
    conn.close()
    return existe
