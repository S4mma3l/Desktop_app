from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Scopes necesarios para Google Fit
SCOPES = ['https://www.googleapis.com/auth/fitness.heart_rate.read']

def authenticate_google_fit():
    """Autentica al usuario en Google Fit sin mostrar el mensaje de URL."""
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES
    )
    
    # Usar 'run_local_server' sin imprimir el enlace de autorización.
    creds = flow.run_local_server(port=0)
    return creds

def get_heart_rate_data(creds):
    """Obtiene datos de frecuencia cardíaca de Google Fit."""
    service = build('fitness', 'v1', credentials=creds)

    # Intervalo de tiempo (últimos 24h)
    now = datetime.utcnow()
    start_time = now - timedelta(days=1)

    # Convertir tiempos a nanosegundos desde la época Unix
    start_time_nanos = int(start_time.timestamp() * 1e9)
    end_time_nanos = int(now.timestamp() * 1e9)

    # Crear datasetId en formato correcto
    dataset_id = f"{start_time_nanos}-{end_time_nanos}"

    # Solicitar datos de frecuencia cardíaca
    try:
        dataset = service.users().dataSources().datasets().get(
            userId="me",
            dataSourceId="derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm",
            datasetId=dataset_id
        ).execute()

        heart_rates = [point["value"][0]["fpVal"] for point in dataset.get("point", [])]

        return heart_rates

    except Exception as e:
        print(f"Error al obtener datos de frecuencia cardíaca: {e}")
        return []

# Autenticación y lectura de datos
credentials = authenticate_google_fit()
heart_rate_data = get_heart_rate_data(credentials)
print("Frecuencia cardíaca (últimos 24h):", heart_rate_data)