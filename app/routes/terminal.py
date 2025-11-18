"""WebSocket terminal for interactive host access"""
import asyncio
import os
import tempfile
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.host import Host
from app.services.crypto_service import crypto_service
from app.config import settings
import logging

router = APIRouter(prefix="/api/terminal", tags=["terminal"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/{host_id}")
async def websocket_terminal(
    websocket: WebSocket,
    host_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for interactive terminal access to a host

    Client connects via WebSocket and sends/receives terminal data.
    Commands are proxied through gs-netcat in interactive mode.
    """
    await websocket.accept()

    try:
        # Get host
        host = db.query(Host).filter(Host.id == host_id).first()
        if not host:
            await websocket.send_json({
                "type": "error",
                "data": f"Host {host_id} not found"
            })
            await websocket.close()
            return

        # Decrypt secret
        try:
            decrypted_secret = crypto_service.decrypt(host.gsocket_secret)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "data": f"Failed to decrypt secret: {e}"
            })
            await websocket.close()
            return

        # Create temporary file for secret
        secret_file = None
        process = None

        try:
            # Write secret to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gs') as f:
                f.write(decrypted_secret)
                secret_file = f.name

            os.chmod(secret_file, 0o600)

            # Build gs-netcat command for interactive session
            # -k: secret from file
            # -i: interactive mode
            # -w: wait for listener
            gs_args = ["gs-netcat", "-k", secret_file, "-i", "-w", "10"]

            # Prepare environment
            env = os.environ.copy()

            # Set GS_HOST if IP address is provided
            if host.ip_address:
                env['GS_HOST'] = host.ip_address
                logger.debug(f"Using GS_HOST: {host.ip_address}")

            # Set custom GSRN server if specified
            if host.custom_gsrn_server:
                env['GSOCKET_ARGS'] = f"-s {host.custom_gsrn_server}"
            elif settings.DEFAULT_GSRN_SERVER:
                env['GSOCKET_ARGS'] = f"-s {settings.DEFAULT_GSRN_SERVER}"

            logger.info(f"Starting interactive terminal session to host {host.hostname}")

            # Start gs-netcat process
            process = await asyncio.create_subprocess_exec(
                *gs_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Send welcome message
            await websocket.send_json({
                "type": "connected",
                "data": f"Connected to {host.hostname}\r\n"
            })

            async def read_stdout():
                """Read from gs-netcat stdout and send to WebSocket"""
                try:
                    while True:
                        data = await process.stdout.read(1024)
                        if not data:
                            break
                        await websocket.send_json({
                            "type": "output",
                            "data": data.decode('utf-8', errors='replace')
                        })
                except Exception as e:
                    logger.error(f"Error reading stdout: {e}")

            async def read_stderr():
                """Read from gs-netcat stderr and send to WebSocket"""
                try:
                    while True:
                        data = await process.stderr.read(1024)
                        if not data:
                            break
                        # Send stderr as info, not error (gs-netcat uses stderr for info messages)
                        await websocket.send_json({
                            "type": "info",
                            "data": data.decode('utf-8', errors='replace')
                        })
                except Exception as e:
                    logger.error(f"Error reading stderr: {e}")

            async def write_stdin():
                """Read from WebSocket and write to gs-netcat stdin"""
                try:
                    while True:
                        message = await websocket.receive_text()
                        if message:
                            # Write to gs-netcat stdin
                            process.stdin.write(message.encode('utf-8'))
                            await process.stdin.drain()
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected")
                except Exception as e:
                    logger.error(f"Error writing to stdin: {e}")

            # Run all tasks concurrently
            await asyncio.gather(
                read_stdout(),
                read_stderr(),
                write_stdin(),
                return_exceptions=True
            )

        finally:
            # Cleanup
            if process and process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass

            if secret_file and os.path.exists(secret_file):
                try:
                    os.unlink(secret_file)
                except:
                    pass

            logger.info(f"Terminal session closed for host {host.hostname}")

    except Exception as e:
        logger.error(f"Terminal session error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": f"Session error: {str(e)}"
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
