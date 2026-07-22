
from fpdf import FPDF
from pathlib import Path
import json
import requests
from PIL import Image
import io
from datetime import datetime

from core.translations import get_text

class PDFGenerator:
    """Genera cuadernillos y diplomas PDF con ejercicios matemáticos y emojis."""
    
    def __init__(self, activities_file: Path, base_dir: Path = None):
        self.activities = self._load_activities(activities_file)
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.emoji_dir = self.base_dir / "assets" / "emojis"
        self.emoji_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_activities(self, file_path: Path) -> list:
        if not file_path.exists():
            return []
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return data.get("activities", [])
        except Exception as e:
            print(f"❌ Error cargando actividades: {e}")
            return []
    
    def _download_emoji_image(self, emoji_char: str, size: int = 24) -> Path:
        code = format(ord(emoji_char), 'x')
        img_path = self.emoji_dir / f"{code}_{size}.png"
        
        if not img_path.exists():
            url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{code}.png"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    img.save(img_path, "PNG")
            except Exception as e:
                print(f"⚠️ Error descargando {emoji_char}: {e}")
                return None
        return img_path if img_path.exists() else None
    
    def generate_workbook(self, level: int, output_path: Path, lang: str = "es") -> Path:
        activities = [a for a in self.activities if a["level"] == level]
        if not activities:
            raise ValueError(f"No hay actividades para el nivel {level}")
        
        pdf = FPDF()
        pdf.add_page()
        
        # 1. Encabezado colorido
        pdf.set_fill_color(255, 223, 0) # Amarillo
        pdf.rect(0, 0, 210, 40, 'F') # Barra superior
        
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(74, 20, 140) # Índigo
        title = get_text(lang, "workbook_title")
        pdf.cell(0, 15, f"{title} {level}", ln=True, align="C")
        
        # Campo para nombre y fecha
        pdf.set_font("Helvetica", "", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        nombre_label = "Nombre:" if lang == "es" else "Name:"
        fecha_label = "Fecha:" if lang == "es" else "Date:"
        pdf.cell(90, 10, f"{nombre_label} ________________________", ln=False)
        pdf.cell(0, 10, f"{fecha_label} ________________", ln=True)
        
        pdf.ln(10)
        
        # 2. Ejercicios
        pdf.set_font("Helvetica", "B", 16) # Letra más grande para niños
        for i, activity in enumerate(activities[:8], 1): # 8 ejercicios por página para que queden grandes
            emoji_char = activity["emoji"]
            total = activity["total"]
            operation = activity["operation"]
            
            emoji_img_path = self._download_emoji_image(emoji_char, size=30) # Emojis más grandes
            
            # Color según operación
            if operation == "+":
                pdf.set_text_color(0, 128, 0) # Verde para suma
            elif operation == "-":
                pdf.set_text_color(200, 0, 0) # Rojo para resta
            elif operation == "×":
                pdf.set_text_color(0, 0, 200) # Azul para multiplicación
            else:
                pdf.set_text_color(128, 0, 128) # Morado para división
            
            pdf.cell(15, 20, f"{i}.", ln=False)
            
            if emoji_img_path:
                try:
                    pdf.image(emoji_img_path, x=pdf.get_x(), y=pdf.get_y(), w=15, h=15)
                    pdf.set_x(pdf.get_x() + 18)
                except:
                    pdf.cell(20, 20, " ", ln=False)
            else:
                pdf.cell(20, 20, " ", ln=False)
            
            # Ecuación grande
            if operation == "-":
                text = f"{total}  -  {activity['remove']}  =  ______"
            elif operation == "+":
                text = f"{total}  +  {activity['add']}  =  ______"
            elif operation == "×":
                text = f"{activity['groups']}  ×  {activity['per_group']}  =  ______"
            elif operation == "÷":
                text = f"{total}  ÷  {activity['divisor']}  =  ______"
            
            pdf.cell(0, 20, text, ln=True)
            pdf.ln(5)
            
            # Línea separadora suave
            pdf.set_draw_color(200, 200, 200)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)
        
        # 3. Pie de página divertido
        pdf.set_y(-20)
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        footer = get_text(lang, "footer")
        pdf.cell(0, 10, footer, ln=True, align="C")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(output_path))
        return output_path
    
    def generate_diploma(self, user_name: str, level: int, stars: int, output_path: Path, lang: str = "es") -> Path:
        """Genera un diploma de reconocimiento en PDF con soporte bilingüe."""
        from core.translations import get_text
        from datetime import datetime
        
        pdf = FPDF(orientation="L", format="A4")
        pdf.add_page()
        
        # ===== BORDE DECORATIVO =====
        pdf.set_draw_color(255, 215, 0)  # Dorado
        pdf.set_line_width(3)
        pdf.rect(10, 10, 277, 190)
        pdf.set_line_width(1)
        pdf.rect(15, 15, 267, 180)
        
        # ===== EMOJIS COMO IMÁGENES (no como texto) =====
        medal_img = self._download_emoji_image("🏅", size=80)
        star_img = self._download_emoji_image("⭐", size=60)
        
        if medal_img:
            try:
                pdf.image(medal_img, x=235, y=20, w=35, h=35)
            except Exception as e:
                print(f"⚠️ No se pudo insertar medalla: {e}")
        
        if star_img:
            try:
                pdf.image(star_img, x=20, y=25, w=30, h=30)
            except Exception as e:
                print(f"️ No se pudo insertar estrella: {e}")
        
        # ===== TÍTULO =====
        pdf.set_font("Helvetica", "B", 36)
        pdf.set_text_color(74, 20, 140)  # Índigo
        pdf.cell(0, 35, get_text(lang, "diploma_title"), ln=True, align="C")
        
        # ===== SUBTÍTULO =====
        pdf.set_font("Helvetica", "I", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 15, get_text(lang, "diploma_subtitle"), ln=True, align="C")
        
        # ===== NOMBRE DEL NIÑO =====
        pdf.set_font("Helvetica", "B", 28)
        pdf.set_text_color(0, 100, 0)  # Verde
        pdf.cell(0, 25, user_name.upper(), ln=True, align="C")
        
        # ===== LOGRO (SIN EMOJIS EN TEXTO) =====
        pdf.set_font("Helvetica", "", 16)
        pdf.set_text_color(0, 0, 0)
        stars_text = get_text(lang, "stars_text")
        
        # Construir texto sin emojis
        achievement_text = f"{get_text(lang, 'completed_level')} {level}\n{get_text(lang, 'with_grade')} {stars} {stars_text}."
        
        pdf.multi_cell(0, 10, achievement_text, align="C")
        
        # Pequeña medalla como imagen (no emoji en texto)
        small_medal = self._download_emoji_image("🏅", size=30)
        if small_medal:
            try:
                x_medal = (297 - 15) / 2
                y_medal = pdf.get_y() + 5
                pdf.image(small_medal, x=x_medal, y=y_medal, w=15, h=15)
            except:
                pass
        
        # ===== FECHA =====
        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 12)
        if lang == "es":
            fecha = datetime.now().strftime("%d de %B de %Y")
        else:
            fecha = datetime.now().strftime("%B %d, %Y")
        pdf.cell(0, 10, f"{get_text(lang, 'date')}: {fecha}", ln=True, align="C")
        
        # ===== LÍNEA DE FIRMA =====
        pdf.ln(12)
        pdf.set_draw_color(0, 0, 0)
        pdf.line(80, 160, 180, 160)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, get_text(lang, "teacher_signature"), ln=True, align="C")
        
        # ===== FOOTER (SIN EMOJIS - SOLO TEXTO) =====
        pdf.set_y(-15)
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        # Versión sin emojis del footer
        footer_text = f"Generated by MateKids - Learning is Fun!" if lang == "en" else "Generado por MateKids - ¡Aprender es divertido!"
        pdf.cell(0, 10, footer_text, ln=True, align="C")
        
        # ===== GUARDAR =====
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(output_path))
        print(f"✅ Diploma generado: {output_path}")
        return output_path