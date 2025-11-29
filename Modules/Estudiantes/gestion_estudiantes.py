"""
Gestión de Estudiantes del Sistema
"""

import tkinter as tk
from tkinter import Toplevel, Frame, Label, Entry, Button, ttk, END
import sqlite3

from config.database import DB
from ui.theme_manager import FondoManager
from ui.message_manager import MessageManager
from utils.validators import (
    validar_cedula, validar_solo_texto, validar_telefono,
    mostrar_error_cedula, mostrar_error_texto, mostrar_error_telefono
)

class GestionEstudiantes:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Estudiantes Técnicos")
        self.root.geometry("1150x750")
        self.root.configure(bg="#f9fafb")
        self.root.minsize(1000, 700)

        # Configurar para mantener el foco
        self.root.focus_force()
        self.root.grab_set()

        # Aplicar fondo temático
        self.fondo_manager = FondoManager(root, "gestion_estudiantes")
        self.fondo_manager.aplicar_fondo()

        # Panel principal semi-transparente
        self.panel_principal = Frame(root, bg='white', bd=3, relief='raised')
        self.panel_principal.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        self._crear_interfaz()
        self.cargar_carreras()
        self.llenar_tabla()
        
        # Poner foco en el primer campo
        self.txt_cedula.focus_set()

    def _crear_interfaz(self):
        """Crea la interfaz de usuario"""
        # Encabezado
        header = Frame(self.panel_principal, bg="white", pady=10)
        header.pack(fill='x')
        
        Label(header, text="🎓 Gestión de Estudiantes Técnicos - Instituto Rubén Darío",
              font=("Arial", 18, "bold"), bg="white", fg="#2563eb").pack()
        
        # Botón cerrar en header
        Button(header, text="✖ Cerrar", bg="#dc2626", fg="white", 
               command=self.root.destroy, font=("Arial", 10)).pack(side=tk.RIGHT, padx=20)

        # Contenedor principal
        main_container = Frame(self.root, bg="#f9fafb")
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        # Frame del formulario
        form_container = Frame(main_container, bg="#f9fafb")
        form_container.pack(fill=tk.X, pady=10)

        form = Frame(form_container, bg="#f9fafb", padx=20, pady=20)
        form.pack(fill=tk.X)

        # Crear campos del formulario
        self._crear_campos_formulario(form)
        
        # Botones de acción
        self._crear_botones_accion(form_container)
        
        # Tabla de estudiantes
        self._crear_tabla_estudiantes(main_container)
        
        # Leyenda
        self._crear_leyenda(main_container)

    def _crear_campos_formulario(self, form):
        """Crea los campos del formulario"""
        # Fila 1 - Cédula y Nombres
        Label(form, text="Cédula:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=0, column=0, padx=12, pady=10, sticky=tk.E)
        self.txt_cedula = Entry(form, width=22, font=("Arial", 10))
        self.txt_cedula.grid(row=0, column=1, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Ejemplo: 001-080888-8888A", font=("Arial", 9), 
              fg="gray", bg="#f9fafb", wraplength=200).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        Label(form, text="Nombres:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=0, column=3, padx=12, pady=10, sticky=tk.E)
        self.txt_nombres = Entry(form, width=25, font=("Arial", 10))
        self.txt_nombres.grid(row=0, column=4, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Solo letras y espacios", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=0, column=5, sticky=tk.W, padx=5)

        # Fila 2 - Apellidos y Carrera
        Label(form, text="Apellidos:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=1, column=0, padx=12, pady=10, sticky=tk.E)
        self.txt_apellidos = Entry(form, width=22, font=("Arial", 10))
        self.txt_apellidos.grid(row=1, column=1, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Solo letras y espacios", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=1, column=2, sticky=tk.W, padx=5)
        
        Label(form, text="Carrera Técnica:*", bg="#f9fafb", fg="red", 
              font=("Arial", 10, "bold")).grid(row=1, column=3, padx=12, pady=10, sticky=tk.E)
        self.cmb_carrera = ttk.Combobox(form, width=23, font=("Arial", 10), state="readonly")
        self.cmb_carrera.grid(row=1, column=4, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Seleccione una carrera", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=1, column=5, sticky=tk.W, padx=5)

        # Fila 3 - Año y Sección
        Label(form, text="Año:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=12, pady=10, sticky=tk.E)
        self.txt_anio = Entry(form, width=22, font=("Arial", 10))
        self.txt_anio.grid(row=2, column=1, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Ejemplo: 2024, 1er Año", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=2, column=2, sticky=tk.W, padx=5)
        
        Label(form, text="Sección:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=2, column=3, padx=12, pady=10, sticky=tk.E)
        self.txt_seccion = Entry(form, width=25, font=("Arial", 10))
        self.txt_seccion.grid(row=2, column=4, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Ejemplo: A, B, Matutina", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=2, column=5, sticky=tk.W, padx=5)

        # Fila 4 - Teléfono y Dirección
        Label(form, text="Teléfono:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=12, pady=10, sticky=tk.E)
        self.txt_telefono = Entry(form, width=22, font=("Arial", 10))
        self.txt_telefono.grid(row=3, column=1, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Ejemplo: 8888-8888", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=3, column=2, sticky=tk.W, padx=5)
        
        Label(form, text="Dirección:", bg="#f9fafb", font=("Arial", 10, "bold")).grid(row=3, column=3, padx=12, pady=10, sticky=tk.E)
        self.txt_direccion = Entry(form, width=45, font=("Arial", 10))
        self.txt_direccion.grid(row=3, column=4, columnspan=2, padx=12, pady=10, sticky=tk.W)
        
        Label(form, text="Ejemplo: Managua, Barrio X", font=("Arial", 9), 
              fg="gray", bg="#f9fafb").grid(row=3, column=6, sticky=tk.W, padx=5)

        # Configurar eventos
        self._configurar_eventos()

    def _configurar_eventos(self):
        """Configura eventos de teclado y validaciones"""
        # Navegación con Enter
        self.txt_cedula.bind('<Return>', lambda event: self.txt_nombres.focus_set())
        self.txt_nombres.bind('<Return>', lambda event: self.txt_apellidos.focus_set())
        self.txt_apellidos.bind('<Return>', lambda event: self.cmb_carrera.focus_set())
        self.txt_anio.bind('<Return>', lambda event: self.txt_seccion.focus_set())
        self.txt_seccion.bind('<Return>', lambda event: self.txt_telefono.focus_set())
        self.txt_telefono.bind('<Return>', lambda event: self.txt_direccion.focus_set())
        self.txt_direccion.bind('<Return>', lambda event: self.guardar_estudiante())

        # Validaciones en tiempo real
        self.txt_cedula.bind("<FocusOut>", self.validar_cedula_tiempo_real)
        self.txt_nombres.bind("<FocusOut>", self.validar_nombres_tiempo_real)
        self.txt_apellidos.bind("<FocusOut>", self.validar_apellidos_tiempo_real)
        self.txt_telefono.bind("<FocusOut>", self.validar_telefono_tiempo_real)

    def _crear_botones_accion(self, parent):
        """Crea los botones de acción"""
        separator = Frame(parent, height=2, bg="#e5e7eb")
        separator.pack(fill=tk.X, pady=20)

        acciones = Frame(parent, bg="#f9fafb", pady=15)
        acciones.pack()
        
        Button(acciones, text="💾 Guardar Estudiante", bg="#2563eb", fg="white", 
               font=("Arial", 11, "bold"), padx=20, pady=10, 
               command=self.guardar_estudiante).grid(row=0, column=0, padx=12)
        Button(acciones, text="✏️ Actualizar", bg="#16a34a", fg="white", 
               font=("Arial", 11), padx=20, pady=10, 
               command=self.actualizar_estudiante).grid(row=0, column=1, padx=12)
        Button(acciones, text="🗑️ Eliminar", bg="#dc2626", fg="white", 
               font=("Arial", 11), padx=20, pady=10, 
               command=self.eliminar_estudiante).grid(row=0, column=2, padx=12)
        Button(acciones, text="🧹 Limpiar", bg="#f59e0b", fg="white", 
               font=("Arial", 11), padx=20, pady=10, 
               command=self.limpiar_campos).grid(row=0, column=3, padx=12)

    def _crear_tabla_estudiantes(self, parent):
        """Crea la tabla de estudiantes"""
        tree_frame = Frame(parent, bg="#f9fafb")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        cols = ("id", "cedula", "nombres", "apellidos", "carrera", "anio", "seccion", "telefono", "direccion")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=16, yscrollcommand=scrollbar.set)
        
        headers = {
            "id": "ID", "cedula": "Cédula", "nombres": "Nombres", "apellidos": "Apellidos",
            "carrera": "Carrera", "anio": "Año", "seccion": "Sección", 
            "telefono": "Teléfono", "direccion": "Dirección"
        }
        
        # Configurar columnas más anchas
        column_widths = {
            "id": 60, "cedula": 140, "nombres": 150, "apellidos": 150,
            "carrera": 180, "anio": 80, "seccion": 100, 
            "telefono": 120, "direccion": 200
        }
        
        for col in cols:
            self.tree.heading(col, text=headers.get(col, col.capitalize()))
            self.tree.column(col, width=column_widths.get(col, 120))
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_estudiante)

    def _crear_leyenda(self, parent):
        """Crea la leyenda de campos obligatorios"""
        leyenda = Frame(parent, bg="#f9fafb")
        leyenda.pack(fill=tk.X, pady=8)
        Label(leyenda, text="* Campos obligatorios", font=("Arial", 9, "italic"), 
              fg="red", bg="#f9fafb").pack(side=tk.LEFT)

    def cargar_carreras(self):
        """Cargar carreras disponibles desde la base de datos"""
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("SELECT nombre FROM carreras ORDER BY nombre")
            carreras = [row[0] for row in c.fetchall()]
            self.cmb_carrera['values'] = carreras
            if carreras:
                self.cmb_carrera.current(0)
        except Exception as e:
            print(f"Error cargando carreras: {e}")
            # Si hay error, cargar algunas carreras por defecto
            carreras_default = [
                "Técnico en Informática",
                "Técnico en Electrónica", 
                "Técnico en Mecánica",
                "Técnico en Administración"
            ]
            self.cmb_carrera['values'] = carreras_default
            if carreras_default:
                self.cmb_carrera.current(0)
        finally:
            conn.close()

    def llenar_tabla(self):
        """Llenar la tabla con datos de estudiantes"""
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                SELECT id, cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion 
                FROM estudiantes 
                ORDER BY id DESC
            """)
            for row in c.fetchall():
                self.tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error llenando tabla: {e}")
            MessageManager.show_error(self.root, "Error", f"Error al cargar estudiantes: {e}")
        finally:
            conn.close()

    def guardar_estudiante(self):
        """Guardar nuevo estudiante"""
        # Obtener datos del formulario
        cedula = self.txt_cedula.get().strip()
        nombres = self.txt_nombres.get().strip()
        apellidos = self.txt_apellidos.get().strip()
        carrera = self.cmb_carrera.get().strip()
        anio = self.txt_anio.get().strip()
        seccion = self.txt_seccion.get().strip()
        telefono = self.txt_telefono.get().strip()
        direccion = self.txt_direccion.get().strip()
        
        # Validaciones básicas
        if not cedula:
            MessageManager.show_warning(self.root, "Atención", "La cédula es obligatoria")
            self.txt_cedula.focus_set()
            return
            
        if not nombres:
            MessageManager.show_warning(self.root, "Atención", "Los nombres son obligatorios")
            self.txt_nombres.focus_set()
            return
            
        if not apellidos:
            MessageManager.show_warning(self.root, "Atención", "Los apellidos son obligatorios")
            self.txt_apellidos.focus_set()
            return
            
        if not carrera:
            MessageManager.show_warning(self.root, "Atención", "La carrera es obligatoria")
            self.cmb_carrera.focus_set()
            return
        
        # Validación de cédula
        if not validar_cedula(cedula):
            MessageManager.show_error(self.root, "Error en formato de cédula", 
                                    "❌ El formato de la cédula no es válido.\n\n"
                                    "🆔 FORMATOS ACEPTADOS:\n"
                                    "   • 0010808888888A (13 dígitos + letra)\n"
                                    "   • 001-080888-8888A (con guiones)")
            self.txt_cedula.focus_set()
            return
        
        # Validación de nombres (solo texto)
        if not validar_solo_texto(nombres):
            mostrar_error_texto("nombres")
            self.txt_nombres.focus_set()
            return
        
        # Validación de apellidos (solo texto)
        if not validar_solo_texto(apellidos):
            mostrar_error_texto("apellidos")
            self.txt_apellidos.focus_set()
            return
        
        # Validación de teléfono
        if telefono and not validar_telefono(telefono):
            mostrar_error_telefono()
            self.txt_telefono.focus_set()
            return
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO estudiantes (cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion))
            conn.commit()
            
            MessageManager.show_info(self.root, "Éxito", "✅ Estudiante guardado correctamente")
            
            self.limpiar_campos()
            self.llenar_tabla()
            
        except sqlite3.IntegrityError:
            MessageManager.show_error(self.root, "Error", "❌ La cédula ya existe en el sistema")
            self.txt_cedula.focus_set()
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al guardar: {str(e)}")
        finally:
            conn.close()

    def seleccionar_estudiante(self, event):
        """Selecciona un estudiante de la tabla para editar"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        values = item['values']
        
        if not values:
            return
            
        # Limpiar campos primero
        self.limpiar_campos()
        
        # Llenar campos con datos del estudiante seleccionado
        self.txt_cedula.insert(0, str(values[1]) if len(values) > 1 and values[1] else "")
        self.txt_nombres.insert(0, str(values[2]) if len(values) > 2 and values[2] else "")
        self.txt_apellidos.insert(0, str(values[3]) if len(values) > 3 and values[3] else "")
        
        # Buscar y seleccionar la carrera en el combobox
        if len(values) > 4 and values[4]:
            carrera_valor = str(values[4])
            carreras = list(self.cmb_carrera['values'])
            if carrera_valor in carreras:
                self.cmb_carrera.set(carrera_valor)
            else:
                # Si la carrera no está en la lista, la agregamos temporalmente
                nuevas_carreras = list(carreras) + [carrera_valor]
                self.cmb_carrera['values'] = nuevas_carreras
                self.cmb_carrera.set(carrera_valor)
        
        self.txt_anio.insert(0, str(values[5]) if len(values) > 5 and values[5] else "")
        self.txt_seccion.insert(0, str(values[6]) if len(values) > 6 and values[6] else "")
        self.txt_telefono.insert(0, str(values[7]) if len(values) > 7 and values[7] else "")
        self.txt_direccion.insert(0, str(values[8]) if len(values) > 8 and values[8] else "")

    def actualizar_estudiante(self):
        """Actualizar estudiante seleccionado"""
        selection = self.tree.selection()
        if not selection:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un estudiante para actualizar")
            return
            
        item = self.tree.item(selection[0])
        values = item['values']
        
        if not values or len(values) == 0:
            MessageManager.show_warning(self.root, "Atención", "No hay datos del estudiante seleccionado")
            return
            
        estudiante_id = values[0]
        
        # Obtener datos actualizados del formulario
        cedula = self.txt_cedula.get().strip()
        nombres = self.txt_nombres.get().strip()
        apellidos = self.txt_apellidos.get().strip()
        carrera = self.cmb_carrera.get().strip()
        anio = self.txt_anio.get().strip()
        seccion = self.txt_seccion.get().strip()
        telefono = self.txt_telefono.get().strip()
        direccion = self.txt_direccion.get().strip()
        
        # Validaciones
        if not cedula or not nombres or not apellidos or not carrera:
            MessageManager.show_warning(self.root, "Atención", "Complete los campos obligatorios")
            return
        
        # Validación de cédula
        if not validar_cedula(cedula):
            mostrar_error_cedula()
            return
        
        # Validación de nombres (solo texto)
        if not validar_solo_texto(nombres):
            mostrar_error_texto("nombres")
            return
        
        # Validación de apellidos (solo texto)
        if not validar_solo_texto(apellidos):
            mostrar_error_texto("apellidos")
            return
        
        # Validación de teléfono
        if telefono and not validar_telefono(telefono):
            mostrar_error_telefono()
            return
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                UPDATE estudiantes 
                SET cedula=?, nombres=?, apellidos=?, carrera=?, anio=?, seccion=?, telefono=?, direccion=?
                WHERE id=?
            """, (cedula, nombres, apellidos, carrera, anio, seccion, telefono, direccion, estudiante_id))
            
            if c.rowcount > 0:
                conn.commit()
                MessageManager.show_info(self.root, "Éxito", "✅ Estudiante actualizado correctamente")
                self.limpiar_campos()
                self.llenar_tabla()
            else:
                MessageManager.show_error(self.root, "Error", "❌ No se pudo actualizar el estudiante")
                
        except sqlite3.IntegrityError:
            MessageManager.show_error(self.root, "Error", "❌ La cédula ya existe en el sistema")
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al actualizar: {str(e)}")
        finally:
            conn.close()

    def eliminar_estudiante(self):
        """Eliminar estudiante seleccionado"""
        selection = self.tree.selection()
        if not selection:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un estudiante para eliminar")
            return
            
        item = self.tree.item(selection[0])
        values = item['values']
        
        if not values or len(values) == 0:
            MessageManager.show_warning(self.root, "Atención", "No hay datos del estudiante seleccionado")
            return
            
        estudiante_id = values[0]
        nombre_completo = f"{values[2]} {values[3]}" if len(values) > 3 else "Estudiante"
        
        # Confirmar eliminación
        respuesta = MessageManager.ask_yesno(
            self.root,
            "Confirmar Eliminación", 
            f"¿Está seguro de eliminar al estudiante:\n{nombre_completo}?\n\nEsta acción no se puede deshacer."
        )
        
        if not respuesta:
            return
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("DELETE FROM estudiantes WHERE id=?", (estudiante_id,))
            conn.commit()
            MessageManager.show_info(self.root, "Éxito", "✅ Estudiante eliminado correctamente")
            self.limpiar_campos()
            self.llenar_tabla()
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"❌ Error al eliminar: {str(e)}")
        finally:
            conn.close()

    def limpiar_campos(self):
        """Limpiar todos los campos del formulario"""
        self.txt_cedula.delete(0, END)
        self.txt_nombres.delete(0, END)
        self.txt_apellidos.delete(0, END)
        self.cmb_carrera.set('')
        self.txt_anio.delete(0, END)
        self.txt_seccion.delete(0, END)
        self.txt_telefono.delete(0, END)
        self.txt_direccion.delete(0, END)
        
        # Restablecer colores de fondo
        self.txt_cedula.config(bg="white")
        self.txt_nombres.config(bg="white")
        self.txt_apellidos.config(bg="white")
        self.txt_telefono.config(bg="white")
        
        # Poner foco en el primer campo
        self.txt_cedula.focus_set()

    # Métodos de validación en tiempo real
    def validar_cedula_tiempo_real(self, event=None):
        cedula = self.txt_cedula.get().strip()
        if cedula:
            if validar_cedula(cedula):
                self.txt_cedula.config(bg="#f0fff4")  # Verde claro
            else:
                self.txt_cedula.config(bg="#fff0f0")  # Rojo claro
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

    def validar_apellidos_tiempo_real(self, event=None):
        apellidos = self.txt_apellidos.get().strip()
        if apellidos:
            if validar_solo_texto(apellidos):
                self.txt_apellidos.config(bg="#f0fff4")
            else:
                self.txt_apellidos.config(bg="#fff0f0")
        else:
            self.txt_apellidos.config(bg="white")

    def validar_telefono_tiempo_real(self, event=None):
        telefono = self.txt_telefono.get().strip()
        if telefono:
            if validar_telefono(telefono):
                self.txt_telefono.config(bg="#f0fff4")
            else:
                self.txt_telefono.config(bg="#fff0f0")
        else:
            self.txt_telefono.config(bg="white")
  
