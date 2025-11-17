"""Host management routes"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
import csv
import io
from app.database import get_db
from app.models.host import Host
from app.models.user import User
from app.schemas import HostCreate, HostUpdate, HostResponse
from app.utils.auth import get_current_user
from app.utils.validators import validate_hostname, validate_ip_address
from app.services.crypto_service import crypto_service
from app.services.logger_service import logger_service

router = APIRouter(prefix="/api/hosts", tags=["hosts"])


@router.get("", response_model=List[HostResponse])
def list_hosts(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by hostname or IP"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all hosts with optional filtering"""

    query = db.query(Host)

    # Apply status filter
    if status_filter:
        query = query.filter(Host.status == status_filter)

    # Apply search
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Host.hostname.like(search_pattern),
                Host.ip_address.like(search_pattern)
            )
        )

    hosts = query.order_by(Host.created_at.desc()).all()
    return hosts


@router.post("", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
def create_host(
    host_data: HostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new host"""

    # Validate hostname
    is_valid, error = validate_hostname(host_data.hostname)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Validate IP if provided
    if host_data.ip_address:
        is_valid, error = validate_ip_address(host_data.ip_address)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Check if hostname already exists
    existing = db.query(Host).filter(Host.hostname == host_data.hostname).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hostname already exists"
        )

    # Encrypt gsocket secret
    encrypted_secret = crypto_service.encrypt(host_data.gsocket_secret)

    # Create host
    host = Host(
        hostname=host_data.hostname,
        ip_address=host_data.ip_address,
        gsocket_secret=encrypted_secret,
        custom_gsrn_server=host_data.custom_gsrn_server,
        description=host_data.description,
        notes=host_data.notes,
        tags=host_data.tags
    )

    db.add(host)
    db.commit()
    db.refresh(host)

    logger_service.info(
        db,
        f"Host created: {host.hostname}",
        category="system",
        host_id=host.id
    )

    return host


@router.get("/{host_id}", response_model=HostResponse)
def get_host(
    host_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get host details by ID"""

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    return host


@router.put("/{host_id}", response_model=HostResponse)
def update_host(
    host_id: int,
    host_data: HostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update host"""

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    # Validate hostname if provided
    if host_data.hostname:
        is_valid, error = validate_hostname(host_data.hostname)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

        # Check uniqueness
        existing = db.query(Host).filter(
            Host.hostname == host_data.hostname,
            Host.id != host_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hostname already exists"
            )

    # Validate IP if provided
    if host_data.ip_address:
        is_valid, error = validate_ip_address(host_data.ip_address)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Update fields
    if host_data.hostname:
        host.hostname = host_data.hostname
    if host_data.ip_address is not None:
        host.ip_address = host_data.ip_address
    if host_data.gsocket_secret:
        host.gsocket_secret = crypto_service.encrypt(host_data.gsocket_secret)
    if host_data.custom_gsrn_server is not None:
        host.custom_gsrn_server = host_data.custom_gsrn_server
    if host_data.description is not None:
        host.description = host_data.description
    if host_data.notes is not None:
        host.notes = host_data.notes
    if host_data.tags is not None:
        host.tags = host_data.tags
    if host_data.status:
        host.status = host_data.status

    db.commit()
    db.refresh(host)

    logger_service.info(
        db,
        f"Host updated: {host.hostname}",
        category="system",
        host_id=host.id
    )

    return host


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_host(
    host_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete host"""

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    hostname = host.hostname
    db.delete(host)
    db.commit()

    logger_service.info(
        db,
        f"Host deleted: {hostname}",
        category="system"
    )

    return None


@router.get("/{host_id}/status")
def check_host_status(
    host_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check host availability status"""

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    return {
        "host_id": host.id,
        "hostname": host.hostname,
        "status": host.status,
        "last_seen": host.last_seen
    }


@router.get("/utils/generate-secret")
def generate_secret(
    current_user: User = Depends(get_current_user)
):
    """
    Generate a cryptographically strong gsocket secret

    Uses gs-netcat -g to generate a secure random password.
    Requires gs-netcat to be installed on the server.

    Returns:
        Dict with generated secret or error message
    """
    from app.services.gsocket_service import gsocket_service

    secret = gsocket_service.generate_secret()

    if secret:
        return {
            "success": True,
            "secret": secret,
            "message": "Secure secret generated successfully"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate secret. Ensure gs-netcat is installed on the server."
        )


@router.post("/{host_id}/test-connection")
async def test_host_connection(
    host_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test gsocket connection to a host

    Uses gs-netcat -t flag to check if the host is listening
    without executing any commands.

    Returns:
        Dict with connection test results
    """
    from app.services.gsocket_service import gsocket_service

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    result = await gsocket_service.test_connection(
        secret=host.gsocket_secret,
        wait_time=5,
        custom_gsrn_server=host.custom_gsrn_server
    )

    logger_service.info(
        db,
        f"Connection test for {host.hostname}: {result['message']}",
        category="connection",
        host_id=host.id
    )

    return {
        "host_id": host.id,
        "hostname": host.hostname,
        "is_listening": result["is_listening"],
        "message": result["message"]
    }


@router.post("/import/csv")
async def import_hosts_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import hosts from CSV file

    CSV Format (with header):
    hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags

    Required columns: hostname, gsocket_secret
    Optional columns: ip_address, custom_gsrn_server, description, tags

    Example:
    hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags
    web-server-01,192.168.1.10,secret123,,Production web server,prod;web
    db-server-01,,secret456,relay.example.com:443,Database server,prod;db
    """

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    try:
        # Read file content
        content = await file.read()
        csv_data = content.decode('utf-8')

        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_data))

        # Validate required columns
        required_columns = {'hostname', 'gsocket_secret'}
        if not required_columns.issubset(csv_reader.fieldnames):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV must contain columns: {', '.join(required_columns)}"
            )

        results = {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            results["total"] += 1

            # Skip empty rows
            if not row.get('hostname') or not row.get('gsocket_secret'):
                results["skipped"] += 1
                results["errors"].append(f"Row {row_num}: Missing required fields")
                continue

            hostname = row['hostname'].strip()
            gsocket_secret = row['gsocket_secret'].strip()

            # Validate hostname
            is_valid, error = validate_hostname(hostname)
            if not is_valid:
                results["skipped"] += 1
                results["errors"].append(f"Row {row_num} ({hostname}): {error}")
                continue

            # Check if host already exists
            existing = db.query(Host).filter(Host.hostname == hostname).first()
            if existing:
                results["skipped"] += 1
                results["errors"].append(f"Row {row_num} ({hostname}): Hostname already exists")
                continue

            # Get optional fields
            ip_address = row.get('ip_address', '').strip() or None
            custom_gsrn_server = row.get('custom_gsrn_server', '').strip() or None
            description = row.get('description', '').strip() or None
            tags = row.get('tags', '').strip() or None

            # Validate IP if provided
            if ip_address:
                is_valid, error = validate_ip_address(ip_address)
                if not is_valid:
                    results["skipped"] += 1
                    results["errors"].append(f"Row {row_num} ({hostname}): {error}")
                    continue

            try:
                # Encrypt secret
                encrypted_secret = crypto_service.encrypt(gsocket_secret)

                # Create host
                host = Host(
                    hostname=hostname,
                    ip_address=ip_address,
                    gsocket_secret=encrypted_secret,
                    custom_gsrn_server=custom_gsrn_server,
                    description=description,
                    tags=tags
                )

                db.add(host)
                results["imported"] += 1

            except Exception as e:
                results["skipped"] += 1
                results["errors"].append(f"Row {row_num} ({hostname}): {str(e)}")

        # Commit all changes
        db.commit()

        # Log import
        logger_service.info(
            db,
            f"CSV import: {results['imported']} hosts imported, {results['skipped']} skipped",
            category="system"
        )

        return {
            "success": True,
            "message": f"Import completed: {results['imported']} imported, {results['skipped']} skipped",
            "results": results
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file encoding. File must be UTF-8"
        )
    except csv.Error as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV parsing error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
