import flet as ft
import random
import threading
import queue
import pyttsx3
import sqlite3
import hashlib
import subprocess
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line
from reportlab.graphics import renderPDF

# ============================================================
# 1. MOTOR DE VOZ (Hilo permanente con cola)
# ============================================================
class MotorVoz:
    _instancia = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    def __init__(self):
        if not hasattr(self, 'inicializado'):
            self.cola = queue.Queue()
            self.engine = None
            self.hilo = threading.Thread(target=self._loop_voz, daemon=True)
            self.hilo.start()
            self.inicializado = True
    
    def _inicializar_engine(self):
        self.engine = pyttsx3.init()
        try:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'es-' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            self.engine.setProperty('rate', 140)
            self.engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"Error configurando voz: {e}")
    
    def _loop_voz(self):
        self._inicializar_engine()
        while True:
            try:
                texto = self.cola.get()
                if texto is None:
                    break
                if self.engine:
                    self.engine.say(texto)
                    self.engine.runAndWait()
                self.cola.task_done()
            except Exception as e:
                print(f"Error en loop de voz: {e}")
    
    def hablar(self, texto):
        self.cola.put(texto)
    
    def detener(self):
        self.cola.put(None)


# ============================================================
# 2. GESTOR DE BASE DE DATOS (SQLite Seguro)
# ============================================================
class GestorBaseDatos:
    def __init__(self, db_nombre="seguridad_matematicas.db"):
        self.db_nombre = db_nombre
        self.inicializar_bd()
    
    def obtener_conexion(self):
        return sqlite3.connect(self.db_nombre)
    
    def inicializar_bd(self):
        conn = self.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                rol TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        # Usuario Profesor (Contraseña: profe2024)
        hash_profe = hashlib.sha256("profe2024".encode()).hexdigest()
        cursor.execute('INSERT OR IGNORE INTO usuarios (nombre, rol, password_hash) VALUES (?, ?, ?)', 
                       ('admin', 'profesor', hash_profe))
        
        # Usuario Estudiante (PIN: 1234)
        hash_est = hashlib.sha256("1234".encode()).hexdigest()
        cursor.execute('INSERT OR IGNORE INTO usuarios (nombre, rol, password_hash) VALUES (?, ?, ?)', 
                       ('estudiante', 'alumno', hash_est))
        
        conn.commit()
        conn.close()

    def verificar_credenciales(self, nombre, password):
        conn = self.obtener_conexion()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('SELECT nombre, rol FROM usuarios WHERE nombre = ? AND password_hash = ?', (nombre, password_hash))
        resultado = cursor.fetchone()
        conn.close()
        return resultado

bd = GestorBaseDatos()


