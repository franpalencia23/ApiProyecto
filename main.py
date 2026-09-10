from fastapi import FastAPI
from routers import auth
from routers import preguntas
from routers import (
    region, especie_vegetal, zona_reforestacion, 
    tipo_sensor, sensor, personal, medicion, 
    tipo_alerta, alerta, tratamiento,preguntas
)

app = FastAPI(
    title="API — Monitoreo de Estrés Hídrico en Zonas de Reforestación",
    description="API REST completa con FastAPI + Neón",
    version="1.0.0"
)

# Rutas con versión v1 según la documentación
app.include_router(region.router, prefix="/api/v1/regiones", tags=["Regiones"])
app.include_router(especie_vegetal.router, prefix="/api/v1/especies", tags=["Especies Vegetales"])
app.include_router(zona_reforestacion.router, prefix="/api/v1/zonas", tags=["Zonas Reforestación"])
app.include_router(tipo_sensor.router, prefix="/api/v1/tipos-sensor", tags=["Tipos de Sensor"])
app.include_router(sensor.router, prefix="/api/v1/sensores", tags=["Sensores"])
app.include_router(personal.router, prefix="/api/v1/personal", tags=["Personal"])
app.include_router(medicion.router, prefix="/api/v1/mediciones", tags=["Mediciones"])
app.include_router(tipo_alerta.router, prefix="/api/v1/tipos-alerta", tags=["Tipos de Alerta"])
app.include_router(alerta.router, prefix="/api/v1/alertas", tags=["Alertas"])
app.include_router(tratamiento.router, prefix="/api/v1/tratamientos", tags=["Tratamientos"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(preguntas.router, prefix="/api/v1/ia", tags=["Asistente IA"])
@app.get("/", tags=["Inicio"])
def home():
    return {"mensaje": "API de Estrés Hídrico funcionando correctamente"}