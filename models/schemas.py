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

class RegionUpdate(BaseModel):
    nombre: Optional[str] = None
    departamento: Optional[str] = None
    municipio: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    altitud_msnm: Optional[int] = None

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

class EspecieVegetalUpdate(BaseModel):
    nombre_cientifico: Optional[str] = None
    nombre_comun: Optional[str] = None
    familia: Optional[str] = None
    umbral_estres_min: Optional[float] = None
    umbral_estres_max: Optional[float] = None
    descripcion: Optional[str] = None

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

class ZonaReforestacionUpdate(BaseModel):
    id_region: Optional[int] = None
    id_especie: Optional[int] = None
    nombre_zona: Optional[str] = None
    area_hectareas: Optional[float] = None
    fecha_siembra: Optional[date] = None
    estado: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

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

class TipoSensorUpdate(BaseModel):
    nombre: Optional[str] = None
    unidad_medida: Optional[str] = None
    rango_min: Optional[float] = None
    rango_max: Optional[float] = None
    descripcion: Optional[str] = None

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

class SensorUpdate(BaseModel):
    id_zona: Optional[int] = None
    id_tipo_sensor: Optional[int] = None
    codigo_sensor: Optional[str] = None
    fecha_instalacion: Optional[date] = None
    estado: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

class SensorResponse(SensorBase):
    id_sensor: int

# ==========================================
# 6. PERSONAL
# ==========================================
class PersonalBase(BaseModel):
    primer_nombre: str
    segundo_nombre: Optional[str] = None
    primer_apellido: str
    segundo_apellido: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    especialidad: Optional[str] = None

class PersonalCreate(PersonalBase): pass

class PersonalUpdate(BaseModel):
    primer_nombre: Optional[str] = None
    segundo_nombre: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    especialidad: Optional[str] = None

class PersonalResponse(PersonalBase):
    id_personal: int

# ==========================================
# 7. MEDICION
# id_personal es opcional: una lectura automática de sensor no la
# registra ninguna persona. tipo_medicion identifica el tipo de dato.
# ==========================================
class MedicionBase(BaseModel):
    id_zona: int
    id_sensor: int
    id_personal: Optional[int] = None
    tipo_medicion: str
    valor: float
    unidad: Optional[str] = None
    observaciones: Optional[str] = None

class MedicionCreate(MedicionBase): pass

class MedicionUpdate(BaseModel):
    id_zona: Optional[int] = None
    id_sensor: Optional[int] = None
    id_personal: Optional[int] = None
    tipo_medicion: Optional[str] = None
    valor: Optional[float] = None
    unidad: Optional[str] = None
    observaciones: Optional[str] = None

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

class TipoAlertaUpdate(BaseModel):
    nombre: Optional[str] = None
    nivel_severidad: Optional[str] = None
    descripcion: Optional[str] = None
    protocolo_accion: Optional[str] = None

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

class AlertaUpdate(BaseModel):
    id_medicion: Optional[int] = None
    id_tipo_alerta: Optional[int] = None
    estado: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None

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

class TratamientoUpdate(BaseModel):
    id_zona: Optional[int] = None
    id_personal: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    tipo_tratamiento: Optional[str] = None
    volumen_agua_litros: Optional[float] = None
    resultado: Optional[str] = None
    notas: Optional[str] = None

class TratamientoResponse(TratamientoBase):
    id_tratamiento: int

# ==========================================
# 11. ROL
# ==========================================
class RolResponse(BaseModel):
    id_roles: int
    tipo_usuario: str

# ==========================================
# 12. USUARIO
# ==========================================
class UsuarioCreate(BaseModel):
    email: str
    password: str          # contraseña en texto plano, SOLO de entrada
    id_rol: int

class UsuarioLogin(BaseModel):
    email: str
    password: str          # contraseña en texto plano, SOLO de entrada

class UsuarioResponse(BaseModel):
    id_usuarios: int
    email: str
    id_rol: int
    creacion: date
    # OJO: password_hash NO está aquí a propósito