# ============================================================
# 3. GENERADOR DE PDF
# ============================================================
class GeneradorPDF:
    def crear_circulo(self, color, tamaño=30):
        drawing = Drawing(tamaño, tamaño)
        drawing.add(Circle(tamaño/2, tamaño/2, r=tamaño/2 - 3, fillColor=color, strokeColor=colors.black, strokeWidth=2))
        return drawing
    
    def crear_circulo_tachado(self, color, tamaño=30):
        drawing = Drawing(tamaño, tamaño)
        drawing.add(Circle(tamaño/2, tamaño/2, r=tamaño/2 - 3, fillColor=color, strokeColor=colors.black, strokeWidth=2))
        drawing.add(Line(5, 5, tamaño-5, tamaño-5, strokeColor=colors.red, strokeWidth=3))
        drawing.add(Line(tamaño-5, 5, 5, tamaño-5, strokeColor=colors.red, strokeWidth=3))
        return drawing
    
    def crear_pieza(self, color, tamaño=30):
        drawing = Drawing(tamaño, tamaño)
        drawing.add(Rect(2, 2, tamaño-4, tamaño-4, fillColor=color, strokeColor=colors.black, strokeWidth=2))
        return drawing
    
    def generar_cuadernillo(self, nombre_archivo="cuadernillo.pdf"):
        doc = canvas.Canvas(nombre_archivo, pagesize=A4)
        width, height = A4
        
        doc.setFillColor(colors.darkgreen)
        doc.rect(0, height - 150, width, 150, fill=1, stroke=0)
        doc.setFillColor(colors.white)
        doc.setFont("Helvetica-Bold", 28)
        doc.drawCentredString(width/2, height - 60, "CUADERNILLO DE MATEMÁTICAS")
        doc.setFont("Helvetica", 16)
        doc.drawCentredString(width/2, height - 90, "Sumas y Restas")
        doc.setFont("Helvetica", 14)
        doc.drawCentredString(width/2, height - 115, "Segundo Grado de Primaria")
        
        doc.setFillColor(colors.black)
        doc.setFont("Helvetica", 12)
        y_pos = height - 200
        doc.drawString(50, y_pos, "Nombre: _________________________________")
        y_pos -= 30
        doc.drawString(50, y_pos, "Fecha: _________________________________")
        doc.showPage()
        
        # Sumas
        doc.setFillColor(colors.darkblue)
        doc.rect(0, height - 50, width, 50, fill=1, stroke=0)
        doc.setFillColor(colors.white)
        doc.setFont("Helvetica-Bold", 18)
        doc.drawCentredString(width/2, height - 30, "SECCIÓN 1: SUMAS")
        y_pos = height - 80
        for i in range(4):
            if y_pos < 100:
                doc.showPage()
                y_pos = height - 50
            cant1, cant2 = random.randint(2, 5), random.randint(1, 4)
            doc.setFont("Helvetica-Bold", 12)
            doc.setFillColor(colors.black)
            doc.drawString(50, y_pos, f"Ejercicio {i+1}: ¿Qué suma muestra este dibujo?")
            y_pos -= 40
            x_pos = 50
            for _ in range(cant1):
                renderPDF.draw(self.crear_pieza(colors.purple, 35), doc, x_pos, y_pos - 35)
                x_pos += 40
            doc.setFont("Helvetica-Bold", 24)
            doc.drawString(x_pos + 10, y_pos - 25, "+")
            x_pos += 50
            for _ in range(cant2):
                renderPDF.draw(self.crear_pieza(colors.green, 35), doc, x_pos, y_pos - 35)
                x_pos += 40
            y_pos -= 60
            doc.setFont("Helvetica", 11)
            doc.drawString(50, y_pos, "Respuesta: __________")
            y_pos -= 40
        doc.showPage()
        
        # Restas
        doc.setFillColor(colors.darkred)
        doc.rect(0, height - 50, width, 50, fill=1, stroke=0)
        doc.setFillColor(colors.white)
        doc.setFont("Helvetica-Bold", 18)
        doc.drawCentredString(width/2, height - 30, "SECCIÓN 2: RESTAS")
        y_pos = height - 80
        for i in range(4):
            if y_pos < 100:
                doc.showPage()
                y_pos = height - 50
            total, tachados = random.randint(5, 8), random.randint(1, 3)
            doc.setFont("Helvetica-Bold", 12)
            doc.setFillColor(colors.black)
            doc.drawString(50, y_pos, f"Ejercicio {i+1}: ¿Qué resta muestra este dibujo?")
            y_pos -= 40
            x_pos = 50
            for j in range(total):
                figura = self.crear_circulo_tachado(colors.orange, 35) if j < tachados else self.crear_circulo(colors.orange, 35)
                renderPDF.draw(figura, doc, x_pos, y_pos - 35)
                x_pos += 40
            y_pos -= 60
            doc.setFont("Helvetica", 11)
            doc.drawString(50, y_pos, "Respuesta: __________")
            y_pos -= 40
        
        doc.save()
        return nombre_archivo


# ============================================================
# 4. UTILIDADES
# ============================================================
def abrir_firewall_windows(puerto):
    try:
        subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', 
                        f'name=Flet App Puerto {puerto}', 'dir=in', 'action=allow', 
                        'protocol=TCP', f'localport={puerto}'], 
                       check=True, capture_output=True)
    except Exception:
        pass


