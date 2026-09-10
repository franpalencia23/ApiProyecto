from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from core.auth_deps import obtener_usuario_actual, requiere_admin
from models.schemas import AlertaCreate, AlertaUpdate, AlertaResponse

router = APIRouter()

class AlertaRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("alerta", "id_alerta", db)

def get_repo(db = Depends(get_db)) -> AlertaRepository:
    return AlertaRepository(db)

@router.get("/", response_model=list[AlertaResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0),
                  repo: AlertaRepository = Depends(get_repo),
                  usuario = Depends(obtener_usuario_actual)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_alerta}", response_model=AlertaResponse)
async def obtener(id_alerta: int, repo: AlertaRepository = Depends(get_repo),
                   usuario = Depends(obtener_usuario_actual)):
    item = repo.get_by_id(id_alerta)
    if not item:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return item

@router.post("/", response_model=AlertaResponse, status_code=201)
async def crear(data: AlertaCreate, repo: AlertaRepository = Depends(get_repo),
                 usuario = Depends(requiere_admin)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_alerta}", response_model=AlertaResponse)
async def actualizar(id_alerta: int, data: AlertaUpdate, repo: AlertaRepository = Depends(get_repo),
                      usuario = Depends(obtener_usuario_actual)):
    item = repo.update(id_alerta, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return item

@router.delete("/{id_alerta}")
async def eliminar(id_alerta: int, repo: AlertaRepository = Depends(get_repo),
                    usuario = Depends(requiere_admin)):
    repo.delete(id_alerta)
    return {"mensaje": "Alerta eliminada correctamente"}