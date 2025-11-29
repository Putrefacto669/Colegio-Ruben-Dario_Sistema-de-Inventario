"""
Gestión de Usuarios y Roles del Sistema
"""

import tkinter as tk
from tkinter import Toplevel, Frame, Label, Entry, Button, ttk, END
from core.security import create_user
from core.database_manager import DatabaseManager
from ui.message_manager import MessageManager

class GestionUsuarios:
    def __init__(self, root):
        self.root = root
        self.root.title("Usuarios y Roles")
        self.root.geometry("800x550")
        self.root.configure(bg="#f9fafb")
        
        self.db_manager = DatabaseManager()
        self._crear_interfaz()
        self.llenar_tabla()

    def _crear_interfaz(self):
        """Crea la interfaz de gestión de usuarios"""
        # Título
        Label(self.root, text="👥 Usuarios y Roles", 
              font=("Arial", 16, "bold"), bg="#f9fafb", fg="#2563eb").pack(pady=8)

        # Formulario
        frm = Frame(self.root, bg="#f9fafb")
        frm.pack(pady=6)
        
        # Campo Usuario
        Label(frm, text="Usuario:", bg="#f9fafb").grid(row=0, column=0, padx=6, pady=4, sticky=tk.E)
        self.txt_usuario = Entry(frm, width=24)
        self.txt_usuario.grid(row=0, column=1, padx=6, pady=4)
        
        # Campo Contraseña
        Label(frm, text="Contraseña:", bg="#f9fafb").grid(row=1, column=0, padx=6, pady=4, sticky=tk.E)
        self.txt_password = Entry(frm, width=24, show="*")
        self.txt_password.grid(row=1, column=1, padx=6, pady=4)
        
        # Campo Rol
        Label(frm, text="Rol:", bg="#f9fafb").grid(row=2, column=0, padx=6, pady=4, sticky=tk.E)
        self.cmb_rol = ttk.Combobox(frm, values=["Administrador", "Docente", "Estudiante"], 
                                  width=20, state="readonly")
        self.cmb_rol.grid(row=2, column=1, padx=6, pady=4)
        self.cmb_rol.current(2)  # Estudiante por defecto

        # Botones principales
        botones = Frame(self.root, bg="#f9fafb")
        botones.pack(pady=6)
        
        Button(botones, text="➕ Crear Usuario", bg="#2563eb", fg="white", 
               command=self.crear_usuario).grid(row=0, column=0, padx=6)
        Button(botones, text="🔄 Actualizar Lista", bg="#16a34a", fg="white", 
               command=self.llenar_tabla).grid(row=0, column=1, padx=6)
        Button(botones, text="🗑️ Eliminar Usuario", bg="#dc2626", fg="white", 
               command=self.eliminar_usuario).grid(row=0, column=2, padx=6)

        # Tabla de usuarios
        self._crear_tabla_usuarios()

        # Configurar eventos
        self.txt_usuario.bind('<Return>', lambda e: self.txt_password.focus_set())
        self.txt_password.bind('<Return>', lambda e: self.cmb_rol.focus_set())
        self.cmb_rol.bind('<Return>', lambda e: self.crear_usuario())

    def _crear_tabla_usuarios(self):
        """Crea la tabla de usuarios"""
        self.tree = ttk.Treeview(self.root, columns=("id", "usuario", "rol"), show="headings")
        
        for col in ("id", "usuario", "rol"):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=200)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

    def crear_usuario(self):
        """Crea un nuevo usuario"""
        usuario = self.txt_usuario.get().strip()
        password = self.txt_password.get().strip()
        rol = self.cmb_rol.get().strip()
        
        if not usuario or not password:
            MessageManager.show_warning(self.root, "Atención", "Complete usuario y contraseña.")
            return
        
        if len(password) < 4:
            MessageManager.show_warning(self.root, "Atención", "La contraseña debe tener al menos 4 caracteres.")
            return
        
        # Crear usuario
        ok, msg = create_user(usuario, password, rol)
        
        if ok:
            MessageManager.show_info(self.root, "Éxito", "✅ Usuario creado correctamente.")
            self.limpiar_campos()
            self.llenar_tabla()
        else:
            MessageManager.show_error(self.root, "Error", f"❌ {msg}")

    def eliminar_usuario(self):
        """Elimina un usuario seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            MessageManager.show_warning(self.root, "Atención", "Seleccione un usuario para eliminar.")
            return
        
        usuario_id = self.tree.item(seleccion[0])['values'][0]
        usuario_nombre = self.tree.item(seleccion[0])['values'][1]
        
        # No permitir eliminar al admin
        if usuario_nombre == 'admin':
            MessageManager.show_error(self.root, "Error", "❌ No se puede eliminar el usuario administrador.")
            return
        
        respuesta = MessageManager.ask_yesno(
            self.root,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar al usuario:\n{usuario_nombre}?\n\nEsta acción no se puede deshacer."
        )
        
        if not respuesta:
            return
        
        # Eliminar usuario
        query = "DELETE FROM usuarios WHERE id_usuario = ?"
        resultado = self.db_manager.execute_query(query, (usuario_id,))
        
        if resultado:
            MessageManager.show_info(self.root, "Éxito", "✅ Usuario eliminado correctamente.")
            self.llenar_tabla()
        else:
            MessageManager.show_error(self.root, "Error", "❌ Error al eliminar usuario.")

    def llenar_tabla(self):
        """Llena la tabla con los usuarios"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        usuarios = self.db_manager.get_usuarios()
        for usuario in usuarios:
            self.tree.insert("", "end", values=(
                usuario['id_usuario'],
                usuario['usuario'],
                usuario['rol']
            ))

    def limpiar_campos(self):
        """Limpia los campos del formulario"""
        self.txt_usuario.delete(0, END)
        self.txt_password.delete(0, END)
        self.cmb_rol.current(2)
