import ollama
import re

MODEL = "llama3.1"


def generar_sql(pregunta: str, esquema: str) -> str:
    prompt = f"""Eres un asistente que traduce preguntas a consultas SQL para PostgreSQL.

Esquema de la base de datos:
{esquema}

Reglas:
- Genera SOLO la consulta SQL, sin explicaciones ni markdown.
- Usa SOLO sentencias SELECT (nunca INSERT, UPDATE, DELETE, DROP).
- Usa los nombres exactos de tablas y columnas del esquema.

Pregunta: {pregunta}

SQL:"""

    respuesta = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    sql = respuesta["message"]["content"].strip()
    # Quita las marcas de bloque de código markdown (```sql ... ```) que
    # algunos modelos agregan aunque se les pida que no lo hagan.
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = sql.replace("```", "").strip()
    return sql


def es_sql_seguro(sql: str) -> bool:
    # Quita un único ";" final (formato normal), antes de revisar.
    # Si después de eso todavía queda un ";" en el texto, es una
    # consulta encadenada (SELECT ...; DROP ...;) y sí se rechaza.
    sql_limpio = sql.strip().rstrip(";").strip()

    prohibido = ["insert", "update", "delete", "drop", "alter", "truncate", "create", ";"]
    sql_lower = sql_limpio.lower()
    return sql_lower.startswith("select") and not any(p in sql_lower for p in prohibido)


def redactar_respuesta(pregunta: str, columnas: list, filas: list) -> str:
    datos_texto = f"Columnas: {columnas}\nFilas: {filas[:20]}"
    prompt = f"""Pregunta original: {pregunta}

Resultado de la consulta SQL:
{datos_texto}

Responde la pregunta de forma clara y en español, basándote solo en estos datos."""

    respuesta = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return respuesta["message"]["content"]