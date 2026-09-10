import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        if self.connection is None or self.connection.closed:
            self._abrir_conexion()
        elif not self._conexion_viva():
            print("⚠️  Conexión inactiva/cerrada por Neon, reconectando...")
            self._abrir_conexion()
        return self.connection

    def _conexion_viva(self) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
            return True
        except Exception:
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False

    def _abrir_conexion(self):
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("❌ DATABASE_URL no está configurada en .env")
        try:
            self.connection = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            print("✅ Conexión a Neon establecida exitosamente")
        except Exception as e:
            print(f"❌ Error al conectar a Neon: {e}")
            raise e


def get_db():
    db = Database()
    return db.connect()


# ============================================================
# Funciones para el asistente de IA (esquema + ejecución de SQL)
# ============================================================
TABLAS_EXCLUIDAS = {"usuarios", "roles"}  # nombres reales de tus tablas de auth


def obtener_esquema() -> str:
    """Devuelve un texto con la estructura de las tablas (nombre + columnas
    + tipo), para dárselo al LLM como contexto y que sepa contra qué
    puede escribir SQL. Excluye las tablas de autenticación a propósito."""
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


def ejecutar_sql(sql: str):
    """Ejecuta un SELECT y devuelve (columnas, filas) — las dos cosas,
    porque routers/preguntas.py hace 'columnas, filas = ejecutar_sql(sql)'."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql)
        columnas = [desc[0] for desc in cur.description]
        filas = cur.fetchall()
    return columnas, filas