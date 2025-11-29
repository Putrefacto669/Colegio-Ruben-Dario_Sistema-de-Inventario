"""
Sistema de Gestión de Temas y Fondos
"""

import os
import random
from PIL import Image, ImageTk, ImageSequence, ImageDraw
import tkinter as tk

# Verificar disponibilidad de PIL
try:
    from PIL import Image, ImageTk, ImageSequence, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class SistemaFondos:
    """Sistema de gestión de fondos del sistema"""
    
    @staticmethod
    def inicializar_fondos():
        """Inicializa el sistema de fondos"""
        directorio_fondos = "fondos_instituto"
        if not os.path.exists(directorio_fondos):
            os.makedirs(directorio_fondos)
            print("✅ Carpeta de fondos creada: 'fondos_instituto'")
            
            # Crear archivo de instrucciones
            with open(os.path.join(directorio_fondos, "INSTRUCCIONES.txt"), "w", encoding="utf-8") as f:
                f.write("""INSTRUCCIONES PARA FONDOS PERSONALIZADOS - INSTITUTO RUBÉN DARÍO

1. AGREGA TUS IMÁGENES: Coloca archivos JPG, PNG o GIF en esta carpeta
2. NOMBRES SUGERIDOS:
   - fondo_login.jpg
   - fondo_menu_principal.jpg  
   - fondo_estudiantes.jpg
   - fondo_docentes.jpg
3. TAMAÑO RECOMENDADO: 800x600 o mayor
4. Los GIFs se animarán automáticamente

¡Personaliza tu sistema con imágenes de tu instituto!
                """)
        
        return directorio_fondos

    @staticmethod
    def obtener_fondo(tipo_ventana):
        """Obtiene la ruta del fondo para un tipo de ventana"""
        directorio = "fondos_instituto"
        
        # Mapeo de nombres de archivo por tipo de ventana
        mapeo_fondos = {
            "login": ["fondo_login.jpg", "fondo_principal.jpg", "fondo_rdario.jpg"],
            "menu_principal": ["fondo_menu_principal.jpg", "fondo_aula.jpg", "fondo_instituto.jpg"],
            "gestion_estudiantes": ["fondo_estudiantes.jpg", "fondo_libros.jpg", "fondo_educacion.jpg"],
            "gestion_docentes": ["fondo_docentes.jpg", "fondo_graduacion.jpg", "fondo_biblioteca.jpg"],
            "gestion_asistencia": ["fondo_asistencia.jpg", "fondo_reloj.jpg"],
            "dashboard": ["fondo_dashboard.jpg", "fondo_estadisticas.jpg"]
        }
        
        # Buscar archivos para este tipo de ventana
        if tipo_ventana in mapeo_fondos:
            for nombre_archivo in mapeo_fondos[tipo_ventana]:
                ruta = os.path.join(directorio, nombre_archivo)
                if os.path.exists(ruta):
                    return ruta
        
        # Si no se encuentra ningún archivo específico, buscar cualquier imagen
        if os.path.exists(directorio):
            for archivo in os.listdir(directorio):
                if archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    return os.path.join(directorio, archivo)
        
        return None

