"""routers/estadisticas.py
Consultas SQL complejas sobre la tabla 'medicion' (Punto 1 del parcial).

Las usan tres clientes distintos:
  - el ESP32 (menu del teclado matricial)  -> se autentica con X-API-Key
  - la app movil (tablero de graficos)      -> se autentica con JWT
  - el bot de Telegram                      -> se autentica con JWT

Todas las consultas son SELECT con parametros (%s): nunca se concatena
texto del usuario dentro del SQL.

Sobre las ventanas de tiempo ("ultimas 24 horas", etc.): por defecto se
calculan respecto al ULTIMO dato registrado y no respecto a la hora
actual. Asi, si el ESP32 esta apagado, la consulta sigue devolviendo
datos en vez de una lista vacia. Con ?desde_ahora=true se usa NOW().
"""
from typing import Literal, Optional
from datetime import date

from fastapi import APIRouter, Depends, Query

from core.database import get_db
from core.auth_deps import acceso_usuario_o_dispositivo

router = APIRouter()

TipoMedicion = Literal["temperatura_suelo", "humedad_suelo"]

# Fragmentos SQL fijos (no vienen del usuario) para elegir el "ahora".
_ANCLA_ULTIMO_DATO = "(SELECT COALESCE(MAX(fecha_hora), NOW()) FROM medicion)"
_ANCLA_AHORA = "NOW()"


def _ancla(desde_ahora: bool) -> str:
    return _ANCLA_AHORA if desde_ahora else _ANCLA_ULTIMO_DATO


def _consultar(db, sql: str, params: tuple) -> list[dict]:
    """Ejecuta un SELECT y devuelve la lista de filas.

    Los endpoints son 'async def' igual que los demas routers: la conexion
    a Neon es una sola compartida, y asi las peticiones se atienden una a
    una en vez de en hilos paralelos que se pisarian la transaccion.

    La conexion es compartida (singleton) y no esta en autocommit: si una
    consulta falla, hay que hacer rollback o la conexion queda inutilizable
    para el resto de peticiones. Si funciona, se cierra la transaccion de
    lectura con commit para no dejarla abierta.
    """
    try:
        with db.cursor() as cur:
            cur.execute(sql, params)
            filas = cur.fetchall()
        db.commit()
        return filas
    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------------------
