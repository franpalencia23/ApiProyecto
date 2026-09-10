from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.database import obtener_esquema, ejecutar_sql
from core.ollama_service import generar_sql, es_sql_seguro, redactar_respuesta
from core.auth_deps import obtener_usuario_actual

router = APIRouter()


class Pregunta(BaseModel):
    texto: str


@router.post("/preguntar")
def preguntar(pregunta: Pregunta, usuario=Depends(obtener_usuario_actual)):
    esquema = obtener_esquema()
    sql = generar_sql(pregunta.texto, esquema)

    if not es_sql_seguro(sql):
        return {"error": "Consulta no permitida por seguridad", "sql_generado": sql}

    try:
        columnas, filas = ejecutar_sql(sql)
    except Exception as e:
        return {"error": str(e), "sql_generado": sql}

    respuesta = redactar_respuesta(pregunta.texto, columnas, filas)
    return {"sql": sql, "respuesta": respuesta}