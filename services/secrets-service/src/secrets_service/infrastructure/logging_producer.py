import asyncio
import logging
from datetime import UTC, datetime

from faststream.kafka import KafkaBroker

logger = logging.getLogger(__name__)


async def publish_health_logs(broker: KafkaBroker):
    """
    Background task to publish health check logs to Kafka.
    """
    publisher = broker.publisher("service-logs")

    while True:
        try:
            log_entry = {
                "service": "secrets-service",
                "level": "INFO",
                "message": "Health check: Service is running",
                "timestamp": datetime.now(UTC).isoformat(),
                "environment": "development"
            }

            await publisher.publish(log_entry)
            # logger.info("Published health log to Kafka") # Reduce noise

        except Exception as e:
            logger.error(f"Failed to publish health log: {e}")

        await asyncio.sleep(10)
