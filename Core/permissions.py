"""
Sistema de permisos granular
"""

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
    def tiene_permiso(cls, rol: str, permiso: str) -> bool:
        """Verifica si un rol tiene un permiso específico"""
        return cls.PERMISOS.get(rol, {}).get(permiso, False)
    
    @classmethod
    def get_permisos_rol(cls, rol: str) -> dict:
        """Obtiene todos los permisos de un rol"""
        return cls.PERMISOS.get(rol, {}).copy()
    
    @classmethod
    def get_roles_disponibles(cls) -> list:
        """Obtiene la lista de roles disponibles"""
        return list(cls.PERMISOS.keys())
    
    @classmethod
    def puede_gestionar_estudiantes(cls, rol: str) -> bool:
        """Verifica si puede gestionar estudiantes"""
        return cls.tiene_permiso(rol, 'gestion_estudiantes')
    
    @classmethod
    def puede_gestionar_docentes(cls, rol: str) -> bool:
        """Verifica si puede gestionar docentes"""
        return cls.tiene_permiso(rol, 'gestion_docentes')
    
    @classmethod
    def puede_control_asistencia(cls, rol: str) -> bool:
        """Verifica si puede controlar asistencia"""
        return cls.tiene_permiso(rol, 'control_asistencia')
    
    @classmethod
    def puede_ver_reportes(cls, rol: str) -> bool:
        """Verifica si puede ver reportes"""
        return cls.tiene_permiso(rol, 'ver_reportes')
