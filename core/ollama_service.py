import ollama
import re

MODEL = "llama3.1"

def generar_sql(pregunta, esquema):
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
    sql = re.sub(r"sql|", "", sql).strip()
    return sql

def es_sql_seguro(sql):
    prohibido = ["insert", "update", "delete", "drop", "alter", "truncate", "create"]
    sql_lower = sql.lower()
    return sql.lower().startswith("select") and not any(p in sql_lower for p in prohibido)

def redactar_respuesta(pregunta, columnas, filas):
    datos_texto = f"Columnas: {columnas}\nFilas: {filas[:20]}"
    prompt = f"""Pregunta original: {pregunta}

Resultado de la consulta SQL:
{datos_texto}

Responde la pregunta de forma clara y en español, basándote solo en estos datos."""

    respuesta = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return respuesta["message"]["content"]