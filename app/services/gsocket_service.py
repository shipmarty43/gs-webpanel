"""Gsocket service for communication with remote hosts

ARCHITECTURE:
- Remote hosts run: gs-netcat -l -s <SECRET> -e /bin/bash -D
  (-l = listen mode, -e = execute commands, -D = daemon mode)

- Panel connects as client: gs-netcat -k <secret_file> -w
  (-k = secret from file (secure), -w = wait for listener)

- Commands are sent via stdin, responses received via stdout/stderr

SECURITY:
- Secrets stored encrypted in database (AES-256)
- Secrets passed via temporary file (-k flag) to avoid ps exposure
- Each host has unique secret
- SRP-AES-256-CBC-SHA end-to-end encryption (4096-bit prime)
"""
import os
import asyncio
import tempfile
from typing import Dict, Optional
from app.config import settings
from app.services.crypto_service import crypto_service
import logging

logger = logging.getLogger(__name__)


class GsocketError(Exception):
    """Base gsocket error"""
    pass


class GsocketConnectionError(GsocketError):
    """Failed to connect to host"""
    pass


class GsocketTimeoutError(GsocketError):
    """Connection or command timed out"""
    pass


class GsocketService:
    """Service for interacting with hosts via gsocket

    NOTE: Remote hosts must be configured with:
        gs-netcat -l -s <SECRET> -e /bin/bash -D

    See HOST_SETUP_GUIDE.md for detailed setup instructions.
    """

    @staticmethod
    async def execute_command(
        secret: str,
        command: str,
        timeout: int = None,
        wait_time: int = None,
        use_interactive: bool = False,
        custom_gsrn_server: str = None
    ) -> Dict[str, any]:
        """
        Execute a command on a remote host via gsocket

        The remote host must be running:
            gs-netcat -l -s <SECRET> -e /bin/bash -D

        This method connects as client and sends commands via stdin.

        Args:
            secret: Gsocket secret (encrypted in database)
            command: Bash command to execute
            timeout: Command timeout in seconds (default: 300)
            wait_time: Time to wait for listener to become available (default: 10)
            use_interactive: Use interactive PTY mode with -i flag
            custom_gsrn_server: Custom GSRN server (e.g., "relay.example.com:443")

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

        # Create temporary file for secret (secure method per documentation)
        secret_file = None
        try:
            # Write secret to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gs') as f:
                f.write(decrypted_secret)
                secret_file = f.name

            # Restrict file permissions (readable only by owner)
            os.chmod(secret_file, 0o600)

            import time
            start_time = time.time()

            # Build command arguments
            # -k: read secret from file (secure)
            # -w: wait for listener to become available (seconds)
            # -i: interactive PTY mode (optional)
            gs_args = ["gs-netcat", "-k", secret_file, "-w", str(wait_time)]

            if use_interactive:
                gs_args.append("-i")

            # Prepare environment variables for custom GSRN server
            env = os.environ.copy()
            if custom_gsrn_server:
                # Use GSOCKET_ARGS environment variable to specify custom relay server
                # Format: GSOCKET_ARGS="-s relay.example.com:443"
                env['GSOCKET_ARGS'] = f"-s {custom_gsrn_server}"
                logger.debug(f"Using custom GSRN server: {custom_gsrn_server}")
            elif settings.DEFAULT_GSRN_SERVER:
                env['GSOCKET_ARGS'] = f"-s {settings.DEFAULT_GSRN_SERVER}"
                logger.debug(f"Using default GSRN server: {settings.DEFAULT_GSRN_SERVER}")

            logger.debug(f"Executing gs-netcat with wait_time={wait_time}s, timeout={timeout}s")

            # Execute gs-netcat
            process = await asyncio.create_subprocess_exec(
                *gs_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Send command followed by exit to close connection cleanly
            command_input = f"{command}\nexit\n"

            # Execute with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=command_input.encode()),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Kill process if it times out
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass

                duration_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"Command execution timed out after {timeout}s")

                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Command execution timed out after {timeout} seconds",
                    "duration_ms": duration_ms
                }

            duration_ms = int((time.time() - start_time) * 1000)

            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            # Check for common gsocket errors in stderr
            if "waiting for a connection" in stderr_text.lower():
                # Listener not available yet (this is expected with -w)
                logger.debug("Waiting for listener to become available...")

            if "not reachable" in stderr_text.lower() or "connection refused" in stderr_text.lower():
                raise GsocketConnectionError("Host not reachable or not in listen mode")

            return {
                "exit_code": process.returncode if process.returncode is not None else 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "duration_ms": duration_ms
            }

        except GsocketConnectionError as e:
            logger.error(f"Connection failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Connection failed: {str(e)}. Ensure host is running 'gs-netcat -l -e /bin/bash -D'",
                "duration_ms": 0
            }

        except Exception as e:
            logger.error(f"Gsocket command execution failed: {e}", exc_info=True)
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution failed: {str(e)}",
                "duration_ms": 0
            }

        finally:
            # Clean up temporary secret file
            if secret_file and os.path.exists(secret_file):
                try:
                    os.unlink(secret_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary secret file: {e}")

    @staticmethod
    async def check_host_availability(secret: str, timeout: int = 10, custom_gsrn_server: str = None) -> bool:
        """
        Check if a host is available via gsocket

        Sends a simple echo command to verify the host is listening and responding.

        Args:
            secret: Gsocket secret (encrypted)
            timeout: Ping timeout in seconds
            custom_gsrn_server: Custom GSRN server (e.g., "relay.example.com:443")

        Returns:
            True if host is online and responding, False otherwise
        """
        # Use shorter wait time for availability check
        result = await GsocketService.execute_command(
            secret=secret,
            command="echo 'pong'",
            timeout=timeout,
            wait_time=timeout,  # Wait same time as timeout for quick check
            custom_gsrn_server=custom_gsrn_server
        )

        # Host is available if:
        # 1. Command executed successfully (exit_code 0)
        # 2. We got our expected output
        # 3. No connection errors in stderr
        is_available = (
            result["exit_code"] == 0 and
            "pong" in result["stdout"] and
            "Connection failed" not in result["stderr"] and
            "not reachable" not in result["stderr"].lower()
        )

        if not is_available:
            logger.debug(
                f"Host availability check failed: "
                f"exit_code={result['exit_code']}, "
                f"stderr_preview={result['stderr'][:100]}"
            )

        return is_available

    @staticmethod
    def generate_secret() -> Optional[str]:
        """
        Generate a cryptographically strong secret using gs-netcat -g

        This uses gsocket's built-in secure random password generator.

        Returns:
            Generated secret string, or None if gs-netcat is not available
        """
        try:
            import subprocess

            result = subprocess.run(
                ["gs-netcat", "-g"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                secret = result.stdout.strip()
                logger.info("Generated new secure gsocket secret")
                return secret
            else:
                logger.error(f"Failed to generate secret: {result.stderr}")
                return None

        except FileNotFoundError:
            logger.error("gs-netcat not found. Please install gsocket: https://github.com/hackerschoice/gsocket")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Timeout while generating secret")
            return None
        except Exception as e:
            logger.error(f"Error generating secret: {e}", exc_info=True)
            return None

    @staticmethod
    async def test_connection(secret: str, wait_time: int = 5, custom_gsrn_server: str = None) -> Dict[str, any]:
        """
        Test connection to a host without executing commands

        Uses gs-netcat -t flag to only check if peer is listening.

        Args:
            secret: Gsocket secret (encrypted)
            wait_time: Time to wait for listener
            custom_gsrn_server: Custom GSRN server (e.g., "relay.example.com:443")

        Returns:
            Dict with is_listening (bool) and message (str)
        """
        try:
            decrypted_secret = crypto_service.decrypt(secret)
        except Exception as e:
            return {
                "is_listening": False,
                "message": f"Failed to decrypt secret: {e}"
            }

        secret_file = None
        try:
            # Write secret to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gs') as f:
                f.write(decrypted_secret)
                secret_file = f.name

            os.chmod(secret_file, 0o600)

            # Prepare environment variables for custom GSRN server
            env = os.environ.copy()
            if custom_gsrn_server:
                env['GSOCKET_ARGS'] = f"-s {custom_gsrn_server}"
                logger.debug(f"Testing connection via custom GSRN: {custom_gsrn_server}")
            elif settings.DEFAULT_GSRN_SERVER:
                env['GSOCKET_ARGS'] = f"-s {settings.DEFAULT_GSRN_SERVER}"

            # Use -t flag to test if peer is listening
            process = await asyncio.create_subprocess_exec(
                "gs-netcat", "-k", secret_file, "-t",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=wait_time + 2
            )

            stderr_text = stderr.decode('utf-8', errors='replace')

            # Check if listener is available
            is_listening = process.returncode == 0

            if is_listening:
                message = "Host is listening and available"
            else:
                message = f"Host not listening or not reachable: {stderr_text[:100]}"

            return {
                "is_listening": is_listening,
                "message": message
            }

        except asyncio.TimeoutError:
            return {
                "is_listening": False,
                "message": f"Connection test timed out after {wait_time}s"
            }
        except Exception as e:
            return {
                "is_listening": False,
                "message": f"Test failed: {str(e)}"
            }
        finally:
            if secret_file and os.path.exists(secret_file):
                try:
                    os.unlink(secret_file)
                except:
                    pass


# Singleton instance
gsocket_service = GsocketService()
