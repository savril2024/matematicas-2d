import flet as ft
import asyncio
import os
import hashlib
from gtts import gTTS


class Narrator:
    """Texto a voz (TTS) usando gTTS + ft.Audio — compatible con Flet Web."""

    def __init__(self, lang="es", on_text=None):
        self.lang = lang  # "es" o "en" (código corto que espera gTTS)
        self.on_text = on_text
        self.page = None
        self.audio_control = None
        self._finished_event = None

        # Carpeta donde se guardan los mp3 generados; debe estar
        # DENTRO de la carpeta assets_dir que declares en ft.app(...)
        self.assets_subdir = "audio"
        self.output_dir = os.path.join("assets", self.assets_subdir)
        os.makedirs(self.output_dir, exist_ok=True)

    def set_page(self, page: ft.Page):
        self.page = page
        self.audio_control = ft.Audio(
            src="",
            autoplay=False,
            on_state_changed=self._on_audio_state_changed,
        )
        self.page.overlay.append(self.audio_control)
        self.page.update()
        self._finished_event = asyncio.Event()

    def _on_audio_state_changed(self, e):
        if e.data == "completed" and self._finished_event:
            self._finished_event.set()

    def speak(self, text: str):
        """Dispara la narración sin esperar (fire-and-forget)."""
        if self.on_text:
            self.on_text(text)

        if not self.page or not text:
            print(f"[NARRATOR] {text}")
            return

        self.page.run_task(self._speak_async, text)

    async def speak_and_wait(self, text: str):
        """Genera y reproduce el audio, esperando a que termine antes de continuar."""
        if self.on_text:
            self.on_text(text)

        if not self.page or not text:
            print(f"[NARRATOR] {text}")
            return

        rel_path = await asyncio.to_thread(self._generate_audio, text)
        self._finished_event = asyncio.Event()
        self.audio_control.src = rel_path
        self.audio_control.autoplay = True
        self.audio_control.update()
        await self._finished_event.wait()

    async def _speak_async(self, text: str):
        try:
            rel_path = await asyncio.to_thread(self._generate_audio, text)
            self.audio_control.src = rel_path
            self.audio_control.autoplay = True
            self.audio_control.update()
        except Exception as ex:
            print(f"⚠️ Error generando audio: {ex}")

    def _generate_audio(self, text: str) -> str:
        """Genera el mp3 (o reutiliza uno cacheado) y devuelve la ruta relativa a assets/."""
        key = f"{self.lang}_{text}"
        filename = hashlib.md5(key.encode("utf-8")).hexdigest() + ".mp3"
        filepath = os.path.join(self.output_dir, filename)

        if not os.path.exists(filepath):
            tts = gTTS(text=text, lang=self.lang)
            tts.save(filepath)

        return f"{self.assets_subdir}/{filename}"