class FondoManager:
    """Gestor de fondos para ventanas"""
    
    def __init__(self, ventana, tipo_ventana, tema="default"):
        self.ventana = ventana
        self.tipo_ventana = tipo_ventana
        self.tema = tema
        self.canvas = None
        self.imagen_fondo = None
        self.gif_frames = []
        self.gif_index = 0
        self.animacion_activa = False
        
    def aplicar_fondo(self):
        """Aplica el fondo a la ventana"""
        if not PIL_AVAILABLE:
            self._aplicar_fondo_color()
            return
            
        ruta_fondo = self._obtener_ruta_fondo()
        
        if not ruta_fondo:
            self._aplicar_fondo_color()
            return
        
        try:
            if ruta_fondo.lower().endswith('.gif'):
                self._aplicar_fondo_gif(ruta_fondo)
            else:
                self._aplicar_fondo_imagen(ruta_fondo)
                
            # Asegurar que el fondo esté detrás de todo
            self._configurar_capas()
            
        except Exception as e:
            print(f"❌ Error cargando fondo {ruta_fondo}: {e}")
            self._aplicar_fondo_color()
    
    def _obtener_ruta_fondo(self):
        """Obtiene la ruta del fondo para el tipo de ventana"""
        return SistemaFondos.obtener_fondo(self.tipo_ventana)
    
    def _aplicar_fondo_color(self):
        """Aplica fondo de color sólido"""
        colores = {
            "login": "#1e3a8a",
            "menu_principal": "#2563eb", 
            "gestion_estudiantes": "#1e40af",
            "gestion_docentes": "#3730a3",
            "gestion_asistencia": "#1e3a8a",
            "dashboard": "#1e40af"
        }
        color = colores.get(self.tipo_ventana, "#1e40af")
        self.ventana.configure(bg=color)
    
    def _aplicar_fondo_gif(self, ruta_gif):
        """Aplica GIF animado como fondo"""
        try:
            # Crear canvas para el fondo
            self.canvas = tk.Canvas(self.ventana, highlightthickness=0, bg='white')
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Cargar frames del GIF
            gif = Image.open(ruta_gif)
            self.gif_frames = []
            
            for frame in ImageSequence.Iterator(gif):
                # Convertir a RGB si es necesario
                if frame.mode != 'RGB':
                    frame = frame.convert('RGB')
                self.gif_frames.append(frame)
            
            self.gif_index = 0
            self.animacion_activa = True
            
            # Iniciar animación
            self._animar_gif()
            
            print(f"✅ GIF cargado: {ruta_gif} - {len(self.gif_frames)} frames")
            
        except Exception as e:
            print(f"❌ Error cargando GIF: {e}")
            self._aplicar_fondo_color()
    
    def _animar_gif(self):
        """Anima el GIF"""
        if not self.animacion_activa or not self.gif_frames:
            return
            
        try:
            # Obtener frame actual
            frame_actual = self.gif_frames[self.gif_index]
            
            # Redimensionar al tamaño de la ventana
            ancho = self.ventana.winfo_width()
            alto = self.ventana.winfo_height()
            
            if ancho > 1 and alto > 1:
                frame_redim = frame_actual.resize((ancho, alto), Image.LANCZOS)
                self.imagen_fondo = ImageTk.PhotoImage(frame_redim)
                
                # Limpiar y dibujar
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, image=self.imagen_fondo, anchor="nw")
            
            # Siguiente frame
            self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
            
            # Programar próximo frame
            delay = 100  # ms entre frames
            self.ventana.after(delay, self._animar_gif)
            
        except Exception as e:
            print(f"Error en animación GIF: {e}")
            self.animacion_activa = False
    
    def _aplicar_fondo_imagen(self, ruta_imagen):
        """Aplica imagen de fondo estática"""
        try:
            self.canvas = tk.Canvas(self.ventana, highlightthickness=0)
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            
            imagen = Image.open(ruta_imagen)
            self._actualizar_fondo_imagen(imagen)
            
            # Redimensionar cuando cambie el tamaño
            self.ventana.bind('<Configure>', lambda e: self._actualizar_fondo_imagen(imagen))
            
        except Exception as e:
            print(f"Error aplicando fondo imagen: {e}")
            self._aplicar_fondo_color()
    
    def _actualizar_fondo_imagen(self, imagen):
        """Actualiza imagen de fondo estática"""
        if not self.canvas:
            return
            
        try:
            ancho = self.ventana.winfo_width()
            alto = self.ventana.winfo_height()
            
            if ancho > 1 and alto > 1:
                # Redimensionar manteniendo aspecto
                ratio_orig = imagen.width / imagen.height
                ratio_nuevo = ancho / alto
                
                if ratio_orig > ratio_nuevo:
                    nuevo_ancho = ancho
                    nuevo_alto = int(ancho / ratio_orig)
                else:
                    nuevo_alto = alto
                    nuevo_ancho = int(alto * ratio_orig)
                
                imagen_redim = imagen.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
                self.imagen_fondo = ImageTk.PhotoImage(imagen_redim)
                
                self.canvas.delete("all")
                self.canvas.create_image(ancho//2, alto//2, image=self.imagen_fondo, anchor="center")
                
        except Exception as e:
            print(f"Error actualizando fondo: {e}")
    
    def _configurar_capas(self):
        """Asegura que el fondo esté en la capa inferior"""
        if self.canvas:
            self.canvas.lower()  # Mover a la capa más baja
    
    def limpiar(self):
        """Limpia recursos de animación"""
        self.animacion_activa = False
        if self.canvas:
            try:
                self.canvas.destroy()
            except:
                pass

class CreadorGifsEjemplo:
    """Creador de GIFs animados de ejemplo"""
    
    @staticmethod
    def crear_gifs_ejemplo():
        """Crea GIFs animados de ejemplo para el sistema"""
        directorio = "fondos_instituto"
        os.makedirs(directorio, exist_ok=True)
        
        gifs_creados = []
        
        # GIF para login - Animación suave de colores
        if not os.path.exists(os.path.join(directorio, "fondo_login.gif")):
            try:
                CreadorGifsEjemplo._crear_gif_login()
                gifs_creados.append("fondo_login.gif")
            except Exception as e:
                print(f"❌ No se pudo crear GIF de login: {e}")
        
        # GIF para menú principal - Efecto de partículas
        if not os.path.exists(os.path.join(directorio, "fondo_menu.gif")):
            try:
                CreadorGifsEjemplo._crear_gif_menu()
                gifs_creados.append("fondo_menu.gif")
            except Exception as e:
                print(f"❌ No se pudo crear GIF de menú: {e}")
        
        if gifs_creados:
            print(f"✅ GIFs creados: {', '.join(gifs_creados)}")
        else:
            print("📁 GIFs de ejemplo ya existen")
    
    @staticmethod
    def _crear_gif_login():
        """Crea un GIF animado para el login"""
        frames = []
        width, height = 800, 600
        
        # Crear frames con gradiente animado
        for i in range(10):
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Gradiente azul animado
            for y in range(height):
                # Color que cambia con el frame
                r = int(30 + (i * 2))
                g = int(64 + (i * 3))
                b = int(138 + (i * 4))
                color = (r, g, b)
                draw.line([(0, y), (width, y)], fill=color)
            
            # Añadir texto institucional semi-transparente
            try:
                # Intentar cargar fuente
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except:
                    try:
                        font = ImageFont.truetype("Arial", 36)
                    except:
                        font = ImageFont.load_default()
                
                text = "Instituto Rubén Darío"
                # Calcular posición del texto
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                # Texto con efecto de aparición
                alpha_color = (255, 255, 255, int(50 + (i * 20)))
                draw.text((x, y), text, fill=alpha_color[:3], font=font)
            except Exception as e:
                print(f"⚠️  Error con texto en GIF: {e}")
                # Continuar sin texto si hay error
            
            frames.append(img)
        
        # Guardar como GIF
        frames[0].save(
            os.path.join("fondos_instituto", "fondo_login.gif"),
            save_all=True,
            append_images=frames[1:],
            duration=150,  # ms entre frames
            loop=0,  # loop infinito
            optimize=True
        )
    
    @staticmethod
    def _crear_gif_menu():
        """Crea un GIF animado para el menú principal"""
        frames = []
        width, height = 900, 600
        
        for i in range(15):
            img = Image.new('RGB', (width, height), color=(30, 64, 138))
            draw = ImageDraw.Draw(img)
            
            # Efecto de partículas flotantes
            for j in range(20):
                x = (j * 50 + i * 10) % width
                y = (j * 30 + i * 5) % height
                size = 5 + (i % 3)
                color = (255, 255, 255)  # Blanco
                draw.ellipse([x, y, x+size, y+size], fill=color)
            
            # Patrón de líneas animado
            for j in range(0, width, 30):
                x1 = (j + i * 2) % width
                draw.line([(x1, 0), (x1, height)], fill=(255, 255, 255, 100), width=1)
            
            frames.append(img)
        
        # Guardar como GIF
        frames[0].save(
            os.path.join("fondos_instituto", "fondo_menu.gif"),
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
            optimize=True
        )
