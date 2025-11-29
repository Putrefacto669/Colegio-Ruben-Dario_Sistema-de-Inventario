"""
Validaciones de datos para formularios
"""

import re
from tkinter import messagebox

def validar_correo(correo: str) -> bool:
    """
    Valida que el correo electrónico tenga un formato correcto
    Ejemplo: usuario@dominio.com
    """
    if not correo:
        return True  # Permitir campo vacío (opcional)
    
    # Patrón para validar correo electrónico
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(patron, correo))

def validar_telefono(telefono: str) -> bool:
    """
    Valida que el teléfono tenga un formato correcto
    Ejemplo: 8888-8888 o 88888888
    """
    if not telefono:
        return True  # Permitir campo vacío
    
    # Patrón para validar teléfono (8 dígitos, con o sin guión)
    patron = r'^(\d{8}|\d{4}-\d{4})$'
    
    return bool(re.match(patron, telefono))

def validar_cedula(cedula: str) -> bool:
    """
    Valida que la cédula tenga un formato correcto
    Ejemplo: 001-080888-8888A o 0010808888888A
    """
    if not cedula:
        return False  # Cédula es obligatoria
    
    # Patrón para validar cédula nicaragüense (formato flexible)
    patron = r'^\d{3}[-]?\d{6}[-]?\d{4}[A-Za-z]?$'
    
    return bool(re.match(patron, cedula))

def validar_solo_texto(texto: str) -> bool:
    """
    Valida que el texto contenga solo letras y espacios
    """
    if not texto:
        return False
    
    patron = r'^[A-Za-záéíóúñÑ\s]+$'
    return bool(re.match(patron, texto))

def validar_numero(texto: str) -> bool:
    """
    Valida que el texto contenga solo números
    """
    if not texto:
        return True  # Permitir vacío
    
    return texto.isdigit()

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

def mostrar_error_texto(campo: str):
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
