"""Gsocket service for communication with remote hosts"""
import subprocess
import asyncio
from typing import Dict, Optional
from app.config import settings
from app.services.crypto_service import crypto_service
import logging

logger = logging.getLogger(__name__)


class GsocketService:
    """Service for interacting with hosts via gsocket"""

    @staticmethod
    async def execute_command(
        secret: str,
        command: str,
        timeout: int = None,
        wait_time: int = None
    ) -> Dict[str, any]:
        """
        Execute a command on a remote host via gsocket

        Args:
            secret: Gsocket secret (will be decrypted if encrypted)
            command: Command to execute
            timeout: Command timeout in seconds
            wait_time: Gsocket wait time (-w parameter)

        Returns:
            Dict with exit_code, stdout, stderr, duration_ms
        """
        if timeout is None:
            timeout = settings.DEFAULT_TASK_TIMEOUT

        if wait_time is None:
            wait_time = settings.DEFAULT_GSOCKET_WAIT

        # Decrypt secret
        try:
            decrypted_secret = crypto_service.decrypt(secret)
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Failed to decrypt secret: {e}",
                "duration_ms": 0
            }

        # Build gsocket command
        gs_command = f"gs-netcat -s {decrypted_secret} -w {wait_time}"

        try:
            import time
            start_time = time.time()

            # Execute command via gsocket
            process = await asyncio.create_subprocess_shell(
                gs_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send command and get output
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=command.encode()),
                timeout=timeout
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "duration_ms": duration_ms
            }

        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass

            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command execution timed out",
                "duration_ms": timeout * 1000
            }

        except Exception as e:
            logger.error(f"Gsocket command execution failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution failed: {str(e)}",
                "duration_ms": 0
            }

    @staticmethod
    async def check_host_availability(secret: str, timeout: int = 10) -> bool:
        """
        Check if a host is available via gsocket

        Args:
            secret: Gsocket secret (encrypted)
            timeout: Ping timeout in seconds

        Returns:
            True if host is online, False otherwise
        """
        # Simple echo test
        result = await GsocketService.execute_command(
            secret=secret,
            command="echo 'ping'",
            timeout=timeout,
            wait_time=timeout
        )

        return result["exit_code"] == 0 and "ping" in result["stdout"]


# Singleton instance
gsocket_service = GsocketService()
