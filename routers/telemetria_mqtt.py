"""
routers/telemetria_mqtt.py

Nuevo endpoint de la API: expone las mediciones que llegan por el canal
MQTT (ESP32 -> Mosquitto -> Telegraf -> InfluxDB). Sigue el mismo patrón
de autenticación que el resto de tus routers (Bearer token), para que la
app Java MDI consuma esto en vez de hablar con InfluxDB directamente.

Registrar en tu app principal (donde haces los app.include_router(...)
de los demás routers), por ejemplo:

    from routers import telemetria_mqtt
    app.include_router(
        telemetria_mqtt.router,
        prefix="/api/v1/telemetria",
        tags=["telemetria-mqtt"],
    )
"""
from fastapi import APIRouter, Depends, HTTPException

from core.auth_deps import obtener_usuario_actual
from core.influx_client import ultimas_mediciones_mqtt

router = APIRouter()


@router.get("/mqtt/ultimas")
def obtener_ultimas_mqtt(zona: int, limit: int = 10, usuario=Depends(obtener_usuario_actual)):
    """
    GET /api/v1/telemetria/mqtt/ultimas?zona=1&limit=10

    Devuelve las últimas N mediciones de una zona, leídas de InfluxDB
    (alimentado por Telegraf, que a su vez escucha el broker Mosquitto).
    """
    try:
        return ultimas_mediciones_mqtt(id_zona=zona, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo consultar InfluxDB: {exc}")
