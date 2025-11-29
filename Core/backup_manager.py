"""
Sistema de Backup y Restauración
"""

import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import Toplevel, Frame, Label, Button, Listbox, messagebox

from config.database import DB

class BackupManager:
    """Gestor de backups del sistema"""
    
    def __init__(self):
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def crear_backup(self):
        """Crea un backup de la base de datos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"asistencia_backup_{timestamp}.db")
        
        try:
            shutil.copy2(DB, backup_file)
            return True, f"Backup creado: {backup_file}"
        except Exception as e:
            return False, f"Error creando backup: {e}"
    
    def restaurar_backup(self, backup_file):
        """Restaura un backup"""
        try:
            shutil.copy2(backup_file, DB)
            return True, "Backup restaurado exitosamente"
        except Exception as e:
            return False, f"Error restaurando backup: {e}"
    
    def listar_backups(self):
        """Lista todos los backups disponibles"""
        if os.path.exists(self.backup_dir):
            archivos = sorted(os.listdir(self.backup_dir))
            return [archivo for archivo in archivos if archivo.endswith('.db')]
        return []

class GestionBackup:
    """Interfaz gráfica para gestión de backups"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Backup")
        self.root.geometry("500x400")
        self.root.configure(bg="#f9fafb")
        
        self.backup_manager = BackupManager()
        self._crear_interfaz()
        self.listar_backups()
    
    def _crear_interfaz(self):
        """Crea la interfaz de gestión de backups"""
        Label(self.root, text="💾 Gestión de Backup", 
              font=("Arial", 16, "bold"), bg="#f9fafb").pack(pady=10)
        
        # Botones principales
        btn_frame = Frame(self.root, bg="#f9fafb")
        btn_frame.pack(pady=10)
        
        Button(btn_frame, text="🔄 Crear Backup Ahora", 
               command=self.crear_backup, width=20, bg="#2563eb", fg="white").pack(pady=5)
        
        Button(btn_frame, text="📋 Listar Backups", 
               command=self.listar_backups, width=20, bg="#16a34a", fg="white").pack(pady=5)
        
        # Lista de backups
        Label(self.root, text="Backups Disponibles:", bg="#f9fafb").pack(pady=5)
        self.lista_backups = Listbox(self.root, width=60, height=8)
        self.lista_backups.pack(pady=10, padx=20)
        
        # Botones de acción
        action_frame = Frame(self.root, bg="#f9fafb")
        action_frame.pack(pady=10)
        
        Button(action_frame, text="📥 Restaurar Backup", 
               command=self.restaurar_backup, width=25, bg="#f59e0b", fg="white").pack(side=tk.LEFT, padx=5)
        
        Button(action_frame, text="🗑️ Eliminar Backup", 
               command=self.eliminar_backup, width=15, bg="#dc2626", fg="white").pack(side=tk.LEFT, padx=5)
    
    def crear_backup(self):
        """Crea un nuevo backup"""
        success, message = self.backup_manager.crear_backup()
        if success:
            messagebox.showinfo("Éxito", message)
            self.listar_backups()
        else:
            messagebox.showerror("Error", message)
    
    def listar_backups(self):
        """Lista los backups disponibles"""
        self.lista_backups.delete(0, tk.END)
        backups = self.backup_manager.listar_backups()
        for backup in backups:
            self.lista_backups.insert(tk.END, backup)
    
    def restaurar_backup(self):
        """Restaura un backup seleccionado"""
        seleccion = self.lista_backups.curselection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un backup de la lista")
            return
        
        backup_file = self.lista_backups.get(seleccion[0])
        backup_path = os.path.join(self.backup_manager.backup_dir, backup_file)
        
        if messagebox.askyesno("Confirmar", 
                             f"¿Restaurar backup {backup_file}?\n\nSe sobreescribirán los datos actuales."):
            success, message = self.backup_manager.restaurar_backup(backup_path)
            if success:
                messagebox.showinfo("Éxito", message)
            else:
                messagebox.showerror("Error", message)
    
    def eliminar_backup(self):
        """Elimina un backup seleccionado"""
        seleccion = self.lista_backups.curselection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un backup de la lista")
            return
        
        backup_file = self.lista_backups.get(seleccion[0])
        backup_path = os.path.join(self.backup_manager.backup_dir, backup_file)
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar backup {backup_file}?"):
            try:
                os.remove(backup_path)
                messagebox.showinfo("Éxito", "Backup eliminado correctamente")
                self.listar_backups()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")
