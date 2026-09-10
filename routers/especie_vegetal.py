from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from core.auth_deps import obtener_usuario_actual, requiere_admin
from models.schemas import EspecieVegetalCreate, EspecieVegetalUpdate, EspecieVegetalResponse

router = APIRouter()

class EspecieVegetalRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("especie_vegetal", "id_especie", db)

def get_repo(db = Depends(get_db)) -> EspecieVegetalRepository:
    return EspecieVegetalRepository(db)

@router.get("/", response_model=list[EspecieVegetalResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0),
                  repo: EspecieVegetalRepository = Depends(get_repo),
                  usuario = Depends(obtener_usuario_actual)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_especie}", response_model=EspecieVegetalResponse)
async def obtener(id_especie: int, repo: EspecieVegetalRepository = Depends(get_repo),
                   usuario = Depends(obtener_usuario_actual)):
    item = repo.get_by_id(id_especie)
    if not item:
        raise HTTPException(status_code=404, detail="Especie vegetal no encontrada")
    return item

@router.post("/", response_model=EspecieVegetalResponse, status_code=201)
async def crear(data: EspecieVegetalCreate, repo: EspecieVegetalRepository = Depends(get_repo),
                 usuario = Depends(requiere_admin)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_especie}", response_model=EspecieVegetalResponse)
async def actualizar(id_especie: int, data: EspecieVegetalUpdate, repo: EspecieVegetalRepository = Depends(get_repo),
                      usuario = Depends(requiere_admin)):
    item = repo.update(id_especie, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Especie vegetal no encontrada")
    return item

@router.delete("/{id_especie}")
async def eliminar(id_especie: int, repo: EspecieVegetalRepository = Depends(get_repo),
                    usuario = Depends(requiere_admin)):
    repo.delete(id_especie)
    return {"mensaje": "Especie eliminada correctamente"}