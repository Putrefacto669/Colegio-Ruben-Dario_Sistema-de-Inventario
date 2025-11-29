"""
Manejador mejorado para operaciones de base de datos
"""

import sqlite3
import logging
from typing import List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manejador mejorado para operaciones de base de datos"""
    
    def __init__(self, db_path="asistencia.db"):
        self.db_path = db_path
        self.cache = {}
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query: str, params: Tuple = (), fetch: bool = False) -> Optional[Any]:
        """Ejecuta una consulta con manejo de errores"""
        try:
            conn = self.get_connection()
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
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return None

    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """Ejecuta múltiples inserciones/actualizaciones"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error en ejecución múltiple: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False

    def get_estudiantes(self, force_refresh: bool = False) -> List[sqlite3.Row]:
        """Obtiene estudiantes con cache"""
        cache_key = "estudiantes"
        if not force_refresh and cache_key in self.cache:
            return self.cache[cache_key]
        
        query = "SELECT * FROM estudiantes ORDER BY id DESC"
        result = self.execute_query(query, fetch=True)
        if result:
            self.cache[cache_key] = result
        return result or []

    def get_docentes(self, force_refresh: bool = False) -> List[sqlite3.Row]:
        """Obtiene docentes con cache"""
        cache_key = "docentes"
        if not force_refresh and cache_key in self.cache:
            return self.cache[cache_key]
        
        query = "SELECT * FROM docentes ORDER BY id_docente DESC"
        result = self.execute_query(query, fetch=True)
        if result:
            self.cache[cache_key] = result
        return result or []

    def get_usuarios(self) -> List[sqlite3.Row]:
        """Obtiene todos los usuarios"""
        query = "SELECT id_usuario, usuario, rol FROM usuarios ORDER BY id_usuario DESC"
        return self.execute_query(query, fetch=True) or []

    def clear_cache(self, key: str = None):
        """Limpia la cache"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()
        logger.debug("Cache limpiada")

    def get_estadisticas(self) -> dict:
        """Obtiene estadísticas del sistema"""
        stats = {}
        
        # Total estudiantes
        result = self.execute_query("SELECT COUNT(*) FROM estudiantes", fetch=True)
        stats['total_estudiantes'] = result[0][0] if result else 0
        
        # Total docentes activos
        result = self.execute_query("SELECT COUNT(*) FROM docentes WHERE estado = 'ACTIVO'", fetch=True)
        stats['total_docentes'] = result[0][0] if result else 0
        
        # Asistencias hoy
        from datetime import datetime
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        result = self.execute_query(
            "SELECT COUNT(*) FROM asistencia WHERE fecha = ?", 
            (fecha_hoy,), 
            fetch=True
        )
        stats['asistencias_hoy'] = result[0][0] if result else 0
        
        return stats
