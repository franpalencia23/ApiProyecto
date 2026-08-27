from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# ==========================================
# 1. REGION
# ==========================================
class RegionBase(BaseModel):
    nombre: str
    departamento: str
    municipio: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    altitud_msnm: Optional[int] = None

class RegionCreate(RegionBase): pass
class RegionUpdate(RegionBase): pass
class RegionResponse(RegionBase):
    id_region: int

# ==========================================
# 2. ESPECIE VEGETAL
# ==========================================
class EspecieVegetalBase(BaseModel):
    nombre_cientifico: str
    nombre_comun: str
    familia: Optional[str] = None
    umbral_estres_min: Optional[float] = None
    umbral_estres_max: Optional[float] = None
    descripcion: Optional[str] = None

class EspecieVegetalCreate(EspecieVegetalBase): pass
class EspecieVegetalUpdate(EspecieVegetalBase): pass
class EspecieVegetalResponse(EspecieVegetalBase):
    id_especie: int

# ==========================================
# 3. ZONA REFORESTACION
# ==========================================
class ZonaReforestacionBase(BaseModel):
    id_region: int
    id_especie: int
    nombre_zona: str
    area_hectareas: float
    fecha_siembra: Optional[date] = None
    estado: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

class ZonaReforestacionCreate(ZonaReforestacionBase): pass
class ZonaReforestacionUpdate(ZonaReforestacionBase): pass
class ZonaReforestacionResponse(ZonaReforestacionBase):
    id_zona: int

# ==========================================
# 4. TIPO SENSOR
# ==========================================
class TipoSensorBase(BaseModel):
    nombre: str
    unidad_medida: str
    rango_min: Optional[float] = None
    rango_max: Optional[float] = None
    descripcion: Optional[str] = None

class TipoSensorCreate(TipoSensorBase): pass
class TipoSensorUpdate(TipoSensorBase): pass
class TipoSensorResponse(TipoSensorBase):
    id_tipo_sensor: int

# ==========================================
# 5. SENSOR
# ==========================================
class SensorBase(BaseModel):
    id_zona: int
    id_tipo_sensor: int
    codigo_sensor: str
    fecha_instalacion: Optional[date] = None
    estado: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

class SensorCreate(SensorBase): pass
class SensorUpdate(SensorBase): pass
class SensorResponse(SensorBase):
    id_sensor: int

# ==========================================
# 6. PERSONAL
# ==========================================
class PersonalBase(BaseModel):
    nombre: str
    apellido: str
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    especialidad: Optional[str] = None

class PersonalCreate(PersonalBase): pass
class PersonalUpdate(PersonalBase): pass
class PersonalResponse(PersonalBase):
    id_personal: int

# ==========================================
# 7. MEDICION
# ==========================================
class MedicionBase(BaseModel):
    id_zona: int
    id_sensor: int
    id_personal: int
    valor: float
    unidad: Optional[str] = None
    observaciones: Optional[str] = None

class MedicionCreate(MedicionBase): pass
class MedicionUpdate(MedicionBase): pass
class MedicionResponse(MedicionBase):
    id_medicion: int
    fecha_hora: datetime

# ==========================================
# 8. TIPO ALERTA
# ==========================================
class TipoAlertaBase(BaseModel):
    nombre: str
    nivel_severidad: Optional[str] = None
    descripcion: Optional[str] = None
    protocolo_accion: Optional[str] = None

class TipoAlertaCreate(TipoAlertaBase): pass
class TipoAlertaUpdate(TipoAlertaBase): pass
class TipoAlertaResponse(TipoAlertaBase):
    id_tipo_alerta: int

# ==========================================
# 9. ALERTA
# ==========================================
class AlertaBase(BaseModel):
    id_medicion: int
    id_tipo_alerta: int
    estado: Optional[str] = None
    descripcion: Optional[str] = None

class AlertaCreate(AlertaBase): pass
class AlertaUpdate(AlertaBase): pass
class AlertaResponse(AlertaBase):
    id_alerta: int
    fecha_generacion: datetime
    fecha_resolucion: Optional[datetime] = None

# ==========================================
# 10. TRATAMIENTO
# ==========================================
class TratamientoBase(BaseModel):
    id_zona: int
    id_personal: int
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    tipo_tratamiento: Optional[str] = None
    volumen_agua_litros: Optional[float] = None
    resultado: Optional[str] = None
    notas: Optional[str] = None

class TratamientoCreate(TratamientoBase): pass
class TratamientoUpdate(TratamientoBase): pass
class TratamientoResponse(TratamientoBase):
    id_tratamiento: int