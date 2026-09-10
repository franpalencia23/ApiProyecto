from core.database import get_db

TABLAS_EXCLUIDAS = {"usuario", "rol"}  # ajusta según qué tablas quieras ocultar

def obtener_esquema():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        filas = cur.fetchall()

    esquema = {}
    for fila in filas:
        tabla = fila["table_name"]
        if tabla in TABLAS_EXCLUIDAS:
            continue
        columna = fila["column_name"]
        tipo = fila["data_type"]
        esquema.setdefault(tabla, []).append(f"{columna} ({tipo})")

    texto = ""
    for tabla, columnas in esquema.items():
        texto += f"Tabla {tabla}: {', '.join(columnas)}\n"
    return texto

def ejecutar_sql(sql):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql)
        filas = cur.fetchall()
    return filas