# 1. Promedio por hora (GROUP BY + date_trunc)            -> menu: opcion 5
# ---------------------------------------------------------------------
@router.get("/promedio-por-hora")
async def promedio_por_hora(
    tipo: TipoMedicion = "humedad_suelo",
    horas: int = Query(24, ge=1, le=720),
    id_zona: Optional[int] = None,
    desde_ahora: bool = False,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    sql = f"""
        SELECT date_trunc('hour', fecha_hora)        AS hora,
               ROUND(AVG(valor)::numeric, 2)         AS promedio,
               MIN(valor)                            AS minimo,
               MAX(valor)                            AS maximo,
               COUNT(*)                              AS registros
        FROM medicion
        WHERE tipo_medicion = %s
          AND (%s::int IS NULL OR id_zona = %s)
          AND fecha_hora >= {_ancla(desde_ahora)} - make_interval(hours => %s)
        GROUP BY date_trunc('hour', fecha_hora)
        ORDER BY hora;
    """
    return _consultar(db, sql, (tipo, id_zona, id_zona, horas))


# ---------------------------------------------------------------------
# 2. Maximo y minimo del dia, por tipo de medicion        -> menu: opcion 4
# ---------------------------------------------------------------------
@router.get("/resumen-dia")
async def resumen_dia(
    fecha: Optional[date] = None,
    id_zona: Optional[int] = None,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    # Sin fecha: usa el dia del ultimo dato registrado.
    sql = """
        WITH dia AS (
            SELECT COALESCE(%s::date,
                            (SELECT DATE(MAX(fecha_hora)) FROM medicion)) AS d
        )
        SELECT dia.d                              AS fecha,
               m.tipo_medicion,
               MAX(m.valor)                       AS maximo,
               MIN(m.valor)                       AS minimo,
               ROUND(AVG(m.valor)::numeric, 2)    AS promedio,
               COUNT(*)                           AS registros
        FROM medicion m
        CROSS JOIN dia
        WHERE DATE(m.fecha_hora) = dia.d
          AND (%s::int IS NULL OR m.id_zona = %s)
        GROUP BY dia.d, m.tipo_medicion
        ORDER BY m.tipo_medicion;
    """
    return _consultar(db, sql, (fecha, id_zona, id_zona))


# ---------------------------------------------------------------------
# 3. Registros por dia con HAVING                         -> menu: opcion 6
# ---------------------------------------------------------------------
@router.get("/registros-por-dia")
async def registros_por_dia(
    min_registros: int = Query(1, ge=1),
    dias: int = Query(15, ge=1, le=365),
    id_zona: Optional[int] = None,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    sql = """
        SELECT DATE(fecha_hora)                                   AS dia,
               COUNT(*)                                           AS registros,
               ROUND(AVG(valor) FILTER (WHERE tipo_medicion = 'temperatura_suelo')::numeric, 2)
                                                                  AS temp_promedio,
               ROUND(AVG(valor) FILTER (WHERE tipo_medicion = 'humedad_suelo')::numeric, 2)
                                                                  AS hum_promedio
        FROM medicion
        WHERE (%s::int IS NULL OR id_zona = %s)
        GROUP BY DATE(fecha_hora)
        HAVING COUNT(*) >= %s
        ORDER BY dia DESC
        LIMIT %s;
    """
    return _consultar(db, sql, (id_zona, id_zona, min_registros, dias))


# ---------------------------------------------------------------------
# 4. Zonas por encima del promedio general (subconsulta)  -> menu: opcion 7
# ---------------------------------------------------------------------
@router.get("/zonas-sobre-promedio")
async def zonas_sobre_promedio(
    tipo: TipoMedicion = "humedad_suelo",
    solo_sobre_promedio: bool = True,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    # Con solo_sobre_promedio=false devuelve TODAS las zonas (util para el
    # grafico de barras de la app cuando hay pocas zonas con datos).
    sql = """
        SELECT z.id_zona,
               z.nombre_zona,
               ROUND(AVG(m.valor)::numeric, 2)  AS promedio_zona,
               COUNT(*)                         AS registros,
               (SELECT ROUND(AVG(valor)::numeric, 2)
                  FROM medicion WHERE tipo_medicion = %s) AS promedio_general
        FROM medicion m
        JOIN zona_reforestacion z ON z.id_zona = m.id_zona
        WHERE m.tipo_medicion = %s
        GROUP BY z.id_zona, z.nombre_zona
        HAVING (NOT %s)
            OR AVG(m.valor) > (SELECT AVG(valor) FROM medicion WHERE tipo_medicion = %s)
        ORDER BY promedio_zona DESC;
    """
    return _consultar(db, sql, (tipo, tipo, solo_sobre_promedio, tipo))


# ---------------------------------------------------------------------
# 5. Promedio de las ultimas 24 horas                     -> menu: opcion 3
# ---------------------------------------------------------------------
@router.get("/promedio-24h")
async def promedio_24h(
    id_zona: Optional[int] = None,
    desde_ahora: bool = False,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    sql = f"""
        SELECT tipo_medicion,
               ROUND(AVG(valor)::numeric, 2) AS promedio,
               COUNT(*)                      AS registros,
               MIN(fecha_hora)               AS desde,
               MAX(fecha_hora)               AS hasta
        FROM medicion
        WHERE fecha_hora >= {_ancla(desde_ahora)} - INTERVAL '24 hours'
          AND (%s::int IS NULL OR id_zona = %s)
        GROUP BY tipo_medicion
        ORDER BY tipo_medicion;
    """
    return _consultar(db, sql, (id_zona, id_zona))


# ---------------------------------------------------------------------
# 6. Desviacion estandar de la muestra (ultimas N)        -> menu: opcion 9
# ---------------------------------------------------------------------
@router.get("/desviacion")
async def desviacion(
    muestras: int = Query(100, ge=2, le=5000),
    id_zona: Optional[int] = None,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    # ROW_NUMBER toma las ultimas N muestras de CADA tipo de medicion.
    sql = """
        SELECT tipo_medicion,
               COUNT(*)                               AS muestras,
               ROUND(AVG(valor)::numeric, 2)          AS promedio,
               ROUND(STDDEV_SAMP(valor)::numeric, 2)  AS desviacion_estandar,
               ROUND(VARIANCE(valor)::numeric, 2)     AS varianza,
               MIN(valor)                             AS minimo,
               MAX(valor)                             AS maximo
        FROM (
            SELECT tipo_medicion, valor,
                   ROW_NUMBER() OVER (PARTITION BY tipo_medicion
                                      ORDER BY fecha_hora DESC) AS n
            FROM medicion
            WHERE (%s::int IS NULL OR id_zona = %s)
        ) ult
        WHERE n <= %s
        GROUP BY tipo_medicion
        ORDER BY tipo_medicion;
    """
    return _consultar(db, sql, (id_zona, id_zona, muestras))


# ---------------------------------------------------------------------
# 7. Ultimo registro guardado de cada tipo                -> menu: opcion 2
# ---------------------------------------------------------------------
@router.get("/ultimo-registro")
async def ultimo_registro(
    id_zona: Optional[int] = None,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    sql = """
        SELECT DISTINCT ON (tipo_medicion)
               tipo_medicion, valor, unidad, id_zona, fecha_hora
        FROM medicion
        WHERE (%s::int IS NULL OR id_zona = %s)
        ORDER BY tipo_medicion, fecha_hora DESC;
    """
    return _consultar(db, sql, (id_zona, id_zona))


# ---------------------------------------------------------------------
# 8. Distribucion por estado (grafico de pastel de la app)
# ---------------------------------------------------------------------
# Une temperatura y humedad del mismo minuto y las clasifica con los
# mismos umbrales que los LEDs del ESP32, separando 'critico' de 'estres'.
@router.get("/distribucion-estados")
async def distribucion_estados(
    id_zona: Optional[int] = None,
    db=Depends(get_db),
    _=Depends(acceso_usuario_o_dispositivo),
):
    sql = """
        WITH pares AS (
            SELECT date_trunc('minute', fecha_hora) AS minuto,
                   AVG(valor) FILTER (WHERE tipo_medicion = 'temperatura_suelo') AS temp,
                   AVG(valor) FILTER (WHERE tipo_medicion = 'humedad_suelo')     AS hum
            FROM medicion
            WHERE (%s::int IS NULL OR id_zona = %s)
            GROUP BY id_zona, date_trunc('minute', fecha_hora)
        ),
        clasificados AS (
            SELECT CASE
                     WHEN hum < 15 OR temp > 40 THEN 'critico'
                     WHEN hum < 30 OR temp > 35 THEN 'estres'
                     WHEN hum < 50 OR temp > 28 THEN 'precaucion'
                     ELSE 'optimo'
                   END AS estado
            FROM pares
            WHERE temp IS NOT NULL AND hum IS NOT NULL
        )
        SELECT estado,
               COUNT(*)                                                  AS muestras,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)        AS porcentaje
        FROM clasificados
        GROUP BY estado
        ORDER BY muestras DESC;
    """
    return _consultar(db, sql, (id_zona, id_zona))