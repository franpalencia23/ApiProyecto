from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from models.schemas import RegionCreate, RegionUpdate, RegionResponse
from core.auth_deps import obtener_usuario_actual, requiere_admin

router = APIRouter()

class RegionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("region", "id_region", db)

def get_repo(db = Depends(get_db)) -> RegionRepository:
    return RegionRepository(db)

@router.get("/", response_model=list[RegionResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), repo: RegionRepository = Depends(get_repo)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_region}", response_model=RegionResponse)
async def obtener(id_region: int, repo: RegionRepository = Depends(get_repo)):
    item = repo.get_by_id(id_region)
    if not item:
        raise HTTPException(status_code=404, detail="Región no encontrada")
    return item

@router.post("/", response_model=RegionResponse, status_code=201)
async def crear(data: RegionCreate, repo: RegionRepository = Depends(get_repo)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_region}", response_model=RegionResponse)
async def actualizar(id_region: int, data: RegionUpdate, repo: RegionRepository = Depends(get_repo)):
    item = repo.update(id_region, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Región no encontrada")
    return item

@router.delete("/{id_region}")
async def eliminar(id_region: int, repo: RegionRepository = Depends(get_repo)):
    repo.delete(id_region)
    return {"mensaje": "Región eliminada correctamente"}


@router.get("/", response_model=list[RegionResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0),
                  repo: RegionRepository = Depends(get_repo),
                  usuario=Depends(obtener_usuario_actual)):   # <- cualquiera logueado
    return repo.get_all(limit=limit, offset=offset)

@router.post("/", response_model=RegionResponse, status_code=201)
async def crear(data: RegionCreate, repo: RegionRepository = Depends(get_repo),
                 usuario=Depends(requiere_admin)):             # <- solo admin
    return repo.create(data.model_dump(exclude_unset=True))