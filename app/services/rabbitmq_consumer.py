import pika
import json
import logging
import time

from typing import Callable
from app.config.settings import settings
from app.models.events import (
    UsuarioCreadoEvent,
    SesionIniciadaEvent,
    PasswordResetSolicitadoEvent,
    PasswordActualizadoEvent
)

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """
    Consumidor de mensajes de RabbitMQ.
    Escucha múltiples colas y procesa eventos de dominio.
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self.setup_connection()

    def setup_connection(self):

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
                logger.info(f"🔄 Intentando conectar a RabbitMQ (intento {attempt}/{MAX_RETRIES})...")
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declarar exchange y colas
                self.channel.exchange_declare(
                    exchange=settings.exchange_name,
                    exchange_type='topic',
                    durable=True
                )
                self._declare_queues()

                logger.info("✅ Conexión a RabbitMQ establecida exitosamente")
                return

            except Exception as e:
                logger.error(f"❌ Error conectando a RabbitMQ: {e}")
                if attempt == MAX_RETRIES:
                    logger.critical("🔥 No se pudo conectar después de múltiples intentos. Abortando.")
                    raise

                wait = WAIT_SECONDS
                logger.info(f"⏳ Reintentando en {wait} segundos...")
                time.sleep(wait)
                attempt += 1


    def _declare_queues(self):
        """
        Declara todas las colas necesarias y las vincula al exchange.
        Cada cola se asocia con su routing key específico.
        """
        queues_config = [
            (settings.usuarios_queue, "usuarios.created"),
            (settings.sesiones_queue, "sesiones.iniciada"),
            (settings.password_reset_queue, "password.reset.requested"),
            (settings.password_updated_queue, "password.updated"),
        ]

        for queue_name, routing_key in queues_config:
            # Declarar cola como durable para persistencia
            self.channel.queue_declare(queue=queue_name, durable=True)

            # Vincular cola al exchange con routing key
            self.channel.queue_bind(
                exchange=settings.exchange_name,
                queue=queue_name,
                routing_key=routing_key
            )

            logger.info(f"✅ Cola configurada: {queue_name} -> {routing_key}")

    def consume_usuarios(self, callback: Callable):
        """
        Consume eventos de usuarios creados.

        Args:
            callback: Función a ejecutar cuando se reciba un mensaje
        """
        def on_message(ch, method, properties, body):
            try:
                # Deserializar mensaje JSON
                data = json.loads(body.decode('utf-8'))
                logger.debug(f"📩 Mensaje recibido en usuarios.events: {data}")

                # Parsear a objeto Pydantic para validación
                event = UsuarioCreadoEvent(**data)

                # Ejecutar callback
                callback(event)

                # Confirmar procesamiento exitoso
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug(f"✅ Mensaje procesado y confirmado")

            except Exception as e:
                logger.error(f"❌ Error procesando evento de usuario: {e}")
                # Rechazar mensaje sin reencolar (evita loops infinitos)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        # Configurar consumidor
        self.channel.basic_consume(
            queue=settings.usuarios_queue,
            on_message_callback=on_message
        )
        logger.info(f"👂 Escuchando en cola: {settings.usuarios_queue}")

    def consume_sesiones(self, callback: Callable):
        """
        Consume eventos de sesiones iniciadas.

        Args:
            callback: Función a ejecutar cuando se reciba un mensaje
        """
        def on_message(ch, method, properties, body):
            try:
                data = json.loads(body.decode('utf-8'))
                logger.debug(f"📩 Mensaje recibido en sesiones.events: {data}")

                event = SesionIniciadaEvent(**data)
                callback(event)

                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug(f"✅ Mensaje procesado y confirmado")

            except Exception as e:
                logger.error(f"❌ Error procesando evento de sesión: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=settings.sesiones_queue,
            on_message_callback=on_message
        )
        logger.info(f"👂 Escuchando en cola: {settings.sesiones_queue}")

    def consume_password_reset(self, callback: Callable):
        """
        Consume eventos de reset de password solicitados.

        Args:
            callback: Función a ejecutar cuando se reciba un mensaje
        """
        def on_message(ch, method, properties, body):
            try:
                data = json.loads(body.decode('utf-8'))
                logger.debug(f"📩 Mensaje recibido en password.reset.requested: {data}")

                event = PasswordResetSolicitadoEvent(**data)
                callback(event)

                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug(f"✅ Mensaje procesado y confirmado")

            except Exception as e:
                logger.error(f"❌ Error procesando evento de password reset: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=settings.password_reset_queue,
            on_message_callback=on_message
        )
        logger.info(f"👂 Escuchando en cola: {settings.password_reset_queue}")

    def consume_password_updated(self, callback: Callable):
        """
        Consume eventos de password actualizado.

        Args:
            callback: Función a ejecutar cuando se reciba un mensaje
        """
        def on_message(ch, method, properties, body):
            try:
                data = json.loads(body.decode('utf-8'))
                logger.debug(f"📩 Mensaje recibido en password.updated: {data}")

                event = PasswordActualizadoEvent(**data)
                callback(event)

                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug(f"✅ Mensaje procesado y confirmado")

            except Exception as e:
                logger.error(f"❌ Error procesando evento de password updated: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=settings.password_updated_queue,
            on_message_callback=on_message
        )
        logger.info(f"👂 Escuchando en cola: {settings.password_updated_queue}")

    def start_consuming(self):
        """
        Inicia el consumo de mensajes.
        Este método es bloqueante y mantendrá el proceso corriendo.
        """
        logger.info("🚀 Iniciando consumo de mensajes...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("⚠️ Consumo interrumpido por el usuario")
            self.close()
        except Exception as e:
            logger.error(f"❌ Error durante el consumo: {e}")
            self.close()
            raise

    def close(self):
        """Cierra la conexión a RabbitMQ de forma segura"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("👋 Conexión a RabbitMQ cerrada")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexión: {e}")