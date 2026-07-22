import asyncio
import flet as ft
from typing import Callable, Optional

class SpeechRecognizer:
    """
    Módulo independiente para reconocimiento de voz.
    Compatible con PWA y diferentes versiones de Flet.
    """
    
    def __init__(self, lang: str = "es"):
        self.lang = "es-ES" if lang == "es" else "en-US"
        self.page: Optional[ft.Page] = None
        self.is_listening = False
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_end: Optional[Callable[[], None]] = None

    def set_page(self, page: ft.Page):
        """Inyecta la página de Flet."""
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
        if e.data == "completed":
            self._finished_event.set()
    async def speak_and_wait(self, text: str):
    #"""Genera y reproduce el audio, esperando a que termine antes de continuar."""
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
    def start_listening(self, on_result: Callable[[str], None], 
                       on_error: Optional[Callable[[str], None]] = None,
                       on_start: Optional[Callable[[], None]] = None,
                       on_end: Optional[Callable[[], None]] = None):
        """
        Inicia el reconocimiento de voz.
        
        Args:
            on_result: Callback que recibe el texto reconocido
            on_error: Callback que recibe el error (opcional)
            on_start: Callback cuando empieza a escuchar (opcional)
            on_end: Callback cuando termina de escuchar (opcional)
        """
        if self.is_listening or not self.page:
            return
        
        self.is_listening = True
        self.on_result = on_result
        self.on_error = on_error
        self.on_start = on_start
        self.on_end = on_end
        
        if on_start:
            on_start()
        
        # Crear ID único para este input
        import uuid
        input_id = str(uuid.uuid4())
        
        # Crear campo oculto para recibir el resultado
        hidden_input = ft.TextField(
            visible=False,
            data={"speech_id": input_id},
            on_change=lambda e: self._handle_result(e.control.value)
        )
        self.page.overlay.append(hidden_input)
        self.page.update()
        
        # JavaScript para SpeechRecognition
        js_code = f"""
        (function() {{
            // Verificar soporte
            if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {{
                console.error('Speech Recognition no soportado en este navegador');
                window.dispatchEvent(new CustomEvent('speech-error-{{input_id}}', {{
                    detail: {{ error: 'not_supported' }}
                }}));
                return;
            }}
            
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = '{self.lang}';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            recognition.continuous = false;
            
            recognition.onstart = function() {{
                console.log('Escuchando...');
            }};
            
            recognition.onresult = function(event) {{
                const transcript = event.results[0][0].transcript;
                console.log('Reconocido:', transcript);
                
                // Buscar el input oculto y actualizarlo
                const inputs = document.querySelectorAll('input');
                for (let input of inputs) {{
                    if (input.getAttribute('data-flet-id') && 
                        input.parentElement.querySelector('[data-speech-id=\"{{input_id}}\"]')) {{
                        input.value = transcript;
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        break;
                    }}
                }}
            }};
            
            recognition.onerror = function(event) {{
                console.error('Error de reconocimiento:', event.error);
                window.dispatchEvent(new CustomEvent('speech-error-{{input_id}}', {{
                    detail: {{ error: event.error }}
                }}));
            }};
            
            recognition.onend = function() {{
                console.log('Reconocimiento terminado');
                window.dispatchEvent(new CustomEvent('speech-end-{{input_id}}'));
            }};
            
            // Iniciar
            try {{
                recognition.start();
            }} catch (e) {{
                console.error('No se pudo iniciar:', e);
            }}
        }})();
        """
        
        # Ejecutar JavaScript compatible con todas las versiones
        #asyncio.create_task(self._execute_js(js_code))  ANTES
        self.page.run_task(self._execute_js, js_code)


    def stop_listening(self):
        """Detiene el reconocimiento de voz."""
        if not self.is_listening:
            return
        
        js_code = """
        if (window.recognitionInstance) {
            window.recognitionInstance.stop();
        }
        """
        #asyncio.create_task(self._execute_js(js_code))  ---ANTES
        self.page.run_task(self._execute_js, js_code)
        self.is_listening = False
        
        if self.on_end:
            self.on_end()

    def _handle_result(self, text: str):
        """Procesa el resultado del reconocimiento."""
        self.is_listening = False
        
        # Limpiar el input oculto
        if self.page:
            self.page.overlay.clear()
            self.page.update()
        
        if self.on_result:
            self.on_result(text)
        
        if self.on_end:
            self.on_end()

    async def _execute_js(self, js_code: str):
        """Ejecuta JavaScript compatible con Flet 0.21-0.26+."""
        if not self.page:
            return
        
        try:
            # Flet 0.26+
            await self.page.run_js(js_code)
        except AttributeError:
            try:
                # Flet 0.21-0.25
                self.page.evaluate(js_code)
            except AttributeError:
                print("⚠️ No se pudo ejecutar JavaScript")
                if self.on_error:
                    self.on_error("javascript_not_supported")

    def check_browser_support(self) -> bool:
        """Verifica si el navegador soporta Speech Recognition."""
        # Esto se verifica del lado del cliente con JavaScript
        return True  # Asumimos que sí, el JS lo verificará


# Función helper para convertir texto a número
def text_to_number(text: str, lang: str = "es") -> int | None:
    """
    Convierte texto hablado a número.
    Ej: "cuatro" -> 4, "veinticinco" -> 25
    """
    text = text.lower().strip()
    
    # Buscar dígitos directamente
    import re
    digit_match = re.search(r'\d+', text)
    if digit_match:
        return int(digit_match.group())
    
    # Diccionarios
    words_es = {
        "cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, 
        "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, 
        "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, 
        "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, 
        "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintidos": 22, 
        "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, 
        "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, 
        "veintinueve": 29, "treinta": 30
    }
    
    words_en = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, 
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, 
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, 
        "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, 
        "eighteen": 18, "nineteen": 19, "twenty": 20, 
        "twenty-one": 21, "twenty-two": 22, "twenty-three": 23, 
        "twenty-four": 24, "twenty-five": 25, "twenty-six": 26, 
        "twenty-seven": 27, "twenty-eight": 28, "twenty-nine": 29, 
        "thirty": 30
    }
    
    dictionary = words_es if lang == "es" else words_en
    clean_text = re.sub(r'[^\w\s]', '', text)
    
    for word, num in dictionary.items():
        if word in clean_text:
            return num
    
    return None