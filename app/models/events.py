from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class NotificationType(str, Enum):
    USER_WELCOME = "user_welcome"
    LOGIN_NOTIFICATION = "login_notification"
    PASSWORD_RESET = "password_reset"
    PASSWORD_UPDATED = "password_updated"

class UsuarioCreadoEvent(BaseModel):
    usuario_id: str = Field(alias="usuarioId")
    email: str
    nombre: str
    timestamp: datetime
    activation_token: Optional[str] = Field(None, alias="activationToken")
    base_url: Optional[str] = Field(None, alias="baseUrl")

    class Config:
        populate_by_name = True

class SesionIniciadaEvent(BaseModel):
    usuario_id: int = Field(alias="usuarioId")
    email: str
    nombre: str
    timestamp: datetime
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")
    device_info: Optional[str] = Field(None, alias="deviceInfo")
    location: Optional[str] = None

    class Config:
        populate_by_name = True

class PasswordResetSolicitadoEvent(BaseModel):
    usuario_id: str = Field(alias="usuarioId")
    email: str
    nombre: str
    token: str
    fecha_solicitud: datetime = Field(alias="fechaSolicitud")

    class Config:
        populate_by_name = True

class PasswordActualizadoEvent(BaseModel):
    usuario_id: str = Field(alias="usuarioId")
    email: str
    nombre: str
    fecha_actualizacion: datetime = Field(alias="fechaActualizacion")

    class Config:
        populate_by_name = True

class NotificationEvent(BaseModel):
    type: NotificationType
    email: str
    user_name: str = Field(alias="userName")
    timestamp: datetime
    additional_data: Optional[Dict[str, Any]] = Field(None, alias="additionalData")

    class Config:
        populate_by_name = True
        use_enum_values = True