"""
core/influx_client.py

Cliente mínimo para InfluxDB 2.x desde la API FastAPI, usando el endpoint
de compatibilidad InfluxQL (/query) que devuelve JSON simple (no hace
falta la librería oficial influxdb-client, basta con 'requests', que
ya está en tu requirements.txt).

Ubicar este archivo junto a tu core/database.py existente.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "estres_hidrico")


def ultimas_mediciones_mqtt(id_zona: int, limit: int = 10) -> list[dict]:
    """
    Trae las últimas N mediciones de una zona desde la serie que escribe
    Telegraf (medición 'mqtt_consumer', alimentada por el ESP32 vía MQTT).

    Devuelve una lista de dicts: [{"tiempo": "...", "temp": 24.5, "hum": 65}, ...]
    """
    if not INFLUX_TOKEN:
        raise RuntimeError("INFLUX_TOKEN no está configurado en el .env de la API")

    influxql = (
        f"SELECT temp, hum FROM mqtt_consumer "
        f"WHERE id_zona='{id_zona}' ORDER BY time DESC LIMIT {limit}"
    )

    resp = requests.get(
        f"{INFLUX_URL}/query",
        params={"db": INFLUX_BUCKET, "q": influxql},
        headers={"Authorization": f"Token {INFLUX_TOKEN}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    resultados = data.get("results", [])
    if not resultados or "series" not in resultados[0]:
        return []

    serie = resultados[0]["series"][0]
    columnas = serie["columns"]  # ["time", "temp", "hum"]
    filas = serie["values"]

    idx_time = columnas.index("time")
    idx_temp = columnas.index("temp")
    idx_hum = columnas.index("hum")

    return [
        {"tiempo": fila[idx_time], "temp": fila[idx_temp], "hum": fila[idx_hum]}
        for fila in filas
    ]
