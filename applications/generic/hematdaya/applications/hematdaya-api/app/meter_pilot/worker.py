"""Receive QoS 1 counter telemetry from the isolated TLS broker."""

import asyncio
import ssl

from paho.mqtt.client import CallbackAPIVersion, Client, MQTTErrorCode, MQTTMessage
from paho.mqtt.reasoncodes import ReasonCode
from sqlalchemy.exc import SQLAlchemyError

from app.core.clock import wall_now
from app.core.database import get_engine, get_session_factory
from app.core.errors.base import AppError, NotFoundError, RequestInvalidError
from app.core.errors.database import resolve_database_error
from app.core.errors.public import public_error_for_code
from app.core.errors.recorder import record_failure
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.meter_pilot.dependencies import build_pilot_service, require_pilot
from app.meter_pilot.service.telemetry import TOPIC_FILTER, decode_telemetry


async def accept_message(message: MQTTMessage) -> None:
    """Commit one message, or fail before the broker acknowledges it."""
    now = wall_now()
    if message.retain or message.qos != 1:
        raise RequestInvalidError()
    meter_id, reading = decode_telemetry(message.topic, message.payload, now)
    async with get_session_factory().begin() as session:
        await build_pilot_service(session).receive(meter_id, reading, now)


def _record(error: AppError, operation: str) -> None:
    public = public_error_for_code(error.code)
    record_failure(error, operation=operation, http_status=public.http_status)


def _serve(runner: asyncio.Runner) -> None:
    require_pilot()
    settings = get_settings()
    host, ca_file, username, password = (
        settings.meter_mqtt_host,
        settings.meter_mqtt_ca_file,
        settings.meter_mqtt_username,
        settings.meter_mqtt_password,
    )
    if not host or not ca_file or not username or password is None or not password.get_secret_value():
        raise RequestInvalidError()
    context = ssl.create_default_context(cafile=ca_file)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    client = Client(
        CallbackAPIVersion.VERSION2, client_id="hematdaya-meter-worker", clean_session=False, manual_ack=True
    )
    client.tls_set_context(context)
    client.username_pw_set(username, password.get_secret_value())

    def connected(broker, _userdata, _flags, reason: ReasonCode, _properties) -> None:
        if reason.is_failure:
            raise AppError()
        result, _ = broker.subscribe(TOPIC_FILTER, qos=1)
        if result != MQTTErrorCode.MQTT_ERR_SUCCESS:
            raise AppError()

    def subscribed(_broker, _userdata, _mid, reasons, _properties) -> None:
        if not reasons or any(reason.is_failure or reason.value != 1 for reason in reasons):
            raise AppError()

    def received(broker, _userdata, message: MQTTMessage) -> None:
        try:
            runner.run(accept_message(message))
        except (RequestInvalidError, NotFoundError) as error:
            # Malformed and unauthorized messages are terminal. A database failure
            # escapes before ACK so the persistent MQTT session can retry it.
            _record(error, "meter_pilot.receive")
        if broker.ack(message.mid, message.qos) != MQTTErrorCode.MQTT_ERR_SUCCESS:
            raise AppError()

    client.on_connect = connected
    client.on_subscribe = subscribed
    client.on_message = received
    client.connect_async(host, port=settings.meter_mqtt_port)
    try:
        client.loop_forever(retry_first_connection=True)
    finally:
        client.disconnect()


def main() -> None:
    """Run the subscriber without logging credentials or raw payloads."""
    setup_logging(get_settings().log_level)
    with asyncio.Runner() as runner:
        try:
            _serve(runner)
        except (AppError, SQLAlchemyError, OSError, ValueError) as raw:
            error = resolve_database_error(raw) if isinstance(raw, SQLAlchemyError) else raw
            _record(error if isinstance(error, AppError) else AppError(), "meter_pilot.worker")
            raise SystemExit(1) from None
        finally:
            runner.run(get_engine().dispose())


if __name__ == "__main__":
    main()
