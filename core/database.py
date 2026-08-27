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
            # Neon (plan gratuito) suspende el cómputo tras inactividad y
            # cierra la conexión del lado del servidor sin avisar al
            # cliente. self.connection.closed sigue en 0 porque, desde
            # psycopg2, la conexión "parece" abierta hasta que se intenta
            # usar. Por eso se prueba con un SELECT 1 y, si falla, se
            # reabre la conexión en vez de dejar que la petición reviente.
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