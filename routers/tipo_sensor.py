from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from models.schemas import TipoSensorCreate, TipoSensorUpdate, TipoSensorResponse

router = APIRouter()

class TipoSensorRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("tipo_sensor", "id_tipo_sensor", db)

def get_repo(db = Depends(get_db)) -> TipoSensorRepository:
    return TipoSensorRepository(db)

@router.get("/", response_model=list[TipoSensorResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), repo: TipoSensorRepository = Depends(get_repo)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_tipo_sensor}", response_model=TipoSensorResponse)
async def obtener(id_tipo_sensor: int, repo: TipoSensorRepository = Depends(get_repo)):
    item = repo.get_by_id(id_tipo_sensor)
    if not item:
        raise HTTPException(status_code=404, detail="Tipo de sensor no encontrado")
    return item

@router.post("/", response_model=TipoSensorResponse, status_code=201)
async def crear(data: TipoSensorCreate, repo: TipoSensorRepository = Depends(get_repo)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_tipo_sensor}", response_model=TipoSensorResponse)
async def actualizar(id_tipo_sensor: int, data: TipoSensorUpdate, repo: TipoSensorRepository = Depends(get_repo)):
    item = repo.update(id_tipo_sensor, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Tipo de sensor no encontrado")
    return item

@router.delete("/{id_tipo_sensor}")
async def eliminar(id_tipo_sensor: int, repo: TipoSensorRepository = Depends(get_repo)):
    repo.delete(id_tipo_sensor)
    return {"mensaje": "Tipo de sensor eliminado correctamente"}