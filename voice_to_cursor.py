import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
from dotenv import load_dotenv
import openai
import pyperclip
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

class VoiceRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Grabador de Voz para Cursor")
        self.root.geometry("300x150")
        
        # Verificar API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            messagebox.showerror("Error", "No se encontró la API key de OpenAI. Por favor, configura OPENAI_API_KEY en el archivo .env")
            self.root.destroy()
            return
            
        self.recording = False
        self.audio_data = []
        self.sample_rate = 44100
        
        # Configurar el botón
        self.button = tk.Button(
            self.root,
            text="Iniciar Grabación",
            command=self.toggle_recording,
            width=20,
            height=2
        )
        self.button.pack(pady=20)
        
        # Configurar OpenAI
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.recording = True
        self.button.config(text="Detener Grabación")
        self.audio_data = []
        
        def callback(indata, frames, time, status):
            if status:
                print(status)
            self.audio_data.extend(indata[:, 0])
        
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            callback=callback
        )
        self.stream.start()
    
    def stop_recording(self):
        self.recording = False
        self.button.config(text="Iniciar Grabación")
        self.stream.stop()
        self.stream.close()
        
        # Guardar el archivo de audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        wav.write(filename, self.sample_rate, np.array(self.audio_data))
        
        # Procesar el audio
        self.process_audio(filename)
    
    def process_audio(self, audio_file):
        try:
            # Transcribir el audio
            with open(audio_file, "rb") as file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file
                )
            
            # Crear el prompt para pulir el texto
            prompt = f"Por favor, pulir y mejorar el siguiente texto para usarlo como prompt en Cursor: {transcript.text}"
            
            # Obtener la respuesta de la IA
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente que ayuda a pulir y mejorar textos para usarlos como prompts en Cursor."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Limpiar el texto antes de copiarlo
            polished_text = response.choices[0].message.content
            # Eliminar la introducción común
            if "Claro, aquí tienes una versión mejorada del texto para tu prompt en Cursor:" in polished_text:
                polished_text = polished_text.split("Claro, aquí tienes una versión mejorada del texto para tu prompt en Cursor:")[1].strip()
            # Eliminar comillas si existen
            polished_text = polished_text.strip('"').strip("'")
            
            # Copiar al portapapeles
            pyperclip.copy(polished_text)
            
            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "El texto pulido ha sido copiado al portapapeles.")
            
            # Eliminar el archivo de audio
            os.remove(audio_file)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el audio: {str(e)}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VoiceRecorder()
    app.run() 