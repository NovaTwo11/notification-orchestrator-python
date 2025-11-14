from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Aplicación
    app_name: str = "notification-orchestrator"
    app_version: str = "1.0.0"
    port: int = 8088

    # RabbitMQ
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    # Colas
    exchange_name: str = "app.events"
    usuarios_queue: str = "usuarios.events"
    sesiones_queue: str = "sesiones.events"
    password_reset_queue: str = "password.reset.requested"
    password_updated_queue: str = "password.updated"
    notifications_queue: str = "notifications.delivery"
    notifications_routing_key: str = "notifications.send"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()