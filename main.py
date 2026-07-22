import asyncio
import flet as ft
import json
import random
from pathlib import Path

from core.engine import ActivityEngine
from core import users
from core.pdf_generator import PDFGenerator
from core.translations import get_text

# Ruta absoluta segura
BASE_DIR = Path(__file__).resolve().parent
ACTIVITIES_FILE = BASE_DIR / "data" / "activities.json"


def load_activities() -> list:
    if not ACTIVITIES_FILE.exists():
        print(f"⚠️ ADVERTENCIA: No se encontró {ACTIVITIES_FILE}")
        return []
    try:
        data = json.loads(ACTIVITIES_FILE.read_text(encoding="utf-8"))
        return data.get("activities", [])
    except Exception as e:
        print(f"⚠️ ERROR leyendo JSON: {e}")
        return []

def rounded_button(text_content, bgcolor, width, height, on_click, text_size=20, text_color="white"):
    return ft.Button(
        content=ft.Text(text_content, size=text_size, weight=ft.FontWeight.BOLD, color=text_color),
        width=width,
        height=height,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=20),
            bgcolor=bgcolor,
            color=text_color,
        ),
        on_click=on_click
    )

def main(page: ft.Page):
    page.title = "MateKids 🧮"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.VerticalAlignment.CENTER
    page.padding = 20
    
    # Configuración de ventana compatible con Flet 0.23+
    if hasattr(page, 'window'):
        page.window.width = 900
        page.window.height = 700

    current_user = None
    current_level = 1
    score = 0
    activities_done = 0
    MAX_PER_SESSION = 5
    current_lang = "es"

    # ==========================================
    # 1. VISTA DE LOGIN
    # ==========================================
    selected_avatar = users.AVATARS[0]
    avatar_buttons = []

    def on_avatar_pick(e, selected: str):
        nonlocal selected_avatar
        selected_avatar = selected
        for btn in avatar_buttons:
            btn.bgcolor = ft.Colors.YELLOW_200 if getattr(btn, '_avatar', '') == selected_avatar else ft.Colors.GREY_200
        page.update()

    avatar_grid = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=15)
    for i, a in enumerate(users.AVATARS):
        # Usamos Container con ink=True para que el emoji mantenga su color y tenga efecto de clic
        avatar_container = ft.Container(
            content=ft.Text(a, size=40),
            width=70,
            height=70,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.YELLOW_200 if i == 0 else ft.Colors.GREY_200,
            border_radius=20,
            ink=True,
            on_click=lambda e, avatar=a: on_avatar_pick(e, avatar)
        )
        avatar_container._avatar = a
        avatar_buttons.append(avatar_container)
        avatar_grid.controls.append(avatar_container)

    name_field = ft.TextField(
        label=get_text(current_lang, "your_name"), 
        text_size=22, 
        width=350, 
        text_align=ft.TextAlign.CENTER, 
        border_radius=20
    )

    def update_language(lang: str):
        nonlocal current_lang
        current_lang = lang
        name_field.label = get_text(current_lang, "your_name")
        login_welcome.value = get_text(current_lang, "welcome")
        login_choose_avatar.value = get_text(current_lang, "choose_avatar")
        login_start_btn.content.value = get_text(current_lang, "start_playing")
        page.update()

    lang_dropdown = ft.Dropdown(
        label="Language / Idioma",
        options=[
            ft.dropdown.Option(key="es", text="🇪🇸 Español"),
            ft.dropdown.Option(key="en", text="🇬🇧 English"),
        ],
        value="es",
        width=220,
        on_change=lambda e: update_language(e.control.value)
    )

    def do_login(e):
        nonlocal current_user
        name = name_field.value.strip()
        if not name:
            name_field.error_text = get_text(current_lang, "name_required")
            page.update()
            return
        current_user = users.create_user(name, selected_avatar, current_lang)
        show_home()

    login_welcome = ft.Text(get_text(current_lang, "welcome"), size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO)
    login_choose_avatar = ft.Text(get_text(current_lang, "choose_avatar"), size=20)
    login_start_btn = rounded_button(get_text(current_lang, "start_playing"), ft.Colors.GREEN, 280, 60, do_login, text_size=22)

    login_view = ft.Column([
        login_welcome,
        login_choose_avatar,
        avatar_grid,
        ft.Container(height=20),
        lang_dropdown,
        ft.Container(height=10),
        name_field,
        ft.Container(height=10),
        login_start_btn
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    # ==========================================
    # 2. VISTA DE INICIO (HOME)
    # ==========================================
    home_title = ft.Text("", size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO)
    stars_label = ft.Text("", size=22)
    pdf_status = ft.Text("", size=16, color=ft.Colors.GREEN)

    def pick_level(lvl: int):
        nonlocal current_level, score, activities_done
        current_level = lvl
        score = 0
        activities_done = 0
        show_game()

    def generate_pdf(e):
        try:
            generator = PDFGenerator(ACTIVITIES_FILE, BASE_DIR)
            output_path = BASE_DIR / "data" / f"cuadernillo_nivel_{current_level}_{current_lang}.pdf"
            generator.generate_workbook(current_level, output_path, current_lang)
            pdf_status.value = f"{get_text(current_lang, 'pdf_saved')} {output_path.name}"
            page.update()
        except Exception as ex:
            pdf_status.value = f"{get_text(current_lang, 'pdf_error')}: {ex}"
            page.update()

    def toggle_home_language(e):
        nonlocal current_lang
        current_lang = "en" if current_lang == "es" else "es"
        
        # Actualizar textos dinámicos del home
        home_title.value = f"{get_text(current_lang, 'greeting')} {current_user['avatar']} {current_user['name']}!"
        stars_label.value = f" {get_text(current_lang, 'stars')}: {current_user.get('stars', 0)}"
        choose_level_text.value = get_text(current_lang, "choose_level")
        lang_toggle_btn.tooltip = "Cambiar idioma / Change language"
        
        # Actualizar botones
        level_btns.controls[0].content.value = get_text(current_lang, "level_1")
        level_btns.controls[1].content.value = get_text(current_lang, "level_2")
        level_btns.controls[2].content.value = get_text(current_lang, "level_3")
        pdf_btn.content.value = get_text(current_lang, "generate_pdf")
        page.update()

    lang_toggle_btn = ft.IconButton(
        icon=ft.Icons.LANGUAGE,
        tooltip="Cambiar idioma / Change language",
        icon_size=30,
        on_click=toggle_home_language
    )

    choose_level_text = ft.Text(get_text(current_lang, "choose_level"), size=26, weight=ft.FontWeight.BOLD)
    level_btns = ft.Row([
        rounded_button(get_text(current_lang, "level_1"), ft.Colors.GREEN, 220, 100, lambda e, l=1: pick_level(l), text_size=22),
        rounded_button(get_text(current_lang, "level_2"), ft.Colors.BLUE, 220, 100, lambda e, l=2: pick_level(l), text_size=22),
        rounded_button(get_text(current_lang, "level_3"), ft.Colors.PURPLE, 220, 100, lambda e, l=3: pick_level(l), text_size=22),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)

    pdf_btn = rounded_button(get_text(current_lang, "generate_pdf"), ft.Colors.PURPLE, 260, 60, generate_pdf, text_size=18)

    home_view = ft.Column([
        ft.Row([lang_toggle_btn], alignment=ft.MainAxisAlignment.END),
        home_title, 
        stars_label,
        ft.Container(height=30),
        choose_level_text,
        ft.Container(height=10),
        level_btns,
        ft.Container(height=20),
        pdf_btn,
        pdf_status
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    def show_home():
        home_title.value = f"{get_text(current_lang, 'greeting')} {current_user['avatar']} {current_user['name']}!"
        stars_label.value = f" {get_text(current_lang, 'stars')}: {current_user.get('stars', 0)}"
        page.views.clear()
        page.views.append(ft.View("/", [home_view]))
        page.update()

    # ==========================================
    # 3. VISTA DE JUEGO (GAME)
    # ==========================================
    game_column = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    game_view = ft.View("/game", [game_column], horizontal_alignment=ft.CrossAxisAlignment.CENTER, vertical_alignment=ft.VerticalAlignment.CENTER)
     
    #aqui reemplazo
    def show_game():
        pool = [a for a in load_activities() if a["level"] == current_level]
        if not pool:
            pdf_status.value = get_text(current_lang, "no_activities")
            page.update()
            return
            
        activity = random.choice(pool)

        # Botón de cambio de idioma en el juego
        def toggle_game_language(e):
            nonlocal current_lang
            current_lang = "en" if current_lang == "es" else "es"
            # Recargar el juego con el nuevo idioma
            show_game()

        game_lang_btn = ft.IconButton(
            icon=ft.Icons.LANGUAGE,
            icon_size=25,
            tooltip="Cambiar idioma",
            on_click=toggle_game_language
        )

        def on_finish(success: bool, stars: int):
            nonlocal score, activities_done
            if success:
                score += stars
                users.add_stars(current_user["name"], stars)
            activities_done += 1
            page.run_task(next_activity)

        async def next_activity():
            await asyncio.sleep(2)
            if activities_done >= MAX_PER_SESSION:
                show_result()
            else:
                show_game()
         # Pasamos current_lang al motor        
        engine = ActivityEngine(page, activity, on_finish, current_lang)
    
        # Agregar botón de idioma en la parte superior
        game_column.controls = [
            ft.Row([game_lang_btn], alignment=ft.MainAxisAlignment.END),
            engine.build()
        ]

       
       # engine = ActivityEngine(page, activity, on_finish, current_lang)
       # game_column.controls = [engine.build()]
        page.views.clear()
        page.views.append(game_view)
        page.update()
        page.run_task(engine.run)

    # ==========================================
    # 4. VISTA DE RESULTADOS (RESULT)
    # ==========================================
    result_title = ft.Text("", size=38, weight=ft.FontWeight.BOLD)
    result_msg = ft.Text("", size=24)
    diploma_status = ft.Text("", size=14, color=ft.Colors.GREEN, italic=True)

    def generate_diploma_action(e):
        try:
            generator = PDFGenerator(ACTIVITIES_FILE, BASE_DIR)
            safe_name = current_user["name"].replace(" ", "_").lower()
            output_path = BASE_DIR / "data" / f"diploma_nivel_{current_level}_{safe_name}_{current_lang}.pdf"
            
            generator.generate_diploma(
                user_name=current_user["name"],
                level=current_level,
                stars=score,
                output_path=output_path,
                lang=current_lang
            )
            diploma_status.value = f"{get_text(current_lang, 'diploma_saved')} {output_path.name}!"
            page.update()
        except Exception as ex:
            diploma_status.value = f"{get_text(current_lang, 'diploma_error')}: {ex}"
            page.update()

    result_view = ft.Column([
        result_title, 
        result_msg,
        ft.Container(height=20),
        rounded_button(get_text(current_lang, "generate_diploma"), ft.Colors.AMBER, 280, 60, generate_diploma_action, text_size=20),
        diploma_status,
        ft.Container(height=10),
        rounded_button(get_text(current_lang, "back_home"), ft.Colors.INDIGO, 260, 60, lambda e: show_home(), text_size=20),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    def show_result():
        if score >= 3:
            result_title.value = f"{get_text(current_lang, 'congratulations')} {current_user['avatar']}!"
            result_title.color = ft.Colors.AMBER
        else:
            result_title.value = f"{get_text(current_lang, 'good_job')} {current_user['avatar']}!"
            result_title.color = ft.Colors.INDIGO
            
        result_msg.value = f"{get_text(current_lang, 'got_stars')} {score} {get_text(current_lang, 'stars_in_level')} {current_level}."
        diploma_status.value = ""
        
        page.views.clear()
        page.views.append(ft.View("/result", [result_view]))
        page.update()

    def show_login():
        page.views.clear()
        page.views.append(ft.View("/", [login_view]))
        page.update()

    # ==========================================
    # INICIO
    # ==========================================
    show_login()


if __name__ == "__main__":
    import os
    # Render asigna el puerto automáticamente en la variable de entorno PORT
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, assets_dir="assets")
    ft.app(
        target=main,
        port=port,
        host="0.0.0.0",  # Vital para que Render lo detecte
        view="web_browser",
    )
        