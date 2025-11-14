import pika
import json
import logging
import time
from datetime import datetime
from app.config.settings import settings
from app.models.events import NotificationEvent, NotificationType

logger = logging.getLogger(__name__)

class NotificationPublisher:
    """
    Publicador de eventos de notificación hacia el servicio de Delivery.
    Transforma eventos de dominio en eventos de notificación.
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self.setup_connection()

    def setup_connection(self):
        """Establece conexión con RabbitMQ para publicar mensajes con reintentos"""
        MAX_RETRIES = 20
        WAIT_SECONDS = 3

        credentials = pika.PlainCredentials(
            settings.rabbitmq_user,
            settings.rabbitmq_password
        )
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

        attempt = 1
        while attempt <= MAX_RETRIES:
            try:
                logger.info(f"🔄 Intentando conectar publicador a RabbitMQ (intento {attempt}/{MAX_RETRIES})...")
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declarar exchange
                self.channel.exchange_declare(
                    exchange=settings.exchange_name,
                    exchange_type='topic',
                    durable=True
                )

                # Declarar cola de destino (notifications.delivery)
                self.channel.queue_declare(
                    queue=settings.notifications_queue,
                    durable=True
                )

                # Vincular cola al exchange
                self.channel.queue_bind(
                    exchange=settings.exchange_name,
                    queue=settings.notifications_queue,
                    routing_key=settings.notifications_routing_key
                )

                logger.info("✅ Publicador de notificaciones configurado exitosamente")
                return

            except Exception as e:
                logger.error(f"❌ Error configurando publicador (intento {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    logger.critical("🔥 No se pudo conectar el publicador después de múltiples intentos. Abortando.")
                    raise

                wait = WAIT_SECONDS
                logger.info(f"⏳ Reintentando en {wait} segundos...")
                time.sleep(wait)
                attempt += 1

    def publish_notification(self, notification: NotificationEvent):
        """
        Publica una notificación al servicio de Delivery.

        Args:
            notification: Evento de notificación a publicar

        Raises:
            RuntimeError: Si ocurre un error al publicar
        """
        try:
            # Serializar el evento a JSON usando el esquema de Pydantic
            message = notification.model_dump(mode='json', by_alias=True)

            logger.debug(f"🚀 Publicando NotificationEvent: {notification.type} -> {notification.email}")

            # Publicar mensaje
            self.channel.basic_publish(
                exchange=settings.exchange_name,
                routing_key=settings.notifications_routing_key,
                body=json.dumps(message, default=str),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json',
                    timestamp=int(datetime.now().timestamp())
                )
            )

            logger.info(f"📤 Notificación publicada exitosamente: {notification.type} -> {notification.email}")

        except Exception as e:
            logger.error(f"❌ Error publicando notificación: {e}")
            raise RuntimeError(f"Error publicando notificación: {e}")

    def create_user_welcome_notification(self, event) -> NotificationEvent:
        """
        Crea una notificación de bienvenida a partir de un evento de usuario creado.

        Args:
            event: UsuarioCreadoEvent

        Returns:
            NotificationEvent configurado para bienvenida
        """
        additional_data = {}

        # Si hay token de activación, incluirlo
        if hasattr(event, 'activation_token') and event.activation_token:
            additional_data['activationToken'] = event.activation_token

        # Si hay base URL, incluirla
        if hasattr(event, 'base_url') and event.base_url:
            additional_data['baseUrl'] = event.base_url

        notification = NotificationEvent(
            type=NotificationType.USER_WELCOME,
            email=event.email,
            user_name=event.nombre,
            timestamp=datetime.now(),
            additional_data=additional_data if additional_data else None
        )

        logger.debug(f"📝 Notificación de bienvenida creada para: {event.email}")
        return notification

    def create_login_notification(self, event) -> NotificationEvent:
        """
        Crea una notificación de inicio de sesión.

        Args:
            event: SesionIniciadaEvent

        Returns:
            NotificationEvent configurado para notificación de login
        """
        additional_data = {
            'ipAddress': event.ip_address if event.ip_address else 'Desconocida',
            'userAgent': event.user_agent if event.user_agent else 'Desconocido',
            'deviceInfo': event.device_info if event.device_info else 'Desconocido',
            'location': event.location if event.location else 'Desconocida'
        }

        notification = NotificationEvent(
            type=NotificationType.LOGIN_NOTIFICATION,
            email=event.email,
            user_name=event.nombre,
            timestamp=event.timestamp,
            additional_data=additional_data
        )

        logger.debug(f"📝 Notificación de login creada para: {event.email}")
        return notification

    def create_password_reset_notification(self, event) -> NotificationEvent:
        """
        Crea una notificación de reset de contraseña.

        Args:
            event: PasswordResetSolicitadoEvent

        Returns:
            NotificationEvent configurado para reset de password
        """
        notification = NotificationEvent(
            type=NotificationType.PASSWORD_RESET,
            email=event.email,
            user_name=event.nombre,
            timestamp=event.fecha_solicitud,
            additional_data={'resetToken': event.token}
        )

        logger.debug(f"📝 Notificación de reset de password creada para: {event.email}")
        return notification

    def create_password_updated_notification(self, event) -> NotificationEvent:
        """
        Crea una notificación de contraseña actualizada.

        Args:
            event: PasswordActualizadoEvent

        Returns:
            NotificationEvent configurado para password actualizado
        """
        notification = NotificationEvent(
            type=NotificationType.PASSWORD_UPDATED,
            email=event.email,
            user_name=event.nombre,
            timestamp=event.fecha_actualizacion,
            additional_data=None
        )

        logger.debug(f"📝 Notificación de password actualizado creada para: {event.email}")
        return notification

    def close(self):
        """Cierra la conexión al publicador"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("👋 Publicador cerrado")
        except Exception as e:
            logger.error(f"❌ Error cerrando publicador: {e}")