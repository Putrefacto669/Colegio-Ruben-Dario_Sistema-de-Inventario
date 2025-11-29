"""
Módulo de Login del Sistema
"""

import tkinter as tk
from tkinter import Tk, Frame, Label, Entry, Button, Canvas, StringVar
import sqlite3
import random
import sys
from tkinter import messagebox

from core.security import verificar_usuario
from ui.theme_manager import FondoManager
from ui.window_manager import GestorVentanas

class Login:
    def __init__(self, root):
        self.root = root
        self.root.title("Inicio de Sesión - Instituto Rubén Darío")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e3a8a")
        self.root.minsize(900, 600)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"1000x700+{x}+{y}")
        
        # Inicializar FondoManager
        try:
            self.fondo_manager = FondoManager(root, "login")
            self.fondo_manager.aplicar_fondo()
        except Exception as e:
            print(f"Error al cargar fondo: {e}")

        # ⌨️ Activar login con ENTER
        self.root.bind('<Return>', lambda event: self.login())

        # ==================== DISEÑO PRINCIPAL ====================
        
        # Panel principal
        self.panel_principal = Frame(root, bg='white', bd=0, relief='flat')
        self.panel_principal.place(relx=0.5, rely=0.5, anchor='center', width=500, height=620)

        # ==================== ENCABEZADO INSTITUCIONAL ====================
        
        # Logo/Icono institucional
        self.frame_logo = Frame(self.panel_principal, bg='white', height=120)
        self.frame_logo.pack(fill='x', pady=(40, 20))
        
        Label(self.frame_logo, text="🏫", font=("Arial", 40),
              bg='white', fg="#1e3a8a").pack(pady=(0, 10))
        
        Label(self.frame_logo, text="INSTITUTO RUBÉN DARÍO", 
              font=("Arial", 18, "bold"), bg='white', fg="#1e3a8a").pack()
        
        Label(self.frame_logo, text="Sistema de Gestión Académica", 
              font=("Arial", 12), bg='white', fg="#64748b").pack(pady=(5, 0))

        # Separador
        separator = Frame(self.panel_principal, height=2, bg="#e2e8f0")
        separator.pack(fill='x', padx=40, pady=25)

        # ==================== FORMULARIO DE LOGIN ====================
        
        self.frame_formulario = Frame(self.panel_principal, bg='white')
        self.frame_formulario.pack(fill='x', padx=50, pady=15)

        # Campo Usuario
        Label(self.frame_formulario, text="USUARIO:", 
              font=("Arial", 12, "bold"), bg='white', fg="#374151").pack(anchor='w', pady=(15, 8))
        
        self.usuario = Entry(self.frame_formulario, 
                           font=("Arial", 14),
                           bd=2, 
                           relief='solid',
                           highlightthickness=1,
                           highlightcolor="#2563eb",
                           highlightbackground="#d1d5db")
        self.usuario.pack(fill='x', pady=(0, 20), ipady=12)
        self.usuario.bind('<FocusIn>', lambda e: self.usuario.config(highlightbackground="#2563eb"))
        self.usuario.bind('<FocusOut>', lambda e: self.usuario.config(highlightbackground="#d1d5db"))

        # Campo Contraseña
        Label(self.frame_formulario, text="CONTRASEÑA:", 
              font=("Arial", 12, "bold"), bg='white', fg="#374151").pack(anchor='w', pady=(10, 8))
        
        self.frame_password = Frame(self.frame_formulario, bg='white')
        self.frame_password.pack(fill='x', pady=(0, 20))
        
        self.clave = Entry(self.frame_password, 
                         font=("Arial", 14),
                         show="•", 
                         bd=2, 
                         relief='solid',
                         highlightthickness=1,
                         highlightcolor="#2563eb",
                         highlightbackground="#d1d5db")
        self.clave.pack(side='left', fill='x', expand=True, ipady=12)
        self.clave.bind('<FocusIn>', lambda e: self.clave.config(highlightbackground="#2563eb"))
        self.clave.bind('<FocusOut>', lambda e: self.clave.config(highlightbackground="#d1d5db"))

        # Botón mostrar/ocultar contraseña
        self.show_pw = False
        self.btn_toggle = Button(self.frame_password, 
                               text="👁️", 
                               command=self.toggle_password,
                               font=("Arial", 12),
                               bg="#f8fafc",
                               fg="#64748b",
                               bd=2,
                               relief='solid',
                               width=4,
                               height=1)
        self.btn_toggle.pack(side='right', padx=(8, 0))

        # ==================== BOTÓN INGRESAR ====================
        
        self.btn_ingresar = Button(self.frame_formulario, 
                                 text="🎯 INGRESAR AL SISTEMA", 
                                 command=self.login,
                                 font=("Arial", 14, "bold"),
                                 bg="#2563eb",
                                 fg="white",
                                 bd=0,
                                 relief='flat',
                                 height=2,
                                 cursor="hand2")
        self.btn_ingresar.pack(fill='x', pady=(25, 20), ipady=8)
        
        # Efecto hover
        self.btn_ingresar.bind("<Enter>", lambda e: self.btn_ingresar.config(bg="#1d4ed8"))
        self.btn_ingresar.bind("<Leave>", lambda e: self.btn_ingresar.config(bg="#2563eb"))

        # ==================== BOTONES ADICIONALES ====================
        
        self.frame_botones = Frame(self.frame_formulario, bg='white')
        self.frame_botones.pack(fill='x', pady=(10, 5))

        # Botón Recuperar Contraseña
        self.btn_recuperar = Button(self.frame_botones, 
                                  text="🔐 Recuperar Contraseña", 
                                  command=self.recuperar_contrasena,
                                  font=("Arial", 10, "bold"),
                                  bg="#f59e0b",
                                  fg="white",
                                  bd=0,
                                  relief='flat',
                                  padx=15,
                                  pady=8,
                                  cursor="hand2")
        self.btn_recuperar.pack(side='left')
        
        self.btn_recuperar.bind("<Enter>", lambda e: self.btn_recuperar.config(bg="#e58e0b"))
        self.btn_recuperar.bind("<Leave>", lambda e: self.btn_recuperar.config(bg="#f59e0b"))
        
        # Botón Demo Confeti
        self.btn_confeti = Button(self.frame_botones, 
                                text="🎉 Demo", 
                                command=lambda: self.disparar_confeti(cantidad=50),
                                font=("Arial", 10, "bold"),
                                bg="#22c55e",
                                fg="white",
                                bd=0,
                                relief='flat',
                                padx=15,
                                pady=8,
                                cursor="hand2")
        self.btn_confeti.pack(side='right')
        
        self.btn_confeti.bind("<Enter>", lambda e: self.btn_confeti.config(bg="#1db34f"))
        self.btn_confeti.bind("<Leave>", lambda e: self.btn_confeti.config(bg="#22c55e"))

        # ==================== FOOTER ====================
        
        self.frame_footer = Frame(self.panel_principal, bg='white')
        self.frame_footer.pack(side='bottom', fill='x', pady=20)
        
        Label(self.frame_footer, 
              text="Sistema desarrollado para el Instituto Rubén Darío", 
              font=("Arial", 9), bg='white', fg="#94a3b8").pack()
        
        Label(self.frame_footer, 
              text="© 2024 - Todos los derechos reservados", 
              font=("Arial", 8), bg='white', fg="#cbd5e1").pack(pady=(5, 0))

        # ==================== INICIALIZACIÓN ====================
        
        # Poner foco en usuario al inicio
        self.usuario.focus_set()
        
        # Confeti de bienvenida
        self.root.after(800, lambda: self.disparar_confeti(cantidad=25))

    def toggle_password(self):
        self.show_pw = not self.show_pw
        self.clave.config(show="" if self.show_pw else "•")
        self.btn_toggle.config(text="🙈" if self.show_pw else "👁️")

    def login(self):
        usuario = self.usuario.get().strip()
        clave = self.clave.get().strip()
        
        if not usuario or not clave:
            messagebox.showwarning("Acceso al Sistema", 
                                "❌ Por favor ingrese usuario y contraseña")
            self.usuario.focus_set()
            return
        
        # Verificar credenciales
        ok = verificar_usuario(usuario, clave)
        if ok:
            usuario, rol = ok
            self.disparar_confeti(cantidad=80)
            messagebox.showinfo("Bienvenido", 
                              f"✅ ¡Bienvenido {usuario}!\n\n"
                              f"Rol: {rol}\n"
                              f"Acceso concedido al Sistema de Gestión")
            
            self.root.after(1500, lambda: self._transicion_a_menu_principal(usuario, rol))
        else:
            messagebox.showerror("Error de Acceso", 
                               "❌ Usuario o contraseña incorrectos\n\n"
                               "Por favor verifique sus credenciales")
            self.clave.delete(0, tk.END)
            self.usuario.focus_set()

    def _transicion_a_menu_principal(self, usuario: str, rol: str):
        try:
            if hasattr(self, 'fondo_manager'):
                self.fondo_manager.limpiar()
            if hasattr(self, 'canvas_confeti'):
                try: 
                    self.canvas_confeti.destroy()
                except: 
                    pass
            
            self.root.withdraw()
            
            # Importar aquí para evitar import circular
            from modules.main_menu import MainMenu
            
            root_menu = Tk()
            # Centrar nueva ventana
            x = (root_menu.winfo_screenwidth() // 2) - (1000 // 2)
            y = (root_menu.winfo_screenheight() // 2) - (600 // 2)
            root_menu.geometry(f"1000x600+{x}+{y}")
            
            app_menu = MainMenu(root_menu, usuario, rol)
            
            def on_closing_menu():
                try:
                    if hasattr(app_menu, 'fondo_manager'):
                        app_menu.fondo_manager.limpiar()
                    root_menu.destroy()
                except: 
                    pass
                finally:
                    sys.exit(0)
            
            root_menu.protocol("WM_DELETE_WINDOW", on_closing_menu)
            self.root.destroy()
            root_menu.mainloop()
            
        except Exception as e:
            print(f"Error en transición: {e}")
            sys.exit(1)

    def recuperar_contrasena(self):
        try:
            # Intentar importar el módulo de recuperación
            from recuperacion_pin import RecuperacionPIN
            RecuperacionPIN(self.root)
        except ImportError:
            messagebox.showinfo("Función no disponible", 
                              "El módulo de recuperación de contraseña no está disponible.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir recuperación: {e}")
    
    def disparar_confeti(self, cantidad=80):
        try:
            if not hasattr(self, 'canvas_confeti'):
                self.canvas_confeti = Canvas(self.root, highlightthickness=0)
                self.canvas_confeti.place(x=0, y=0, relwidth=1, relheight=1)
            self.canvas_confeti.lower(self.panel_principal)
            ancho = self.root.winfo_width() or 1000
            
            # Limpiar anterior
            for pid in getattr(self, "_confeti_particulas", []):
                try: 
                    self.canvas_confeti.delete(pid)
                except: 
                    pass
            self._confeti_particulas = []
            
            colores = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#f97316"]
            for _ in range(cantidad):
                x = random.randint(0, ancho)
                y = random.randint(-100, -20)
                sz = random.randint(10, 18)
                color = random.choice(colores)
                
                shape = random.choice(["circle", "rect", "triangle"])
                if shape == "circle":
                    pid = self.canvas_confeti.create_oval(x, y, x+sz, y+sz, fill=color, outline="")
                elif shape == "rect":
                    pid = self.canvas_confeti.create_rectangle(x, y, x+sz, y+sz, fill=color, outline="")
                else:
                    points = [x+sz/2, y, x+sz, y+sz, x, y+sz]
                    pid = self.canvas_confeti.create_polygon(points, fill=color, outline="")
                
                vx = random.uniform(-2.5, 2.5)
                vy = random.uniform(4, 8)
                self._confeti_particulas.append([pid, vx, vy])
            
            self._animar_confeti()
        except Exception as e:
            print(f"Error en confeti: {e}")

    def _animar_confeti(self):
        if not hasattr(self, '_confeti_particulas') or not self._confeti_particulas:
            return
        vivos = []
        alto = self.root.winfo_height() or 700
        for item in self._confeti_particulas:
            pid, vx, vy = item
            try:
                self.canvas_confeti.move(pid, vx, vy)
                coords = self.canvas_confeti.coords(pid)
                if coords and coords[1] < alto:
                    vivos.append([pid, vx, vy])
                else:
                    self.canvas_confeti.delete(pid)
            except: 
                pass
        self._confeti_particulas = vivos
        if vivos:
            self.root.after(25, self._animar_confeti)
        else:
            self.root.after(1000, self._limpiar_confeti)

    def _limpiar_confeti(self):
        if hasattr(self, 'canvas_confeti'):
            try:
                self.canvas_confeti.destroy()
                del self.canvas_confeti
            except: 
                pass
