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
            try:
                # Usar variable de entorno
                DATABASE_URL = os.getenv("DATABASE_URL")
                
                if not DATABASE_URL:
                    raise ValueError("❌ DATABASE_URL no está configurada en .env")
                
                self.connection = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
                print("✅ Conexión a Neon establecida exitosamente")
                return self.connection
            except Exception as e:
                print(f"❌ Error al conectar a Neon: {e}")
                raise e
        return self.connection

def get_db():
    db = Database()
    return db.connect()