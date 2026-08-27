from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from models.schemas import TipoAlertaCreate, TipoAlertaUpdate, TipoAlertaResponse

router = APIRouter()

class TipoAlertaRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("tipo_alerta", "id_tipo_alerta", db)

def get_repo(db = Depends(get_db)) -> TipoAlertaRepository:
    return TipoAlertaRepository(db)

@router.get("/", response_model=list[TipoAlertaResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), repo: TipoAlertaRepository = Depends(get_repo)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_tipo_alerta}", response_model=TipoAlertaResponse)
async def obtener(id_tipo_alerta: int, repo: TipoAlertaRepository = Depends(get_repo)):
    item = repo.get_by_id(id_tipo_alerta)
    if not item:
        raise HTTPException(status_code=404, detail="Tipo de alerta no encontrado")
    return item

@router.post("/", response_model=TipoAlertaResponse, status_code=201)
async def crear(data: TipoAlertaCreate, repo: TipoAlertaRepository = Depends(get_repo)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_tipo_alerta}", response_model=TipoAlertaResponse)
async def actualizar(id_tipo_alerta: int, data: TipoAlertaUpdate, repo: TipoAlertaRepository = Depends(get_repo)):
    item = repo.update(id_tipo_alerta, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Tipo de alerta no encontrado")
    return item

@router.delete("/{id_tipo_alerta}")
async def eliminar(id_tipo_alerta: int, repo: TipoAlertaRepository = Depends(get_repo)):
    repo.delete(id_tipo_alerta)
    return {"mensaje": "Tipo de alerta eliminado correctamente"}