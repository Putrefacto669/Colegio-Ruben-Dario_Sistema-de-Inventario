"""
Gestión de Docentes del Sistema
"""

import tkinter as tk
from tkinter import Toplevel, Frame, Label, Entry, Button, ttk, END
import sqlite3

from config.database import DB
from ui.theme_manager import FondoManager
from ui.message_manager import MessageManager
from utils.validators import (
    validar_cedula, validar_solo_texto, validar_telefono, validar_correo,
    mostrar_error_cedula, mostrar_error_texto, mostrar_error_telefono, mostrar_error_correo
)

class GestionDocentes:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Docentes")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f9fafb")
        self.root.minsize(1000, 650)

        # Aplicar fondo temático
        self.fondo_manager = FondoManager(root, "gestion_docentes")
        self.fondo_manager.aplicar_fondo()

        # Panel principal semi-transparente
        self.panel_principal = Frame(root, bg='white', bd=3, relief='raised')
        self.panel_principal.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
 
        # Prevenir múltiples instancias
        self.root.focus_set()
        self.root.grab_set()

        self._crear_interfaz()
        self.llenar_docentes()

    def _crear_interfaz(self):
        """Crea la interfaz de usuario"""
        # Encabezado
        header = Frame(self.root, bg="#f9fafb")
        header.pack(fill='x', pady=10)
        Label(header, text="📘 GESTIÓN DE DOCENTES", font=('Arial', 18, 'bold'), 
              bg="#f9fafb", fg="#2563eb").pack(side=tk.LEFT, padx=15)
        Button(header, text="Cerrar", bg="#64748b", fg="white", 
               command=self.root.destroy).pack(side=tk.RIGHT, padx=15)

        # Contenedor principal
        main_container = Frame(self.root, bg="#f9fafb")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Frame del formulario
        form_container = Frame(main_container, bg="#f9fafb")
        form_container.pack(fill=tk.X, pady=10)

        form = Frame(form_container, bg="#f9fafb", padx=20, pady=15)
        form.pack(fill=tk.X)

        # Crear campos del formulario
        self._crear_campos_formulario(form)
        
        # Botones de acción
        self._crear_botones_accion(form_container)
        
        # Tabla de docentes
        self._crear_tabla_docentes(main_container)
        
        # Leyenda
        self._crear_leyenda(main_container)

    def _crear_campos_formulario(self, form):
        """Crea los campos del formulario"""
        # Fila 1 - Cédula y Nombres
        Label(form, text="Cédula/ID:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=8, sticky=tk.E)
        self.txt_cedula = Entry(form, width=25, font=("Arial", 10))
        self.txt_cedula.grid(row=0, column=1, padx=10, pady=8, sticky=tk.W)
        Label(form, text="Ejemplo: 001-080888-8888A", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=0, column=2, sticky=tk.W, padx=10)
        
        Label(form, text="Nombres:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=0, column=3, padx=10, pady=8, sticky=tk.E)
        self.txt_nombres = Entry(form, width=30, font=("Arial", 10))
        self.txt_nombres.grid(row=0, column=4, padx=10, pady=8, sticky=tk.W)
        Label(form, text="Solo letras y espacios", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=0, column=5, sticky=tk.W, padx=10)

        # Fila 2 - Apellidos y Especialidad
        Label(form, text="Apellidos:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=8, sticky=tk.E)
        self.txt_apellido = Entry(form, width=25, font=("Arial", 10))
        self.txt_apellido.grid(row=1, column=1, padx=10, pady=8, sticky=tk.W)
        Label(form, text="Solo letras y espacios", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=1, column=2, sticky=tk.W, padx=10)
        
        Label(form, text="Especialidad:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=1, column=3, padx=10, pady=8, sticky=tk.E)
        self.txt_especialidad = Entry(form, width=30, font=("Arial", 10))
        self.txt_especialidad.grid(row=1, column=4, padx=10, pady=8, sticky=tk.W)
        Label(form, text="Ejemplo: Matemáticas, Informática", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=1, column=5, sticky=tk.W, padx=10)

        # Fila 3 - Correo y Teléfono
        Label(form, text="Correo Electrónico:", bg="#f9fafb", 
              font=("Arial", 10, "bold")).grid(row=2, column=0, padx=10, pady=8, sticky=tk.E)
        self.txt_email = Entry(form, width=25, font=("Arial", 10))
        self.txt_email.grid(row=2, column=1, padx=10, pady=8, sticky=tk.W)
        Label(form, text="Ejemplo: juan.perez@instituto.edu.ni", font=("Arial", 9), 
              fg="gray", bg="#f9fafb", wraplength=250).grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=10)
        
        Label(form, text="Teléfono:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=2, column=3, padx=10, pady=8, sticky=tk.E)
        self.txt_telefono = Entry(form, width=30, font=("Arial", 10))
        self.txt_telefono.grid(row=2, column=4, padx=10, pady=8, sticky=tk.W)
        Label(form, text="Ejemplo: 8888-8888 o 12345678", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=2, column=5, sticky=tk.W, padx=10)

        # Configurar eventos
        self._configurar_eventos()

    def _configurar_eventos(self):
        """Configura eventos de teclado y validaciones"""
        # Navegación con Enter
        self.txt_cedula.bind('<Return>', lambda event: self.txt_nombres.focus_set())
        self.txt_nombres.bind('<Return>', lambda event: self.txt_apellido.focus_set())
        self.txt_apellido.bind('<Return>', lambda event: self.txt_especialidad.focus_set())
        self.txt_especialidad.bind('<Return>', lambda event: self.txt_email.focus_set())
        self.txt_email.bind('<Return>', lambda event: self.txt_telefono.focus_set())
        self.txt_telefono.bind('<Return>', lambda event: self.agregar_docente())

        # Validaciones en tiempo real
        self.txt_cedula.bind("<FocusOut>", self.validar_cedula_tiempo_real)
        self.txt_nombres.bind("<FocusOut>", self.validar_nombres_tiempo_real)
        self.txt_apellido.bind("<FocusOut>", self.validar_apellido_tiempo_real)
        self.txt_email.bind("<FocusOut>", self.validar_correo_tiempo_real)
        self.txt_telefono.bind("<FocusOut>", self.validar_telefono_tiempo_real)

    def _crear_botones_accion(self, parent):
        """Crea los botones de acción"""
        separator = Frame(parent, height=2, bg="#e5e7eb")
        separator.pack(fill=tk.X, pady=15)

        acciones = Frame(parent, bg="#f9fafb", pady=10)
        acciones.pack()
        
        Button(acciones, text="➕ Agregar Docente", bg="#2563eb", fg="white", 
               font=("Arial", 11, "bold"), padx=15, pady=8, 
               command=self.agregar_docente).grid(row=0, column=0, padx=10)
        Button(acciones, text="🔄 Actualizar Lista", bg="#16a34a", fg="white", 
               font=("Arial", 11), padx=15, pady=8, 
               command=self.llenar_docentes).grid(row=0, column=1, padx=10)
        Button(acciones, text="❌ Desactivar", bg="#dc2626", fg="white", 
               font=("Arial", 11), padx=15, pady=8, 
               command=self.desactivar_docente).grid(row=0, column=2, padx=10)
        Button(acciones, text="🧹 Limpiar Campos", bg="#f59e0b", fg="white", 
               font=("Arial", 11), padx=15, pady=8, 
               command=self.limpiar_campos).grid(row=0, column=3, padx=10)

    def _crear_tabla_docentes(self, parent):
        """Crea la tabla de docentes"""
        tree_frame = Frame(parent, bg="#f9fafb")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
                self.tree.column(col, width=60, anchor=tk.CENTER)
            elif col in ["nombres", "apellido", "especialidad", "email"]:
                self.tree.column(col, width=180)
            else:
                self.tree.column(col, width=120)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

    def _crear_leyenda(self, parent):
        """Crea la leyenda de campos obligatorios"""
        leyenda = Frame(parent, bg="#f9fafb")
        leyenda.pack(fill=tk.X, pady=5)
        Label(leyenda, text="* Campos obligatorios", font=("Arial", 9, "italic"), 
              fg="red", bg="#f9fafb").pack(side=tk.LEFT)

    # ==================== MÉTODOS DE FUNCIONALIDAD ====================

    def agregar_docente(self):
        """Agrega un nuevo docente al sistema"""
        ced = self.txt_cedula.get().strip()
        nom = self.txt_nombres.get().strip()
        ape = self.txt_apellido.get().strip()
        esp = self.txt_especialidad.get().strip()
        email = self.txt_email.get().strip()
        tel = self.txt_telefono.get().strip()
        
        # Validaciones obligatorias
        if not (ced and nom and ape and esp):
            MessageManager.show_warning(self.root, "Atención", "Complete los campos obligatorios (*).")
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
            c.execute("""
                INSERT INTO docentes (cedula, nombres, apellido, especialidad, email, telefono) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ced, nom, ape, esp, email, tel))
            conn.commit()
            MessageManager.show_info(self.root, "Éxito", "Docente agregado correctamente.")
            self.llenar_docentes()
            self.limpiar_campos()
        except sqlite3.IntegrityError:
            MessageManager.show_error(self.root, "Error", "La cédula ya existe en el sistema.")
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"Error al agregar docente: {str(e)}")
        finally:
            conn.close()

    def llenar_docentes(self):
        """Llena la tabla con datos de docentes"""
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                SELECT id_docente, cedula, nombres, apellido, especialidad, email, telefono, estado 
                FROM docentes 
                ORDER BY id_docente DESC
            """)
            for row in c.fetchall():
                self.tree.insert("", "end", values=row)
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"Error al cargar docentes: {str(e)}")
        finally:
            conn.close()

    def desactivar_docente(self):
        """Desactiva un docente seleccionado"""
        sel = self.tree.selection()
        if not sel:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un docente.")
            return
        
        id_doc = self.tree.item(sel[0])["values"][0]
        nombre_docente = f"{self.tree.item(sel[0])['values'][2]} {self.tree.item(sel[0])['values'][3]}"
        
        respuesta = MessageManager.ask_yesno(
            self.root,
            "Confirmar Desactivación",
            f"¿Está seguro de desactivar al docente:\n{nombre_docente}?"
        )
        
        if not respuesta:
            return
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("UPDATE docentes SET estado='INACTIVO' WHERE id_docente=?", (id_doc,))
            conn.commit()
            MessageManager.show_info(self.root, "Éxito", "Docente desactivado correctamente.")
            self.llenar_docentes()
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"Error al desactivar docente: {str(e)}")
        finally:
            conn.close()

    def limpiar_campos(self):
        """Limpia todos los campos del formulario"""
        campos = [self.txt_cedula, self.txt_nombres, self.txt_apellido, 
                 self.txt_especialidad, self.txt_email, self.txt_telefono]
        for campo in campos:
            campo.delete(0, END)
            campo.config(bg="white")

    # ==================== VALIDACIONES EN TIEMPO REAL ====================

    def validar_cedula_tiempo_real(self, event=None):
        cedula = self.txt_cedula.get().strip()
        if cedula:
            if validar_cedula(cedula):
                self.txt_cedula.config(bg="#f0fff4")
            else:
                self.txt_cedula.config(bg="#fff0f0")
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
