"""Gsocket service for communication with remote hosts - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
import asyncio
import os
import tempfile
from typing import Dict, Optional
from app.config import settings
from app.services.crypto_service import crypto_service
import logging

logger = logging.getLogger(__name__)


class GsocketError(Exception):
    """Базовая ошибка gsocket"""
    pass


class GsocketConnectionError(GsocketError):
    """Не удалось подключиться к хосту"""
    pass


class GsocketAuthenticationError(GsocketError):
    """Неверный секретный ключ"""
    pass


class GsocketTimeoutError(GsocketError):
    """Таймаут выполнения команды"""
    pass


class GsocketService:
    """Service for interacting with hosts via gsocket

    ВАЖНО: На целевых хостах должен быть запущен:
    gs-netcat -l -s <SECRET> -e /bin/bash -D
    """

    @staticmethod
    async def execute_command(
        secret: str,
        command: str,
        timeout: int = None,
        use_interactive: bool = False
    ) -> Dict[str, any]:
        """
        Execute a command on a remote host via gsocket

        АРХИТЕКТУРА:
        1. Целевой хост запущен в режиме listen: gs-netcat -l -s <SECRET> -e /bin/bash
        2. Панель подключается как клиент: gs-netcat -s <SECRET>
        3. Команда отправляется через stdin
        4. Результат получается через stdout/stderr

        Args:
            secret: Gsocket secret (encrypted in database)
            command: Command to execute
            timeout: Command timeout in seconds
            use_interactive: Use interactive mode (-i flag)

        Returns:
            Dict with exit_code, stdout, stderr, duration_ms
        """
        if timeout is None:
            timeout = settings.DEFAULT_TASK_TIMEOUT

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

        # БЕЗОПАСНОСТЬ: Используем переменную окружения вместо аргумента командной строки
        # Согласно документации: "Using -s is not secure" в аргументах
        env = os.environ.copy()
        env['GSOCKET_ARGS'] = f"-s {decrypted_secret}"

        # Добавляем -i для интерактивного режима если нужно
        if use_interactive:
            env['GSOCKET_ARGS'] += " -i"

        import time
        start_time = time.time()

        try:
            # Подключаемся к хосту (хост должен быть в режиме listen!)
            process = await asyncio.create_subprocess_exec(
                "gs-netcat",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Отправляем команду и добавляем exit для завершения соединения
            command_with_exit = f"{command}\nexit\n"

            # Send command and get output
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=command_with_exit.encode()),
                timeout=timeout
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Проверяем stderr на специфичные ошибки gsocket
            stderr_text = stderr.decode('utf-8', errors='replace')
            if "SRP authentication failed" in stderr_text or "wrong password" in stderr_text.lower():
                raise GsocketAuthenticationError("Invalid gsocket secret")
            elif "connection" in stderr_text.lower() and "failed" in stderr_text.lower():
                raise GsocketConnectionError("Failed to connect to host")

            return {
                "exit_code": process.returncode if process.returncode is not None else 0,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr_text,
                "duration_ms": duration_ms
            }

        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except:
                pass

            logger.warning(f"Command execution timed out after {timeout}s")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command execution timed out after {timeout} seconds",
                "duration_ms": timeout * 1000
            }

        except GsocketAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Authentication failed: Invalid secret key",
                "duration_ms": int((time.time() - start_time) * 1000)
            }

        except GsocketConnectionError as e:
            logger.error(f"Connection failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Connection failed: Host may be offline or not configured",
                "duration_ms": int((time.time() - start_time) * 1000)
            }

        except Exception as e:
            logger.error(f"Gsocket command execution failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution failed: {str(e)}",
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    @staticmethod
    async def execute_command_with_file_secret(
        secret: str,
        command: str,
        timeout: int = None
    ) -> Dict[str, any]:
        """
        Alternative method: Execute command using temporary file for secret

        Более безопасный метод с использованием -k флага вместо переменной окружения

        Args:
            secret: Gsocket secret (encrypted)
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Dict with exit_code, stdout, stderr, duration_ms
        """
        if timeout is None:
            timeout = settings.DEFAULT_TASK_TIMEOUT

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

        # Create temporary file for secret
        secret_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.key') as f:
                f.write(decrypted_secret)
                secret_file = f.name

            # Restrict file permissions
            os.chmod(secret_file, 0o600)

            import time
            start_time = time.time()

            # Execute with -k flag
            process = await asyncio.create_subprocess_exec(
                "gs-netcat",
                "-k", secret_file,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send command
            command_with_exit = f"{command}\nexit\n"
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=command_with_exit.encode()),
                timeout=timeout
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "exit_code": process.returncode if process.returncode is not None else 0,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "duration_ms": duration_ms
            }

        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except:
                pass

            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command execution timed out after {timeout} seconds",
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

        finally:
            # Clean up temporary secret file
            if secret_file and os.path.exists(secret_file):
                try:
                    os.unlink(secret_file)
                except:
                    pass

    @staticmethod
    async def check_host_availability(secret: str, timeout: int = 10) -> bool:
        """
        Check if a host is available via gsocket

        ВАЖНО: Хост должен быть настроен с gs-netcat -l -e /bin/bash

        Args:
            secret: Gsocket secret (encrypted)
            timeout: Ping timeout in seconds

        Returns:
            True if host is online, False otherwise
        """
        # Simple echo test
        result = await GsocketService.execute_command(
            secret=secret,
            command="echo 'pong'",
            timeout=timeout
        )

        # Считаем хост доступным если команда выполнилась успешно
        # и в выводе есть наше контрольное слово
        is_available = (
            result["exit_code"] == 0 and
            "pong" in result["stdout"] and
            "Authentication failed" not in result["stderr"] and
            "Connection failed" not in result["stderr"]
        )

        if not is_available:
            logger.debug(f"Host check failed: exit_code={result['exit_code']}, stderr={result['stderr']}")

        return is_available

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a cryptographically strong secret using gs-netcat

        Выполняет: gs-netcat -g

        Returns:
            Generated secret string or None if failed
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
                # gs-netcat -g выводит секрет в stdout
                secret = result.stdout.strip()
                return secret
            else:
                logger.error(f"Failed to generate secret: {result.stderr}")
                return None

        except FileNotFoundError:
            logger.error("gs-netcat not found. Please install gsocket.")
            return None
        except Exception as e:
            logger.error(f"Error generating secret: {e}")
            return None


# Singleton instance
gsocket_service = GsocketService()
