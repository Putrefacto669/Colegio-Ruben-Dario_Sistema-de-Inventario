"""
Gestor de configuración del sistema - MEJORADO
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manejador de configuración del sistema - CORREGIDO"""
    
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
                "animaciones": True,
                "usar_fondos": True  # NUEVO: control para fondos
            },
            "system": {
                "version": "2.0.0",
                "debug": False
            }
        }
        self.load_config()
    
    def load_config(self):
        """Carga la configuración desde archivo - MEJORADO"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge con configuración por defecto
                self.config = self._merge_configs(self.default_config, loaded_config)
                logger.info("✅ Configuración cargada exitosamente")
            else:
                self.config = self.default_config
                self.save_config()
                logger.info("📁 Configuración por defecto creada")
                
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            self.config = self.default_config
    
    def _merge_configs(self, default, loaded):
        """Fusión segura de configuraciones"""
        result = default.copy()
        
        for key, value in loaded.items():
            if isinstance(value, dict) and key in result:
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def save_config(self):
        """Guarda la configuración en archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("✅ Configuración guardada exitosamente")
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")
    
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