# ============================================================
# 5. APLICACIÓN PRINCIPAL
# ============================================================
class CuadernilloInteractivo:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Matemáticas 2do Grado"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.WHITE
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.window.width = 1000
        self.page.window.height = 750
        
        self.motor_voz = MotorVoz()
        self.generador_pdf = GeneradorPDF()
        
        self.puntos = 0
        self.ejercicio_actual = 0
        self.total_ejercicios = 10
        self.ejercicios = []
        self.respuestas_correctas = []
        self.contenedor_principal = None
        self.figuras_tachadas = set()
    
    def hablar(self, texto):
        """Audio híbrido: pyttsx3 (local) + Web Speech API (nube)"""
          # Intento 1: pyttsx3 (solo funciona en tu PC)
        try:
            self.motor_voz.hablar(texto)
        except Exception:
            pass
         # Intento 2: Web Speech API (funciona en el navegador del niño)
        try:
            texto_seguro = texto.replace("'", "\\'").replace('"', '\\"')
            self.page.run_javascript(f"""
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance('{texto_seguro}');
                    utterance.lang = 'es-ES';
                    utterance.rate = 0.9;
                    utterance.pitch = 1.1;
                    window.speechSynthesis.speak(utterance);
                }}
            """)
        except Exception:
            pass 
    
    def crear_borde(self, width=2, color=ft.Colors.BLUE):
        return ft.Border(
            top=ft.BorderSide(width=width, color=color),
            right=ft.BorderSide(width=width, color=color),
            bottom=ft.BorderSide(width=width, color=color),
            left=ft.BorderSide(width=width, color=color),
        )

    # --- PANTALLAS DE ACCESO ---
    def mostrar_login(self):
        self.page.clean()
        
        input_usuario = ft.TextField(label="Usuario", prefix_icon=ft.Icons.PERSON, width=300, text_align=ft.TextAlign.CENTER)
        input_password = ft.TextField(label="Contraseña o PIN", prefix_icon=ft.Icons.LOCK, password=True, 
                                      can_reveal_password=True, keyboard_type=ft.KeyboardType.NUMBER, 
                                      width=300, text_align=ft.TextAlign.CENTER,
                                      on_submit=lambda e: self.validar_login(input_usuario.value, input_password.value, texto_error))
        texto_error = ft.Text("", color=ft.Colors.RED, size=12)

        def validar_click(e):
            self.validar_login(input_usuario.value, input_password.value, texto_error)

        # CORRECCIÓN: alignment y expand van DENTRO del Container
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SCHOOL, size=80, color=ft.Colors.BLUE),
                    ft.Container(height=10),
                    ft.Text("Matemáticas 2do Grado", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(height=30),
                    input_usuario,
                    ft.Container(height=15),
                    input_password,
                    ft.Container(height=10),
                    texto_error,
                    ft.Container(height=20),
                    ft.Button("Ingresar", icon=ft.Icons.LOGIN, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, width=300, on_click=validar_click),
                    ft.Container(height=20),
                    ft.Text("💡 Tip: Usa 'estudiante' y '1234'", size=11, color=ft.Colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40, 
                border_radius=20, 
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(spread_radius=2, blur_radius=20, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                alignment=ft.Alignment.CENTER,  # <-- MOVIDO AQUÍ DENTRO
                expand=True                     # <-- MOVIDO AQUÍ DENTRO
            )
        )

    def validar_login(self, usuario, password, label_error):
        if not usuario or not password:
            label_error.value = "Por favor completa todos los campos."
            try: self.page.update()
            except: pass
            return

        resultado = bd.verificar_credenciales(usuario, password)
        if resultado:
            nombre, rol = resultado
            if rol == 'profesor':
                self.hablar(f"Bienvenido, profesor {nombre}.")
                self.pantalla_inicial_profesor()
            else:
                self.hablar("¡Hola! Vamos a practicar matemáticas.")
                self.iniciar_ejercicios_directo()
        else:
            label_error.value = "Usuario o contraseña incorrectos."
            try: self.page.update()
            except: pass

    def pantalla_inicial_profesor(self):
        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("PANEL DE CONTROL", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Acceso de Profesor / Padre", size=14, color=ft.Colors.WHITE70),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.INDIGO, padding=30, border_radius=10,
            ),
            ft.Container(height=30),
            ft.Row([
                ft.Container(
                    content=ft.Column([ft.Icon(ft.Icons.PICTURE_AS_PDF, size=60, color=ft.Colors.RED), ft.Text("Generar PDF", size=16, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30, border_radius=15, border=self.crear_borde(2, ft.Colors.RED),
                    on_click=lambda e: self.generar_pdf(), ink=True,
                ),
                ft.Container(width=30),
                ft.Container(
                    content=ft.Column([ft.Icon(ft.Icons.COMPUTER, size=60, color=ft.Colors.BLUE), ft.Text("Iniciar Clase", size=16, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30, border_radius=15, border=self.crear_borde(2, ft.Colors.BLUE),
                    on_click=lambda e: self.iniciar_ejercicios(), ink=True,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=30),
            ft.Button("Cerrar Sesión", icon=ft.Icons.LOGOUT, on_click=lambda e: self.mostrar_login())
        )

    def iniciar_ejercicios_directo(self):
        self.generar_ejercicios()
        self.contenedor_principal = ft.Column(scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Text("¡A PRACTICAR!", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                bgcolor=ft.Colors.GREEN, padding=20, border_radius=10,
            ),
            ft.Divider(),
            self.contenedor_principal,
            ft.Button("Salir", icon=ft.Icons.LOGOUT, on_click=lambda e: self.mostrar_login(), bgcolor=ft.Colors.GREY_300)
        )
        self.mostrar_ejercicio()

    # --- LÓGICA DE EJERCICIOS ---
    def generar_ejercicios(self):
        self.ejercicios = []
        self.figuras_tachadas = set()
        for _ in range(3):
            a, b = random.randint(2, 5), random.randint(1, 4)
            self.ejercicios.append({'tipo': 'suma_visual', 'a': a, 'b': b, 'respuesta': a + b, 'texto': "¿Qué suma muestra este dibujo?"})
        for _ in range(3):
            total, restar = random.randint(5, 8), random.randint(1, 3)
            self.ejercicios.append({'tipo': 'resta_visual', 'total': total, 'restar': restar, 'respuesta': total - restar, 'texto': "¿Qué resta muestra este dibujo?"})
        for _ in range(2):
            if random.choice([True, False]):
                a, b = random.randint(3, 7), random.randint(1, 4)
                self.ejercicios.append({'tipo': 'completar_suma', 'a': a, 'b': b, 'resultado': a + b, 'respuesta': b, 'texto': f"Completa: {a} + ___ = {a + b}"})
            else:
                total, resto = random.randint(6, 10), random.randint(1, 4)
                self.ejercicios.append({'tipo': 'completar_resta', 'total': total, 'resto': resto, 'resultado': total - resto, 'respuesta': total - resto, 'texto': f"Completa: {total} - {resto} = ___"})
        
        for prob in [{"texto": "María tiene 5 manzanas y su mamá le da 3 más. ¿Cuántas tiene?", "resp": 8},
                     {"texto": "Hay 8 pájaros. Si 3 vuelan, ¿cuántos quedan?", "resp": 5}]:
            self.ejercicios.append({'tipo': 'problema_verbal', 'texto': prob['texto'], 'respuesta': prob['resp']})
        
        random.shuffle(self.ejercicios)
        self.total_ejercicios = len(self.ejercicios)

    def generar_pdf(self):
        try:
            self.hablar("Generando PDF. Por favor espera.")
            nombre = f"cuadernillo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            self.generador_pdf.generar_cuadernillo(nombre)
            
            def cerrar(e):
                dlg.open = False
                try: self.page.update()
                except: pass
            
            dlg = ft.AlertDialog(title=ft.Text("PDF Generado", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                                 content=ft.Column([ft.Icon(ft.Icons.CHECK_CIRCLE, size=60, color=ft.Colors.GREEN), ft.Text(f"Archivo: {nombre}", size=12)]),
                                 actions=[ft.Button("Continuar", on_click=cerrar, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)])
            self.page.overlay.append(dlg)
            dlg.open = True
            try: self.page.update()
            except: pass
        except Exception as e:
            print(f"Error PDF: {e}")

    # --- PÁGINA DE AYUDA ---
    def mostrar_pagina_ayuda(self, ejercicio):
        self.page.clean()
        contenedor_ayuda = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
        
        contenedor_ayuda.controls.append(ft.Button("← Volver al ejercicio", icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.volver_desde_ayuda(ejercicio), bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE))
        contenedor_ayuda.controls.append(ft.Text("Aprender con un ejemplo", size=24, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD))
        contenedor_ayuda.controls.append(ft.Divider())
        
        if ejercicio['tipo'] == 'resta_visual':
            total, tachados, respuesta = ejercicio['total'], ejercicio['restar'], ejercicio['respuesta']
            
            figuras = []
            for i in range(total):
                if i < tachados:
                    figuras.append(ft.Stack([ft.Icon(ft.Icons.FACE, size=45, color=ft.Colors.ORANGE), ft.Icon(ft.Icons.CLOSE, size=50, color=ft.Colors.RED)]))
                else:
                    figuras.append(ft.Icon(ft.Icons.FACE, size=45, color=ft.Colors.ORANGE))
            
            contenedor_ayuda.controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([ft.Container(content=ft.Text("pregunta", size=11, color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN, padding=ft.Padding(8, 8, 8, 8), border_radius=5), ft.Container(width=15), ft.Text("¿Qué resta muestra este dibujo?", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=20),
                    ft.Row(figuras, alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ], spacing=10),
                padding=ft.Padding(20, 20, 20, 20), border_radius=10, border=self.crear_borde(1, ft.Colors.BLUE_200), bgcolor=ft.Colors.BLUE_50
            ))
            contenedor_ayuda.controls.append(ft.Container(height=15))
            
            pasos = [
                f"Primero, cuenta las caras, incluso las que se hayan tachado. Hay {total} caras.",
                f"Ahora cuenta cuántas caras se han tachado. {tachados} caras se han tachado.",
                f"La primera parte de la resta es {total} - {tachados}. Para hallar la diferencia, cuenta las caras que no se hayan tachado. {respuesta} caras no se han tachado. Este dibujo muestra la resta {total} - {tachados} = {respuesta}."
            ]
            
            columnas_pasos = []
            for paso in pasos:
                columnas_pasos.append(ft.Row([ft.IconButton(icon=ft.Icons.VOLUME_UP, icon_color=ft.Colors.BLUE, on_click=lambda e, t=paso: self.hablar(t), icon_size=24), ft.Container(width=10), ft.Text(paso, size=12, expand=True)], alignment=ft.MainAxisAlignment.START))
                columnas_pasos.append(ft.Container(height=10))
            
            contenedor_ayuda.controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([ft.Container(content=ft.Text("solución", size=11, color=ft.Colors.WHITE), bgcolor=ft.Colors.ORANGE, padding=ft.Padding(8, 8, 8, 8), border_radius=5), ft.Container(width=15)], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=10)
                ] + columnas_pasos, spacing=5),
                padding=ft.Padding(20, 20, 20, 20), border_radius=10, border=self.crear_borde(1, ft.Colors.ORANGE_200), bgcolor=ft.Colors.ORANGE_50
            ))
            self.hablar(pasos[0])
        
        self.page.add(ft.Container(content=contenedor_ayuda, padding=ft.Padding(20, 20, 20, 20), expand=True))
        try: self.page.update()
        except: pass

    def volver_desde_ayuda(self, ejercicio_guardado):
        self.page.clean()
        self.page.add(
            ft.Container(content=ft.Column([ft.Text("¡A PRACTICAR!", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=ft.Colors.GREEN, padding=20, border_radius=10),
            ft.Divider(),
            self.contenedor_principal,
            ft.Button("Salir", icon=ft.Icons.LOGOUT, on_click=lambda e: self.mostrar_login(), bgcolor=ft.Colors.GREY_300)
        )
        self.figuras_tachadas.clear()
        self.contenedor_principal.controls.clear()
        self._renderizar_contenido_ejercicio(ejercicio_guardado)
        try: self.page.update()
        except: pass

    def _renderizar_contenido_ejercicio(self, ejercicio):
        progreso = ft.ProgressBar(width=self.page.window.width - 100, value=(self.ejercicio_actual + 1) / self.total_ejercicios, color=ft.Colors.GREEN)
        titulo = ft.Text(f"Ejercicio {self.ejercicio_actual + 1} de {self.total_ejercicios}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        contenido = [
            ft.Button("Ver ayuda / ejemplo", icon=ft.Icons.HELP_OUTLINE, on_click=lambda e: self.mostrar_pagina_ayuda(ejercicio), bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ft.Container(height=10)
        ]
        
        if ejercicio['tipo'] == 'suma_visual':
            contenido.extend([ft.Text("SUMA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700), ft.Container(height=10)])
            contenido.extend(self._crear_figuras(ejercicio['a'], 'manzana'))
            contenido.append(ft.Text("+", size=30, text_align=ft.TextAlign.CENTER))
            contenido.extend(self._crear_figuras(ejercicio['b'], 'estrella'))
            contenido.append(ft.Text(ejercicio['texto'], size=14, italic=True))
            opciones = self._generar_opciones(ejercicio['respuesta'])
            contenido.extend([ft.Container(height=10), ft.Text("Selecciona la respuesta:", size=14)])
            contenido.append(ft.Row([self._crear_boton_opcion(op, ejercicio['respuesta'], ft.Colors.LIGHT_BLUE) for op in opciones], alignment=ft.MainAxisAlignment.CENTER))
        
        elif ejercicio['tipo'] == 'resta_visual':
            contenido.extend([ft.Text("RESTA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700), ft.Container(height=10)])
            contenido.extend(self._crear_figuras(ejercicio['total'], 'sol'))
            contenido.extend([ft.Container(height=10), ft.Text(ejercicio['texto'], size=14, italic=True)])
            opciones = self._generar_opciones(ejercicio['respuesta'])
            contenido.extend([ft.Container(height=10), ft.Text("Selecciona la respuesta:", size=14)])
            contenido.append(ft.Row([self._crear_boton_opcion(op, ejercicio['respuesta'], ft.Colors.LIGHT_GREEN) for op in opciones], alignment=ft.MainAxisAlignment.CENTER))
        
        elif ejercicio['tipo'] in ['completar_suma', 'completar_resta']:
            contenido.extend([ft.Text("COMPLETA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700), ft.Container(height=20)])
            texto = f"{ejercicio['a']} + ___ = {ejercicio['resultado']}" if ejercicio['tipo'] == 'completar_suma' else f"{ejercicio['total']} - {ejercicio['resto']} = ___"
            contenido.append(ft.Container(content=ft.Text(texto, size=24, weight=ft.FontWeight.BOLD), padding=20, bgcolor=ft.Colors.YELLOW_100, border_radius=10, border=self.crear_borde(2, ft.Colors.BLUE)))
            opciones = self._generar_opciones(ejercicio['respuesta'])
            contenido.extend([ft.Container(height=10), ft.Text("Selecciona la respuesta:", size=14)])
            contenido.append(ft.Row([self._crear_boton_opcion(op, ejercicio['respuesta'], ft.Colors.ORANGE) for op in opciones], alignment=ft.MainAxisAlignment.CENTER))
        
        elif ejercicio['tipo'] == 'problema_verbal':
            contenido.extend([ft.Text("PROBLEMA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700), ft.Container(height=10)])
            contenido.append(ft.Container(content=ft.Text(ejercicio['texto'], size=14), padding=15, bgcolor=ft.Colors.BLUE_50, border_radius=10, border=self.crear_borde(1, ft.Colors.BLUE_200)))
            opciones = self._generar_opciones(ejercicio['respuesta'])
            contenido.extend([ft.Container(height=10), ft.Text("Selecciona la respuesta:", size=14)])
            contenido.append(ft.Row([self._crear_boton_opcion(op, ejercicio['respuesta'], ft.Colors.PURPLE) for op in opciones], alignment=ft.MainAxisAlignment.CENTER))
        
        self.contenedor_principal.controls.extend([progreso, ft.Divider(), titulo, ft.Container(height=20), ft.Column(contenido, horizontal_alignment=ft.CrossAxisAlignment.CENTER)])

    def mostrar_ejercicio(self):
        if self.ejercicio_actual >= len(self.ejercicios):
            self.mostrar_resultados()
            return
        
        ejercicio = self.ejercicios[self.ejercicio_actual]
        self.figuras_tachadas.clear()
        
        if not self.contenedor_principal:
            self.contenedor_principal = ft.Column(scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            self.page.clean()
            self.page.add(
                ft.Container(content=ft.Column([ft.Text("¡A PRACTICAR!", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=ft.Colors.GREEN, padding=20, border_radius=10),
                ft.Divider(),
                self.contenedor_principal,
                ft.Button("Salir", icon=ft.Icons.LOGOUT, on_click=lambda e: self.mostrar_login(), bgcolor=ft.Colors.GREY_300)
            )
        else:
            self.contenedor_principal.controls.clear()
            
        self._renderizar_contenido_ejercicio(ejercicio)
        try: self.page.update()
        except: pass

    def _crear_figuras(self, cantidad, tipo):
        iconos = {'manzana': (ft.Icons.FAVORITE, ft.Colors.RED), 'estrella': (ft.Icons.STAR, ft.Colors.AMBER), 'sol': (ft.Icons.WB_SUNNY, ft.Colors.ORANGE)}
        icono, color = iconos.get(tipo, (ft.Icons.CIRCLE, ft.Colors.BLUE))
        
        def toggle_tachado(e, idx):
            if idx in self.figuras_tachadas:
                self.figuras_tachadas.remove(idx)
                e.control.content.color = color
                e.control.content.opacity = 1.0
            else:
                self.figuras_tachadas.add(idx)
                e.control.content.color = ft.Colors.GREY
                e.control.content.opacity = 0.3
            try: self.page.update()
            except: pass

        figuras = []
        for i in range(cantidad):
            figuras.append(ft.Container(content=ft.Icon(icono, size=40, color=color), on_click=lambda e, idx=i: toggle_tachado(e, idx), padding=5, border_radius=5))
        return [ft.Row(figuras, alignment=ft.MainAxisAlignment.CENTER, wrap=True)]

    def _generar_opciones(self, correcta):
        opciones = [correcta]
        while len(opciones) < 4:
            opcion = correcta + random.randint(-3, 3)
            if opcion > 0 and opcion not in opciones:
                opciones.append(opcion)
        random.shuffle(opciones)
        return opciones

    def _crear_boton_opcion(self, opcion, correcta, color_bg):
        return ft.Button(str(opcion), width=100, height=50, style=ft.ButtonStyle(bgcolor=color_bg, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)), on_click=lambda e, opt=opcion: self._verificar_respuesta(opt, correcta))

    def _verificar_respuesta(self, seleccion, correcta):
        if seleccion == correcta:
            self.puntos += 1
            self.respuestas_correctas.append(True)
            self.hablar("¡Correcto! Muy bien hecho.")
        else:
            self.respuestas_correctas.append(False)
            self.hablar(f"Incorrecto. La respuesta era {correcta}.")
        self.ejercicio_actual += 1
        self.figuras_tachadas.clear()
        self.mostrar_ejercicio()

    def mostrar_resultados(self):
        self.contenedor_principal.controls.clear()
        porcentaje = (self.puntos / self.total_ejercicios) * 100
        
        if porcentaje >= 80:
            mensaje, color, icono = "¡Excelente trabajo!", ft.Colors.GREEN, ft.Icons.EMOJI_EVENTS
        elif porcentaje >= 60:
            mensaje, color, icono = "¡Buen trabajo!", ft.Colors.BLUE, ft.Icons.THUMB_UP
        else:
            mensaje, color, icono = "Sigue practicando", ft.Colors.ORANGE, ft.Icons.SCHOOL
        
        self.contenedor_principal.controls.extend([
            ft.Icon(icono, size=80, color=ft.Colors.AMBER), ft.Container(height=20),
            ft.Text("EJERCICIOS COMPLETADOS", size=24, weight=ft.FontWeight.BOLD), ft.Divider(),
            ft.Text(mensaje, size=20, color=color, weight=ft.FontWeight.BOLD),
            ft.Text(f"Puntuación: {self.puntos} de {self.total_ejercicios}", size=16),
            ft.Text(f"Porcentaje: {porcentaje:.0f}%", size=16), ft.Divider(),
            ft.Row([
                ft.Button("Volver al inicio", icon=ft.Icons.HOME, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE), on_click=lambda e: self.pantalla_inicial_profesor()),
                ft.Button("Intentar de nuevo", icon=ft.Icons.REFRESH, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE), on_click=lambda e: self.iniciar_ejercicios_directo()),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
        ])
        self.hablar(f"Completaste {self.puntos} de {self.total_ejercicios}. {porcentaje:.0f} por ciento. {mensaje}")
        try: self.page.update()
        except: pass


# ============================================================
# 6. PUNTO DE ENTRADA
# ============================================================
import os

def main(page: ft.Page):
    app = CuadernilloInteractivo(page)
    app.mostrar_login()

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8550))
    ES_RENDER = os.environ.get("RENDER", "").lower() == "true"
    
    if ES_RENDER:
        print("🚀 Modo Render.com activado")
        print(f"📡 Puerto: {PORT}")
        print("🌍 Audio: Web Speech API del navegador")
    else:
        print("=" * 60)
        print("🖥️  Modo LOCAL (tu PC)")
        print(f"📱 Acceso local: http://localhost:{PORT}")
        print("=" * 60)
        try:
            abrir_firewall_windows(PORT)
        except Exception:
            pass
    
    ft.run(
        main,
        view="web_browser",
        host="0.0.0.0",
        port=PORT
    )