from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from fastapi import Header, HTTPException, status

from core.seguridad import verificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
SENSOR_API_KEY = os.getenv("SENSOR_API_KEY")

def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> dict:
    """Lee el header Authorization: Bearer <token>, lo verifica, y
    devuelve su contenido ({"sub": email, "rol": "admin"/"usuario"}).
    Si el token es inválido o expiró, corta la petición con 401."""
    datos = verificar_token(token)
    if datos is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return datos


def requiere_admin(usuario: dict = Depends(obtener_usuario_actual)) -> dict:
    """Se apoya en obtener_usuario_actual y además exige rol admin."""
    if usuario.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere rol de administrador",
        )
    return usuario

def verificar_api_key_sensor(x_api_key: str = Header(...)):
    """
    Protección simple para el endpoint que alimentan los sensores
    automáticos (no personas). En vez de pedir login con usuario y
    contraseña (que no tiene sentido para un dispositivo), solo exige
    que el header 'X-API-Key' coincida con la clave secreta del .env.
    """
    if not SENSOR_API_KEY or x_api_key != SENSOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key de sensor inválida",
        )
    return True