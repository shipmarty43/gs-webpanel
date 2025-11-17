"""Monitor service for checking host availability"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.host import Host
from app.models.log import PingHistory
from app.services.gsocket_service import gsocket_service
from app.services.logger_service import logger_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MonitorService:
    """Service for monitoring host availability"""

    @staticmethod
    async def check_all_hosts():
        """Check availability of all hosts"""
        db = SessionLocal()

        try:
            hosts = db.query(Host).all()
            logger.info(f"Checking {len(hosts)} hosts...")

            # Check all hosts in parallel
            tasks = [MonitorService._check_single_host(db, host) for host in hosts]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("Host check completed")

        except Exception as e:
            logger.error(f"Error checking hosts: {e}")

        finally:
            db.close()

    @staticmethod
    async def _check_single_host(db: Session, host: Host):
        """Check a single host availability"""
        import time
        start_time = time.time()

        try:
            is_online = await gsocket_service.check_host_availability(
                secret=host.gsocket_secret,
                timeout=settings.PING_TIMEOUT,
                custom_gsrn_server=host.custom_gsrn_server
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            # Update host status
            old_status = host.status
            new_status = "online" if is_online else "offline"

            host.status = new_status
            if is_online:
                host.last_seen = datetime.utcnow()

            # Log status change
            if old_status != new_status:
                logger_service.info(
                    db,
                    f"Host {host.hostname} status changed: {old_status} -> {new_status}",
                    category="connection",
                    host_id=host.id
                )

            # Save ping history
            ping = PingHistory(
                host_id=host.id,
                status=new_status,
                response_time_ms=response_time_ms if is_online else None
            )
            db.add(ping)
            db.commit()

        except Exception as e:
            logger.error(f"Error checking host {host.hostname}: {e}")
            host.status = "offline"
            db.commit()

    @staticmethod
    async def cleanup_old_records(db: Session):
        """Clean up old ping history records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.LOG_RETENTION_DAYS)

            # Delete old ping history
            deleted = db.query(PingHistory).filter(
                PingHistory.checked_at < cutoff_date
            ).delete()

            db.commit()
            logger.info(f"Cleaned up {deleted} old ping history records")

        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            db.rollback()

    @staticmethod
    async def monitor_loop():
        """Main monitoring loop"""
        logger.info("Starting monitor service...")

        while True:
            try:
                await MonitorService.check_all_hosts()

                # Cleanup old records once a day
                db = SessionLocal()
                await MonitorService.cleanup_old_records(db)
                db.close()

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")

            # Wait for next check
            await asyncio.sleep(settings.HOST_CHECK_INTERVAL)


# Singleton instance
monitor_service = MonitorService()


# Main entry point for running as standalone service
if __name__ == "__main__":
    asyncio.run(monitor_service.monitor_loop())
