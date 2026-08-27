from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from models.schemas import MedicionCreate, MedicionUpdate, MedicionResponse

router = APIRouter()

class MedicionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("medicion", "id_medicion", db)

def get_repo(db = Depends(get_db)) -> MedicionRepository:
    return MedicionRepository(db)

@router.get("/", response_model=list[MedicionResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), repo: MedicionRepository = Depends(get_repo)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_medicion}", response_model=MedicionResponse)
async def obtener(id_medicion: int, repo: MedicionRepository = Depends(get_repo)):
    item = repo.get_by_id(id_medicion)
    if not item:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return item

@router.post("/", response_model=MedicionResponse, status_code=201)
async def crear(data: MedicionCreate, repo: MedicionRepository = Depends(get_repo)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_medicion}", response_model=MedicionResponse)
async def actualizar(id_medicion: int, data: MedicionUpdate, repo: MedicionRepository = Depends(get_repo)):
    item = repo.update(id_medicion, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return item

@router.delete("/{id_medicion}")
async def eliminar(id_medicion: int, repo: MedicionRepository = Depends(get_repo)):
    repo.delete(id_medicion)
    return {"mensaje": "Medición eliminada correctamente"}