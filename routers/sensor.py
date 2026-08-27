from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from models.schemas import SensorCreate, SensorUpdate, SensorResponse

router = APIRouter()

class SensorRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("sensor", "id_sensor", db)

def get_repo(db = Depends(get_db)) -> SensorRepository:
    return SensorRepository(db)

@router.get("/", response_model=list[SensorResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), repo: SensorRepository = Depends(get_repo)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_sensor}", response_model=SensorResponse)
async def obtener(id_sensor: int, repo: SensorRepository = Depends(get_repo)):
    item = repo.get_by_id(id_sensor)
    if not item:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return item

@router.post("/", response_model=SensorResponse, status_code=201)
async def crear(data: SensorCreate, repo: SensorRepository = Depends(get_repo)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_sensor}", response_model=SensorResponse)
async def actualizar(id_sensor: int, data: SensorUpdate, repo: SensorRepository = Depends(get_repo)):
    item = repo.update(id_sensor, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return item

@router.delete("/{id_sensor}")
async def eliminar(id_sensor: int, repo: SensorRepository = Depends(get_repo)):
    repo.delete(id_sensor)
    return {"mensaje": "Sensor eliminado correctamente"}