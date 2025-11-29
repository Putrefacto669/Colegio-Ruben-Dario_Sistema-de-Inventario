"""
Sistema de Exportación de Datos
"""

import os
from datetime import datetime

class ExportadorAvanzado:
    """Sistema de exportación mejorado"""
    
    @staticmethod
    def exportar_csv(datos, nombre_archivo, encabezados=None):
        """Exporta datos a CSV"""
        try:
            # Asegurar que el directorio de exportaciones existe
            os.makedirs("exportaciones", exist_ok=True)
            
            ruta_completa = os.path.join("exportaciones", f"{nombre_archivo}.csv")
            
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                if encabezados:
                    f.write(','.join(f'"{h}"' for h in encabezados) + '\n')
                for fila in datos:
                    linea = ','.join(f'"{str(x)}"' for x in fila)
                    f.write(linea + '\n')
            return True, f"Archivo exportado: {ruta_completa}"
        except Exception as e:
            return False, f"Error exportando CSV: {e}"
    
    @staticmethod
    def exportar_html(datos, nombre_archivo, titulo="Reporte", encabezados=None):
        """Exporta datos a HTML"""
        try:
            os.makedirs("exportaciones", exist_ok=True)
            ruta_completa = os.path.join("exportaciones", f"{nombre_archivo}.html")
            
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{titulo}</title>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                        th {{ background-color: #2563eb; color: white; }}
                        tr:nth-child(even) {{ background-color: #f9fafb; }}
                        tr:hover {{ background-color: #f1f5f9; }}
                        .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                        .info {{ margin: 10px 0; color: #64748b; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>{titulo}</h1>
                        <p>Instituto Rubén Darío - Sistema de Gestión Académica</p>
                        <p class="info">Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    </div>
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
                
                f.write(f"""
                    </table>
                    <div class="info">
                        <p>Total de registros: {len(datos)}</p>
                    </div>
                </body>
                </html>
                """)
            return True, f"Archivo exportado: {ruta_completa}"
        except Exception as e:
            return False, f"Error exportando HTML: {e}"

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
