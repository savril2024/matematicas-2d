import asyncio
import flet as ft
import random
from core.narrator import Narrator
from core.speech import SpeechRecognizer, text_to_number
from core.translations import get_text

class ActivityEngine:
    """Motor del juego. Maneja la UI, animaciones y lógica matemática."""

    def __init__(self, page: ft.Page, activity: dict, on_finish, lang: str = "es"):
        self.page = page
        self.data = activity
        self.on_finish = on_finish
        self.lang = lang
        self.lang_code = "es-ES" if lang == "es" else "en-US"
        self.is_listening = False

        # 1. Elementos de la Interfaz
        self.subtitle = ft.Text("", size=22, italic=True, color=ft.Colors.BLUE_GREY_700, 
                                text_align=ft.TextAlign.CENTER, width=600)
        self.objects_view = ft.Row(wrap=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        self.feedback = ft.Text("", size=36, weight=ft.FontWeight.BOLD)
        self.confetti_layer = ft.Stack(expand=True)

        # 2. Módulos de Voz (TTS y STT)
        self.narrator = Narrator(lang=lang, on_text=self._show_subtitle)
        self.narrator.set_page(page)

        self.speech_recognizer = SpeechRecognizer(lang=lang)
        self.speech_recognizer.set_page(page)

    def build(self) -> ft.Control:
        """Construye la vista principal del ejercicio."""
        title_text = self.data["title"]
        if isinstance(title_text, dict):
            title_text = title_text.get(self.lang, title_text.get("es", ""))

        return ft.Stack([
            ft.Column([
                ft.Text(title_text, size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO),
                ft.Container(height=20),
                self.objects_view,
                ft.Container(height=20),
                self.subtitle,
                self.feedback,
                ft.Container(height=10),
                self._build_options(),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            self.confetti_layer
        ], expand=True)

    async def run(self):
        """Flujo principal del ejercicio."""
        self._reset()
        op = self.data["operation"]

        # Obtener narración en el idioma correcto
        narration = self.data["narration"]
        if isinstance(narration, dict) and self.lang in narration:
            narration = narration[self.lang]
        elif isinstance(narration, dict) and "es" in narration:
            narration = narration["es"]

        # Paso 1: Mostrar objetos iniciales
        if op in ("+", "-"):
            self._render_objects(self.data["total"])
        elif op == "×":
            self._render_groups(self.data["groups"], self.data["per_group"])
        elif op == "÷":
            self._render_objects(self.data["total"])

        await self._wait(500)
        await self._speak(narration.get("intro", ""))
        await self._wait(500)

        # Paso 2: Animación de la operación
        if op == "-":
            await self._animate_remove(self.data["remove"])
        elif op == "+":
            await self._animate_add(self.data["add"])
        elif op == "×":
            await self._animate_multiply()
        elif op == "÷":
            await self._animate_divide(self.data["divisor"])

        await self._speak(narration.get("action", ""))
        await self._wait(500)
        await self._speak(narration.get("question", ""))

    # ==========================================
    # RENDERIZADO VISUAL
    # ==========================================

    def _reset(self):
        self.objects_view.controls = []
        self.feedback.value = ""
        self.subtitle.value = ""
        self.confetti_layer.controls = []
        self.page.update()

    def _make_emoji(self, emoji: str, size: int = 40) -> ft.Image:
        """Crea una imagen SVG de Twemoji para que siempre se vea a color en la web."""
        emoji_codes = {
            "🍎": "1f34e", "🍕": "1f355", "🚗": "1f697", "🚕": "1f695",
            "🐟": "1f41f", "🐶": "1f436", "⭐": "2b50", "🎈": "1f388",
            "📚": "1f4da", "🎒": "1f392", "✏️": "270f-fe0f", "📐": "1f4d0",
            "🖍️": "1f58d-fe0f", "🏆": "1f3c6", "🍪": "1f36a", "🍬": "1f36c",
            "🌸": "1f338", "👩": "1f469-200d-1f9b0"
        }
       
        code = emoji_codes.get(emoji, "1f34e")
        url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/{code}.svg"
        return ft.Image(src=url, width=size, height=size, fit=ft.ImageFit.CONTAIN, animate_scale=ft.Animation(400))

    def _render_objects(self, count: int):
        """Renderiza objetos. Si son >= 10, los agrupa en decenas y unidades."""
        self.objects_view.controls.clear()
        
        if count < 10:
            for _ in range(count):
                self.objects_view.controls.append(self._make_emoji(self.data["emoji"]))
        else:
            tens = count // 10
            units = count % 10
            main_container = ft.Row(wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER)
            
            for _ in range(tens):
                ten_group = ft.Container(
                    content=ft.Row([self._make_emoji(self.data["emoji"], size=32) for _ in range(10)], spacing=2, wrap=True),
                    border=ft.border.all(2, ft.Colors.BLUE),
                    border_radius=10,
                    padding=8,
                    bgcolor=ft.Colors.BLUE_50,
                )
                main_container.controls.append(ten_group)
            
            if units > 0:
                units_container = ft.Container(
                    content=ft.Row([self._make_emoji(self.data["emoji"], size=32) for _ in range(units)], spacing=2),
                    border=ft.border.all(2, ft.Colors.ORANGE),
                    border_radius=10,
                    padding=8,
                    bgcolor=ft.Colors.ORANGE_50,
                )
                main_container.controls.append(units_container)
            
            self.objects_view.controls.append(main_container)
        self.page.update()

    def _render_groups(self, groups: int, per_group: int):
        """Renderiza grupos para multiplicación."""
        self.objects_view.controls.clear()
        for _ in range(groups):
            group = ft.Container(
                content=ft.Row([self._make_emoji(self.data["emoji"], size=35) for _ in range(per_group)], spacing=3, wrap=True),
                border=ft.border.all(2, ft.Colors.GREEN),
                border_radius=10,
                padding=8,
                bgcolor=ft.Colors.GREEN_50,
            )
            self.objects_view.controls.append(group)
        self.page.update()

    # ==========================================
    # ANIMACIONES
    # ==========================================

    async def _animate_remove(self, n: int):
        controls = self.objects_view.controls[:]
        to_remove = controls[-n:] if len(controls) >= n else controls
        
        for obj in to_remove:
            if hasattr(obj, 'opacity'):
                obj.opacity = 0.3
                obj.scale = 0.5
                self.page.update()
                await self._wait(300)
        
        for obj in to_remove:
            if obj in self.objects_view.controls:
                self.objects_view.controls.remove(obj)
        self.page.update()
        await self._wait(200)

    async def _animate_add(self, n: int):
        for _ in range(n):
            new_obj = self._make_emoji(self.data["emoji"])
            new_obj.scale = 0
            new_obj.opacity = 0
            
            self.objects_view.controls.append(new_obj)
            self.page.update()
            await self._wait(100)
            
            new_obj.scale = 1.3
            new_obj.opacity = 1
            self.page.update()
            await self._wait(200)
            
            new_obj.scale = 1
            self.page.update()

    async def _animate_multiply(self):
        for group in self.objects_view.controls:
            if isinstance(group, ft.Container) and isinstance(group.content, ft.Row):
                for obj in group.content.controls:
                    if hasattr(obj, 'scale'):
                        obj.scale = 1.3
                self.page.update()
                await self._wait(400)
                for obj in group.content.controls:
                    if hasattr(obj, 'scale'):
                        obj.scale = 1
                self.page.update()

    async def _animate_divide(self, divisor: int):
        total_objects = len(self.objects_view.controls)
        self.objects_view.controls.clear()
        group_containers = []
        
        for _ in range(divisor):
            container = ft.Container(
                content=ft.Row(spacing=3, wrap=True),
                border=ft.border.all(2, ft.Colors.PURPLE),
                border_radius=10,
                padding=10,
                bgcolor=ft.Colors.PURPLE_50,
                width=100,
                height=100
            )
            group_containers.append(container)
            self.objects_view.controls.append(container)
        
        self.page.update()
        await self._wait(300)
        
        objects_to_distribute = [self._make_emoji(self.data["emoji"]) for _ in range(total_objects)]
        
        for idx, obj in enumerate(objects_to_distribute):
            group_idx = idx % divisor
            target_container = group_containers[group_idx]
            if isinstance(target_container.content, ft.Row):
                target_container.content.controls.append(obj)
            self.page.update()
            await self._wait(250)

    # ==========================================
    # UI DE RESPUESTA Y VALIDACIÓN
    # ==========================================

    def _build_options(self) -> ft.Control:
        col = ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=16)
        for opt in self.data["options"]:
            row.controls.append(
                ft.Button(
                    content=ft.Text(str(opt), size=34, weight=ft.FontWeight.BOLD),
                    width=90, height=90,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), bgcolor=ft.Colors.BLUE_100, color=ft.Colors.BLACK),
                    on_click=lambda e, v=opt: self._check(v)
                )
            )
        col.controls.append(row)
        
        mic_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.MIC, color=ft.Colors.WHITE, size=30),
                ft.Text("Responder con tu voz", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            width=280, height=60,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), bgcolor=ft.Colors.DEEP_PURPLE),
            on_click=self._start_listening
        )
        col.controls.append(mic_btn)
        
        return col

    def _check(self, value: int):
        correct = value == self.data["answer"]
        if correct:
            self.feedback.value = get_text(self.lang, "very_good")
            self.feedback.color = ft.Colors.GREEN
            self._launch_confetti()
            self.narrator.speak(f"{get_text(self.lang, 'very_good').replace('⭐', '').strip()} {self.data['answer']}.")
            self.on_finish(success=True, stars=1)
        else:
            self.feedback.value = get_text(self.lang, "try_again")
            self.feedback.color = ft.Colors.ORANGE
            self.narrator.speak(get_text(self.lang, "almost"))
            self.on_finish(success=False, stars=0)

    def _launch_confetti(self):
        emojis = ["🎉", "⭐", "🎊", "✨", "🎎"]
        for _ in range(15):
            e = ft.Text(random.choice(emojis), size=32, top=-50, left=random.randint(20, 500))
            self.confetti_layer.controls.append(e)
        self.page.update()
        self.page.run_task(self._clear_confetti)

    async def _clear_confetti(self):
        await self._wait(1500)
        self.confetti_layer.controls = []
        self.page.update()

    # ==========================================
    # RECONOCIMIENTO DE VOZ (Integración con speech.py)
    # ==========================================
    def _start_listening(self, e):
        if self.is_listening:
            return

        self.is_listening = True
        msg = (
            "🎙️ El reconocimiento de voz llega pronto. ¡Usa los botones por ahora!"
            if self.lang == "es"
            else "🎙️ Voice recognition is coming soon. Use the buttons for now!"
        )
        self.feedback.value = msg
        self.feedback.color = ft.Colors.DEEP_PURPLE
        self.page.update()

        self.narrator.speak(
            "El reconocimiento de voz llega pronto. Usa los botones."
            if self.lang == "es"
            else "Voice recognition is coming soon. Use the buttons."
        )

        self.page.run_task(self._reset_listening_state)

    async def _reset_listening_state(self):
        await self._wait(4000)
        self.is_listening = False
        self.feedback.value = ""
        self.page.update()

    # def _start_listening(self, e):
    #     if self.is_listening:
    #         return
        
    #     self.is_listening = True
    #     self.feedback.value = "🎙️ ¡Te escucho! Habla ahora..."
    #     self.feedback.color = ft.Colors.RED
    #     self.page.update()
        
    #     self.speech_recognizer.start_listening(
    #         on_result=self._on_voice_result,
    #         on_error=self._on_voice_error,
    #         on_end=lambda: setattr(self, 'is_listening', False)
    #     )

    def _on_voice_result(self, text: str):
        self.feedback.value = ""
        number = text_to_number(text, self.lang)
        
        if number is not None:
            self.subtitle.value = f'Dijiste: "{text}" ({number})'
            self._check(number)
        else:
            self.subtitle.value = f'Dijiste: "{text}"'
            self.feedback.value = "🤔 No entendí el número. ¡Intenta de nuevo!"
            self.feedback.color = ft.Colors.ORANGE
            self.narrator.speak("No entendí el número. Intenta de nuevo." if self.lang == "es" else "I didn't catch the number. Try again.")
            self.page.update()

    def _on_voice_error(self, error: str):
        self.is_listening = False
        self.feedback.value = ""
        error_messages = {
            "not_supported": "Tu navegador no soporta voz",
            "no-speech": "No se detectó voz",
            "audio-capture": "No se encontró el micrófono",
            "network": "Error de red"
        }
        msg = error_messages.get(error, "Error en el reconocimiento")
        self.feedback.value = f"⚠️ {msg}"
        self.feedback.color = ft.Colors.RED
        self.page.update()

    # ==========================================
    # HELPERS
    # ==========================================

    def _show_subtitle(self, text: str):
        self.subtitle.value = f'"{text}"'
        self.page.update()

    async def _speak(self, text: str):
        if text:
            await self.narrator.speak_and_wait(text)

    async def _wait(self, ms: int):
        await asyncio.sleep(ms / 2000)