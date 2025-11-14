import logging
import signal
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading

from app.config.settings import settings
from app.services.rabbitmq_consumer import RabbitMQConsumer
from app.services.notification_publisher import NotificationPublisher
from app.utils.logger import setup_logging

# Configurar logging al inicio
setup_logging()
logger = logging.getLogger(__name__)

# Variables globales para los servicios
consumer = None
publisher = None
consumer_thread = None

def handle_usuario_creado(event):
    """
    Handler para eventos de usuario creado.
    Transforma el evento y lo publica hacia el servicio de Delivery.
    """
    logger.info(f"📩 Usuario creado recibido: {event.email}")
    try:
        # Transformar evento de dominio a evento de notificación
        notification = publisher.create_user_welcome_notification(event)

        # Publicar hacia Delivery
        publisher.publish_notification(notification)

        logger.info(f"✅ Notificación de bienvenida procesada para: {event.email}")

    except Exception as e:
        logger.error(f"❌ Error procesando usuario creado: {e}", exc_info=True)

def handle_sesion_iniciada(event):
    """
    Handler para eventos de sesión iniciada.
    """
    logger.info(f"📩 Sesión iniciada recibida: {event.email}")
    try:
        notification = publisher.create_login_notification(event)
        publisher.publish_notification(notification)

        logger.info(f"✅ Notificación de login procesada para: {event.email}")

    except Exception as e:
        logger.error(f"❌ Error procesando sesión iniciada: {e}", exc_info=True)

def handle_password_reset(event):
    """
    Handler para eventos de reset de password solicitado.
    """
    logger.info(f"📩 Password reset recibido: {event.email}")
    try:
        notification = publisher.create_password_reset_notification(event)
        publisher.publish_notification(notification)

        logger.info(f"✅ Notificación de reset de password procesada para: {event.email}")

    except Exception as e:
        logger.error(f"❌ Error procesando password reset: {e}", exc_info=True)

def handle_password_updated(event):
    """
    Handler para eventos de password actualizado.
    """
    logger.info(f"📩 Password updated recibido: {event.email}")
    try:
        notification = publisher.create_password_updated_notification(event)
        publisher.publish_notification(notification)

        logger.info(f"✅ Notificación de password actualizado procesada para: {event.email}")

    except Exception as e:
        logger.error(f"❌ Error procesando password updated: {e}", exc_info=True)

def start_rabbitmq_consumers():
    """
    Inicia los consumidores de RabbitMQ.
    Esta función se ejecuta en un thread separado.
    """
    global consumer, publisher

    try:
        logger.info("🔧 Configurando consumidores de RabbitMQ...")

        # Crear instancias de consumer y publisher
        consumer = RabbitMQConsumer()
        publisher = NotificationPublisher()

        # Registrar handlers para cada tipo de evento
        consumer.consume_usuarios(handle_usuario_creado)
        consumer.consume_sesiones(handle_sesion_iniciada)
        consumer.consume_password_reset(handle_password_reset)
        consumer.consume_password_updated(handle_password_updated)

        logger.info("✅ Consumidores configurados. Iniciando consumo...")

        # Iniciar consumo (bloqueante)
        consumer.start_consuming()

    except KeyboardInterrupt:
        logger.info("⚠️ Consumo interrumpido por señal")
    except Exception as e:
        logger.error(f"❌ Error en consumidores: {e}", exc_info=True)
        sys.exit(1)

def signal_handler(signum, frame):
    """
    Maneja señales de terminación (SIGINT, SIGTERM).
    Permite un cierre graceful de las conexiones.
    """
    logger.info(f"⚠️ Señal {signum} recibida, cerrando aplicación...")

    # Cerrar consumer
    if consumer:
        try:
            consumer.close()
        except Exception as e:
            logger.error(f"Error cerrando consumer: {e}")

    # Cerrar publisher
    if publisher:
        try:
            publisher.close()
        except Exception as e:
            logger.error(f"Error cerrando publisher: {e}")

    sys.exit(0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación FastAPI.
    Se ejecuta al inicio y al finalizar la aplicación.
    """
    global consumer_thread

    # ========== STARTUP ==========
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {settings.app_name} v{settings.app_version}")
    logger.info("=" * 60)
    logger.info(f"📍 RabbitMQ Host: {settings.rabbitmq_host}:{settings.rabbitmq_port}")
    logger.info(f"📍 Exchange: {settings.exchange_name}")
    logger.info(f"📍 Puerto HTTP: {settings.port}")
    logger.info("=" * 60)

    # Registrar signal handlers para cierre graceful
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Iniciar consumidores en un thread separado
    # (FastAPI corre en el thread principal)
    logger.info("🔄 Iniciando thread de consumidores...")
    consumer_thread = threading.Thread(
        target=start_rabbitmq_consumers,
        daemon=True,
        name="RabbitMQConsumerThread"
    )
    consumer_thread.start()
    logger.info("✅ Thread de consumidores iniciado")

    # Yield para que la aplicación corra
    yield

    # ========== SHUTDOWN ==========
    logger.info("=" * 60)
    logger.info("👋 Cerrando aplicación...")
    logger.info("=" * 60)

    # Cerrar conexiones
    if consumer:
        consumer.close()
    if publisher:
        publisher.close()

    logger.info("✅ Aplicación cerrada correctamente")

# ========== CREAR APLICACIÓN FASTAPI ==========
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservicio orquestador de notificaciones",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Endpoint raíz - información del servicio"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "description": "Notification Orchestrator - Procesa eventos de dominio y los transforma en notificaciones"
    }

@app.get("/health")
async def health():
    """
    Health check endpoint.
    Usado por Docker y sistemas de orquestación para verificar que el servicio está vivo.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }

@app.get("/metrics")
async def metrics():
    """
    Endpoint de métricas básicas.
    Puede extenderse con Prometheus metrics en el futuro.
    """
    return {
        "service": settings.app_name,
        "consumer_running": consumer_thread.is_alive() if consumer_thread else False
    }

# ========== PUNTO DE ENTRADA ==========
if __name__ == "__main__":
    import uvicorn

    logger.info("🎬 Iniciando servidor Uvicorn...")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True
    )