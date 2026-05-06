import asyncio
import logging
from datetime import UTC, datetime

from faststream.kafka import KafkaBroker

logger = logging.getLogger(__name__)


async def publish_health_logs(broker: KafkaBroker):
    publisher = broker.publisher("service-logs")

    while True:
        try:
            log_entry = {
                "service": "auth-service",
                "level": "INFO",
                "message": "Health check: Service is running",
                "timestamp": datetime.now(UTC).isoformat(),
                "environment": "development"
            }

            await publisher.publish(log_entry)

        except Exception as e:
            logger.error(f"Failed to publish health log: {e}")

        await asyncio.sleep(10)
