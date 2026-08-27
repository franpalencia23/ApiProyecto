from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from models.schemas import PersonalCreate, PersonalUpdate, PersonalResponse

router = APIRouter()

class PersonalRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("personal", "id_personal", db)

def get_repo(db = Depends(get_db)) -> PersonalRepository:
    return PersonalRepository(db)

@router.get("/", response_model=list[PersonalResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), repo: PersonalRepository = Depends(get_repo)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_personal}", response_model=PersonalResponse)
async def obtener(id_personal: int, repo: PersonalRepository = Depends(get_repo)):
    item = repo.get_by_id(id_personal)
    if not item:
        raise HTTPException(status_code=404, detail="Registro de personal no encontrado")
    return item

@router.post("/", response_model=PersonalResponse, status_code=201)
async def crear(data: PersonalCreate, repo: PersonalRepository = Depends(get_repo)):
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_personal}", response_model=PersonalResponse)
async def actualizar(id_personal: int, data: PersonalUpdate, repo: PersonalRepository = Depends(get_repo)):
    item = repo.update(id_personal, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Registro de personal no encontrado")
    return item

@router.delete("/{id_personal}")
async def eliminar(id_personal: int, repo: PersonalRepository = Depends(get_repo)):
    repo.delete(id_personal)
    return {"mensaje": "Personal eliminado correctamente"}