from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from core.repository import BaseRepository
from core.auth_deps import obtener_usuario_actual, requiere_admin
from models.schemas import TratamientoCreate, TratamientoUpdate, TratamientoResponse

router = APIRouter()

class TratamientoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__("tratamiento", "id_tratamiento", db)

def get_repo(db = Depends(get_db)) -> TratamientoRepository:
    return TratamientoRepository(db)

@router.get("/", response_model=list[TratamientoResponse])
async def listar(limit: int = Query(100, ge=1), offset: int = Query(0, ge=0),
                  repo: TratamientoRepository = Depends(get_repo),
                  usuario = Depends(obtener_usuario_actual)):
    return repo.get_all(limit=limit, offset=offset)

@router.get("/{id_tratamiento}", response_model=TratamientoResponse)
async def obtener(id_tratamiento: int, repo: TratamientoRepository = Depends(get_repo),
                   usuario = Depends(obtener_usuario_actual)):
    item = repo.get_by_id(id_tratamiento)
    if not item:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return item

@router.post("/", response_model=TratamientoResponse, status_code=201)
async def crear(data: TratamientoCreate, repo: TratamientoRepository = Depends(get_repo),
                 usuario = Depends(obtener_usuario_actual)):   # <- EXCEPCIÓN: cualquiera
    return repo.create(data.model_dump(exclude_unset=True))

@router.put("/{id_tratamiento}", response_model=TratamientoResponse)
async def actualizar(id_tratamiento: int, data: TratamientoUpdate, repo: TratamientoRepository = Depends(get_repo),
                      usuario = Depends(requiere_admin)):
    item = repo.update(id_tratamiento, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return item

@router.delete("/{id_tratamiento}")
async def eliminar(id_tratamiento: int, repo: TratamientoRepository = Depends(get_repo),
                    usuario = Depends(requiere_admin)):
    repo.delete(id_tratamiento)
    return {"mensaje": "Tratamiento eliminado correctamente"}