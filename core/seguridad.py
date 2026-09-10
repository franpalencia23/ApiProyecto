import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

# ---------- Hashing de contraseñas (bcrypt) ----------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Recibe una contraseña en texto plano y devuelve su hash de bcrypt
    (siempre 60 caracteres). Se usa al CREAR un usuario.
    """
    return pwd_context.hash(password)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    """
    Recibe la contraseña en texto plano y el hash guardado, y devuelve
    True si coinciden. Se usa en el login.
    """
    return pwd_context.verify(password_plano, password_hash)


# ---------- Tokens JWT ----------
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def crear_token(datos: dict) -> str:
    """
    Recibe un diccionario (ej. {"sub": "admin@proyecto.org", "rol": "admin"})
    y devuelve un JWT firmado con SECRET_KEY, válido por
    ACCESS_TOKEN_EXPIRE_MINUTES minutos.
    """
    datos_a_codificar = datos.copy()
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    datos_a_codificar.update({"exp": expira})
    return jwt.encode(datos_a_codificar, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> dict | None:
    """
    Recibe un token y, si es válido y no ha expirado, devuelve su
    contenido. Si es inválido o expiró, devuelve None.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None