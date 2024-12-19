import customtkinter as ctk
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import os

# Configuración inicial de customtkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Scopes necesarios para Google Fit
SCOPES = ['https://www.googleapis.com/auth/fitness.heart_rate.read']

# Archivo CSV para almacenar los datos
DATA_FILE = "heart_rate_data.csv"

# Función para autenticar con Google Fit
def authenticate_google_fit():
    """Autentica al usuario en Google Fit."""
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES
    )
    creds = flow.run_local_server(port=0)
    return creds

# Obtener datos de frecuencia cardíaca desde Google Fit
def get_last_24_hours_heart_rate_data(creds):
    """Obtiene datos de frecuencia cardíaca de las últimas 24 horas desde Google Fit."""
    service = build('fitness', 'v1', credentials=creds)
    now = datetime.utcnow()
    start_time = now - timedelta(days=1)
    start_time_nanos = int(start_time.timestamp() * 1e9)
    end_time_nanos = int(now.timestamp() * 1e9)
    dataset_id = f"{start_time_nanos}-{end_time_nanos}"

    # Listar las fuentes de datos disponibles
    data_sources = service.users().dataSources().list(userId="me").execute()
    heart_rate_source = None

    for source in data_sources.get("dataSource", []):
        if "heart_rate" in source.get("dataStreamId", "").lower():
            heart_rate_source = source["dataStreamId"]
            print(f"Fuente de frecuencia cardíaca encontrada: {heart_rate_source}")
            break

    if not heart_rate_source:
        print("No se encontró ninguna fuente de frecuencia cardíaca.")
        return []

    # Obtener datos de frecuencia cardíaca de la fuente encontrada
    try:
        dataset = service.users().dataSources().datasets().get(
            userId="me",
            dataSourceId=heart_rate_source,
            datasetId=dataset_id
        ).execute()

        heart_rates = [point["value"][0]["fpVal"] for point in dataset.get("point", [])]
        if not heart_rates:
            print("No se encontraron datos de frecuencia cardíaca en el rango de tiempo especificado.")
        return heart_rates

    except Exception as e:
        print(f"Error al obtener datos de frecuencia cardíaca: {e}")
        return []

# Guardar datos en archivo CSV
def save_data_to_csv(heart_rates):
    """Guarda los datos de frecuencia cardíaca en un archivo CSV."""
    now = datetime.now()
    data = pd.DataFrame({
        "timestamp": [now] * len(heart_rates),
        "heart_rate": heart_rates
    })
    if os.path.exists(DATA_FILE):
        data.to_csv(DATA_FILE, mode='a', header=False, index=False)
    else:
        data.to_csv(DATA_FILE, mode='w', index=False)

# Cargar datos históricos desde CSV
def load_data_from_csv():
    """Carga los datos de frecuencia cardíaca desde el archivo CSV."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["timestamp", "heart_rate"])

# Red neuronal para sugerencias de salud
class HealthNet(nn.Module):
    def __init__(self):
        super(HealthNet, self).__init__()
        self.fc1 = nn.Linear(1, 10)
        self.fc2 = nn.Linear(10, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return self.fc2(x)

# Entrenar la red neuronal
def train_health_net(data):
    """Entrena la red neuronal con los datos históricos."""
    if data.empty:
        return None

    # Preparar datos
    x = torch.tensor(data["heart_rate"].values, dtype=torch.float32).unsqueeze(1)
    y = torch.tensor(data["heart_rate"].shift(-1).fillna(data["heart_rate"].iloc[-1]).values, dtype=torch.float32).unsqueeze(1)

    # Modelo y configuración de entrenamiento
    model = HealthNet()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # Entrenamiento
    for epoch in range(100):
        optimizer.zero_grad()
        output = model(x)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()

    return model

# Generar sugerencias de salud
def generate_health_suggestions(model, avg_heart_rate):
    """Genera sugerencias de salud basadas en la red neuronal."""
    if model is None:
        return "No hay suficientes datos para generar sugerencias."
    
    input_data = torch.tensor([[avg_heart_rate]], dtype=torch.float32)
    predicted = model(input_data).item()

    if predicted > 90:
        return "Recomendación: Considera hacer ejercicios de relajación o reducir el estrés."
    elif predicted < 60:
        return "Recomendación: Mantén una dieta equilibrada y consulta a un médico si persiste."
    else:
        return "Tu salud parece estar en buen estado. ¡Sigue así!"

# Función para graficar datos de frecuencia cardíaca
def plot_heart_rate(heart_rates):
    """Crea una gráfica de los datos de frecuencia cardíaca."""
    figure = Figure(figsize=(6, 4), dpi=100)
    subplot = figure.add_subplot(111)
    subplot.plot(heart_rates, marker='o', linestyle='-', color='b')
    subplot.set_title("Frecuencia Cardíaca - Últimas 24 horas")
    subplot.set_xlabel("Muestras")
    subplot.set_ylabel("Frecuencia Cardíaca (bpm)")
    subplot.grid(True)
    return figure

# Interfaz gráfica
def update_interface():
    """Actualiza la gráfica y los datos biométricos en la interfaz."""
    heart_rates = get_last_24_hours_heart_rate_data(credentials)
    if heart_rates:
        save_data_to_csv(heart_rates)
        avg_heart_rate = sum(heart_rates) / len(heart_rates)
        heart_rate_label.configure(text=f"Frecuencia Cardíaca Promedio: {avg_heart_rate:.2f} bpm")

        # Actualizar gráfica
        for widget in graph_frame.winfo_children():
            widget.destroy()

        figure = plot_heart_rate(heart_rates)
        canvas = FigureCanvasTkAgg(figure, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        # Generar sugerencias
        historical_data = load_data_from_csv()
        model = train_health_net(historical_data)
        suggestion = generate_health_suggestions(model, avg_heart_rate)
        suggestions_label.configure(text=suggestion)
    else:
        heart_rate_label.configure(text="Frecuencia Cardíaca: Sin datos")

# Configuración de la ventana principal
app = ctk.CTk()
app.title("Analizador de Estado Emocional")
app.geometry("800x600")

frame = ctk.CTkFrame(app, corner_radius=15)
frame.pack(pady=20, padx=20, fill="both", expand=True)

heart_rate_label = ctk.CTkLabel(frame, text="Frecuencia Cardíaca: - bpm", font=("Arial", 16))
heart_rate_label.pack(pady=10)

graph_frame = ctk.CTkFrame(frame, corner_radius=15)
graph_frame.pack(pady=10, padx=10, fill="both", expand=True)

suggestions_label = ctk.CTkLabel(frame, text="Sugerencias: -", font=("Arial", 14))
suggestions_label.pack(pady=10)

update_button = ctk.CTkButton(frame, text="Actualizar", command=update_interface, corner_radius=8)
update_button.pack(pady=20)

credentials = authenticate_google_fit()
app.mainloop()