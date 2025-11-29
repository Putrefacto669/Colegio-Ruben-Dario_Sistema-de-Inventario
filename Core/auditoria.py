"""
Sistema de Auditoría para registrar acciones
"""

import logging
from datetime import datetime

class Auditoria:
    """Sistema de auditoría para registrar acciones del sistema"""
    
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
    
    def registrar_evento(self, usuario: str, accion: str, detalles: str = "", ip: str = "localhost"):
        """Registra un evento en la auditoría"""
        query = """
            INSERT INTO auditoria (usuario, accion, detalles, ip)
            VALUES (?, ?, ?, ?)
        """
        self.db_manager.execute_query(query, (usuario, accion, detalles, ip))
        logging.info(f"AUDITORIA - Usuario: {usuario}, Acción: {accion}, Detalles: {detalles}")
    
    def obtener_registros(self, limite: int = 100):
        """Obtiene los últimos registros de auditoría"""
        query = """
            SELECT usuario, accion, detalles, fecha, ip 
            FROM auditoria 
            ORDER BY fecha DESC 
            LIMIT ?
        """
        return self.db_manager.execute_query(query, (limite,), fetch=True) or []
    
    def buscar_por_usuario(self, usuario: str):
        """Busca registros de auditoría por usuario"""
        query = """
            SELECT usuario, accion, detalles, fecha, ip 
            FROM auditoria 
            WHERE usuario = ? 
            ORDER BY fecha DESC
        """
        return self.db_manager.execute_query(query, (usuario,), fetch=True) or []
    
    def buscar_por_fecha(self, fecha_inicio: str, fecha_fin: str):
        """Busca registros de auditoría por rango de fechas"""
        query = """
            SELECT usuario, accion, detalles, fecha, ip 
            FROM auditoria 
            WHERE date(fecha) BETWEEN ? AND ? 
            ORDER BY fecha DESC
        """
        return self.db_manager.execute_query(query, (fecha_inicio, fecha_fin), fetch=True) or []
    
    def limpiar_registros_antiguos(self, dias: int = 30):
        """Elimina registros de auditoría más antiguos que los días especificados"""
        query = "DELETE FROM auditoria WHERE date(fecha) < date('now', '-? days')"
        resultado = self.db_manager.execute_query(query, (dias,))
        logging.info(f"Auditoría: Eliminados {resultado} registros antiguos")
        return resultado
