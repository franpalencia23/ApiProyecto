# test_db.py
from core.database import get_db

try:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ Conectado exitosamente a Neon!")
    print(f"📦 Versión de PostgreSQL: {version[0]}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")