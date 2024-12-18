import random
import tkinter as tk
from tkinter import ttk
from transformers import pipeline

# Simulación de datos biométricos
def simulate_biometrics():
    heart_rate = random.randint(50, 120)  # Frecuencia cardíaca
    variability = random.uniform(20, 80)  # Variabilidad cardíaca
    return heart_rate, variability

# Análisis del estado emocional basado en datos biométricos
def analyze_emotion(heart_rate, variability):
    if heart_rate < 60 and variability > 60:
        return "Relajado"
    elif heart_rate > 100 or variability < 30:
        return "Estresado"
    else:
        return "Neutral"

# Generación de texto motivador
text_generator = pipeline("text-generation", model="gpt2")
def generate_text(emotion):
    prompts = {
        "Relajado": "Es un gran momento para disfrutar la calma. Recuerda que cada respiro cuenta.",
        "Estresado": "Aunque el día sea desafiante, tienes la fuerza para superarlo. ",
        "Neutral": "Hoy es una gran oportunidad para ser tu mejor versión. ",
    }
    prompt = prompts.get(emotion, "Siempre hay algo positivo que descubrir.")
    return text_generator(prompt, max_length=50, num_return_sequences=1)[0]['generated_text']

# GUI usando Tkinter
def update_interface():
    heart_rate, variability = simulate_biometrics()
    heart_rate_label["text"] = f"Frecuencia Cardíaca: {heart_rate} bpm"
    variability_label["text"] = f"Variabilidad Cardíaca: {variability:.2f} ms"

    emotion = analyze_emotion(heart_rate, variability)
    emotion_label["text"] = f"Estado Emocional: {emotion}"

    generated_text = generate_text(emotion)
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, generated_text)

# Configuración de la ventana principal
app = tk.Tk()
app.title("Analizador de Estado Emocional")
app.geometry("500x400")

frame = ttk.Frame(app, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Etiquetas para mostrar datos biométricos
heart_rate_label = ttk.Label(frame, text="Frecuencia Cardíaca: - bpm")
heart_rate_label.grid(row=0, column=0, sticky=tk.W)

variability_label = ttk.Label(frame, text="Variabilidad Cardíaca: - ms")
variability_label.grid(row=1, column=0, sticky=tk.W)

emotion_label = ttk.Label(frame, text="Estado Emocional: -")
emotion_label.grid(row=2, column=0, sticky=tk.W)

# Botón para actualizar datos
update_button = ttk.Button(frame, text="Actualizar", command=update_interface)
update_button.grid(row=3, column=0, pady=10)

# Área de texto para mostrar salida generada
text_output = tk.Text(frame, wrap=tk.WORD, height=10, width=50)
text_output.grid(row=4, column=0, pady=10)

# Inicio de la aplicación
app.mainloop()