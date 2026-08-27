"""routers/sensor.py — CRUD tabla SENSOR"""
from fastapi import APIRouter, Depends, Query
from core.database import get_db
from core.repository import BaseRepository
from models.schemas import SensorCreate, SensorUpdate, SensorResponse

router = APIRouter()

class SensorRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("sensor", "id_sensor", db)
    def por_zona(self, id_zona: int) -> list[dict]:
        return self._filter_by("id_zona", id_zona, "eq")
    def por_estado(self, estado: str) -> list[dict]:
        return self._filter_by("estado", estado, "eq")
    def por_tipo(self, id_tipo: int) -> list[dict]:
        return self._filter_by("id_tipo_sensor", id_tipo, "eq")
    def total(self) -> dict:
        return {"tabla": "sensor", "total_registros": self.count()}

def get_repo(db = Depends(get_db)) -> SensorRepository:
    return SensorRepository(db)

@router.get("/sensores", response_model=list[SensorResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), repo: SensorRepository = Depends(get_repo)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/sensores/total")
async def total(repo: SensorRepository = Depends(get_repo)):
    return repo.total()

@router.get("/sensores/zona/{id_zona}", response_model=list[SensorResponse])
async def por_zona(id_zona: int, repo: SensorRepository = Depends(get_repo)):
    return repo.por_zona(id_zona)

@router.get("/sensores/estado/{estado}", response_model=list[SensorResponse])
async def por_estado(estado: str, repo: SensorRepository = Depends(get_repo)):
    return repo.por_estado(estado)

@router.get("/sensores/tipo/{id_tipo}", response_model=list[SensorResponse])
async def por_tipo(id_tipo: int, repo: SensorRepository = Depends(get_repo)):
    return repo.por_tipo(id_tipo)

@router.get("/sensores/{id_sensor}", response_model=SensorResponse)
async def obtener(id_sensor: int, repo: SensorRepository = Depends(get_repo)):
    return repo.get_by_id(id_sensor)

@router.post("/sensores", response_model=SensorResponse, status_code=201)
async def crear(data: SensorCreate, repo: SensorRepository = Depends(get_repo)):
    return repo.create(data.model_dump())

@router.put("/sensores/{id_sensor}", response_model=SensorResponse)
async def actualizar(id_sensor: int, data: SensorUpdate, repo: SensorRepository = Depends(get_repo)):
    return repo.update(id_sensor, data.model_dump(exclude_unset=True))

@router.delete("/sensores/{id_sensor}")
async def eliminar(id_sensor: int, repo: SensorRepository = Depends(get_repo)):
    return repo.delete(id_sensor)
