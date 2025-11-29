"""
Control de Asistencia de Estudiantes
"""

import tkinter as tk
from tkinter import Toplevel, Frame, Label, Entry, Button, ttk, StringVar
import sqlite3
from datetime import datetime

from config.database import DB
from ui.theme_manager import FondoManager
from ui.message_manager import MessageManager

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
        self.panel_principal.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._crear_interfaz()
        self.crear_tabla()
        self.cargar_estudiantes()
        self.llenar_tabla()

    def _crear_interfaz(self):
        """Crea la interfaz de usuario"""
        # Encabezado
        Label(self.panel_principal, text="📋 Control de Asistencia - Estudiantes", 
              font=("Arial", 16, "bold"), bg="white", fg="#1e3a8a").pack(pady=10)
        
        # Formulario de control
        frm = Frame(self.panel_principal, bg="white")
        frm.pack(pady=6)

        # Estudiante
        Label(frm, text="Estudiante:", bg="white").grid(row=0, column=0, sticky=tk.E, padx=6, pady=6)
        self.cmb_estudiante = ttk.Combobox(frm, width=40, state="readonly")
        self.cmb_estudiante.grid(row=0, column=1, padx=6, pady=6)
        
        # Fecha
        Label(frm, text="Fecha:", bg="white").grid(row=0, column=2, sticky=tk.E, padx=6, pady=6)
        self.fecha_var = StringVar()
        self.fecha_var.set(datetime.now().strftime("%Y-%m-%d"))
        Entry(frm, textvariable=self.fecha_var, width=18, state='readonly').grid(row=0, column=3, padx=6, pady=6)

        # Estado
        Label(frm, text="Estado:", bg="white").grid(row=1, column=0, sticky=tk.E, padx=6, pady=6)
        self.cmb_estado = ttk.Combobox(frm, values=["Presente", "Tarde", "Ausente", "Justificado"], 
                                     width=20, state='readonly')
        self.cmb_estado.grid(row=1, column=1, padx=6, pady=6)
        self.cmb_estado.set("Presente")
        
        # Observaciones
        Label(frm, text="Observaciones:", bg="white").grid(row=1, column=2, sticky=tk.E, padx=6, pady=6)
        self.txt_obs = Entry(frm, width=30)
        self.txt_obs.grid(row=1, column=3, padx=6, pady=6)

        # Botones de acción
        btns = Frame(self.panel_principal, bg="white")
        btns.pack(pady=6)
        
        Button(btns, text="✅ Registrar Entrada", bg="#2563eb", fg="white", 
               command=self.registrar_entrada).grid(row=0, column=0, padx=6)
        Button(btns, text="🚪 Registrar Salida", bg="#16a34a", fg="white", 
               command=self.registrar_salida).grid(row=0, column=1, padx=6)
        Button(btns, text="🔄 Actualizar Lista", bg="#64748b", fg="white", 
               command=self.llenar_tabla).grid(row=0, column=2, padx=6)

        # Tabla de asistencias
        self._crear_tabla_asistencias()

    def _crear_tabla_asistencias(self):
        """Crea la tabla de asistencias"""
        cols = ("id_asistencia", "estudiante", "fecha", "hora_entrada", "hora_salida", "estado", "observaciones")
        self.tree = ttk.Treeview(self.panel_principal, columns=cols, show="headings")
        
        headers = {
            "id_asistencia": "ID", "estudiante": "Estudiante", "fecha": "Fecha",
            "hora_entrada": "Hora Entrada", "hora_salida": "Hora Salida", 
            "estado": "Estado", "observaciones": "Observaciones"
        }
        
        for col in cols:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=130)
        
        self.tree.column("id_asistencia", width=50)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

    def crear_tabla(self):
        """Crea la tabla de asistencia si no existe"""
        conn = sqlite3.connect(DB)
        c = conn.cursor()
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
        conn.commit()
        conn.close()

    def cargar_estudiantes(self):
        """Carga la lista de estudiantes en el combobox"""
        conn = sqlite3.connect(DB)
        c = conn.cursor()
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
        """Registra la entrada de un estudiante"""
        estudiante = self.cmb_estudiante.get()
        if not estudiante:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un estudiante.")
            return
        
        id_est = self.estudiantes_map.get(estudiante)
        fecha = self.fecha_var.get()
        hora = datetime.now().strftime("%H:%M:%S")
        estado = self.cmb_estado.get()
        obs = self.txt_obs.get().strip()
        
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        # Verificar si ya existe entrada hoy para ese estudiante
        c.execute("SELECT id_asistencia FROM asistencia WHERE id_estudiante=? AND fecha=?", (id_est, fecha))
        if c.fetchone():
            MessageManager.show_info(self.root, "Información", "Ya existe una entrada para este estudiante hoy.")
            conn.close()
            return
        
        try:
            c.execute("""
                INSERT INTO asistencia (id_estudiante, fecha, hora_entrada, estado, observaciones) 
                VALUES (?, ?, ?, ?, ?)
            """, (id_est, fecha, hora, estado, obs))
            conn.commit()
            MessageManager.show_info(self.root, "Éxito", "✅ Entrada registrada correctamente.")
            self.llenar_tabla()
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al registrar entrada: {str(e)}")
        finally:
            conn.close()

    def registrar_salida(self):
        """Registra la salida de un estudiante seleccionado"""
        sel = self.tree.selection()
        if not sel:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un registro en la tabla para marcar salida.")
            return
        
        id_asist = self.tree.item(sel[0])['values'][0]
        estudiante_nombre = self.tree.item(sel[0])['values'][1]
        hora_salida = datetime.now().strftime("%H:%M:%S")
        
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("UPDATE asistencia SET hora_salida=? WHERE id_asistencia=?", (hora_salida, id_asist))
            conn.commit()
            MessageManager.show_info(self.root, "Éxito", f"✅ Salida registrada para {estudiante_nombre}.")
            self.llenar_tabla()
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al registrar salida: {str(e)}")
        finally:
            conn.close()

    def llenar_tabla(self):
        """Llena la tabla con los registros de asistencia"""
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
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
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"Error al cargar asistencias: {str(e)}")
        finally:
            conn.close()
