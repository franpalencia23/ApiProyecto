from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from core.auth_deps import obtener_usuario_actual, requiere_admin
from models.schemas import ZonaReforestacionCreate, ZonaReforestacionUpdate, ZonaReforestacionResponse

router = APIRouter()

class ZonaReforestacionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("zona_reforestacion", "id_zona", db)

def get_repo(db = Depends(get_db)) -> ZonaReforestacionRepository:
    return ZonaReforestacionRepository(db)

@router.get("/", response_model=list[ZonaReforestacionResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0),
                  repo: ZonaReforestacionRepository = Depends(get_repo),
                  usuario = Depends(obtener_usuario_actual)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_zona}", response_model=ZonaReforestacionResponse)
async def obtener(id_zona: int, repo: ZonaReforestacionRepository = Depends(get_repo),
                   usuario = Depends(obtener_usuario_actual)):
    item = repo.get_by_id(id_zona)
    if not item:
        raise HTTPException(status_code=404, detail="Zona de reforestación no encontrada")
    return item

@router.post("/", response_model=ZonaReforestacionResponse, status_code=201)
async def crear(data: ZonaReforestacionCreate, repo: ZonaReforestacionRepository = Depends(get_repo),
                 usuario = Depends(requiere_admin)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_zona}", response_model=ZonaReforestacionResponse)
async def actualizar(id_zona: int, data: ZonaReforestacionUpdate, repo: ZonaReforestacionRepository = Depends(get_repo),
                      usuario = Depends(requiere_admin)):
    item = repo.update(id_zona, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Zona de reforestación no encontrada")
    return item

@router.delete("/{id_zona}")
async def eliminar(id_zona: int, repo: ZonaReforestacionRepository = Depends(get_repo),
                    usuario = Depends(requiere_admin)):
    repo.delete(id_zona)
    return {"mensaje": "Zona de reforestación eliminada correctamente"}