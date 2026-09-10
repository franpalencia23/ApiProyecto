from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from core.seguridad import verificar_password, crear_token
from models.schemas import UsuarioLogin
from core.seguridad import hash_password
from core.auth_deps import requiere_admin
from models.schemas import UsuarioCreate, UsuarioResponse

router = APIRouter()


@router.post("/login")
async def login(credenciales: UsuarioLogin, db=Depends(get_db)):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.id_usuarios, u.email, u.password_hash, r.tipo_usuario
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_roles
            WHERE u.email = %s;
            """,
            (credenciales.email,),
        )
        usuario = cursor.fetchone()

    if not usuario or not verificar_password(credenciales.password, usuario["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = crear_token({"sub": usuario["email"], "rol": usuario["tipo_usuario"]})
    return {"access_token": token, "token_type": "bearer", "rol": usuario["tipo_usuario"]}

@router.post("/usuarios", response_model=UsuarioResponse, status_code=201)
async def crear_usuario(data: UsuarioCreate, db=Depends(get_db), admin=Depends(requiere_admin)):
    hash_pw = hash_password(data.password)
    with db.cursor() as cursor:
        cursor.execute(
            """INSERT INTO usuarios (id_rol, email, password_hash)
               VALUES (%s, %s, %s) RETURNING id_usuarios, email, id_rol, creacion;""",
            (data.id_rol, data.email, hash_pw),
        )
        db.commit()
        return cursor.fetchone()