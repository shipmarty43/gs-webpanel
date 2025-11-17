"""Script management routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.script import Script
from app.models.user import User
from app.schemas import ScriptCreate, ScriptUpdate, ScriptResponse
from app.utils.auth import get_current_user
from app.services.logger_service import logger_service

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("", response_model=List[ScriptResponse])
def list_scripts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all scripts"""

    scripts = db.query(Script).order_by(Script.created_at.desc()).all()
    return scripts


@router.post("", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
def create_script(
    script_data: ScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new script"""

    # Check if name already exists
    existing = db.query(Script).filter(Script.name == script_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Script name already exists"
        )

    # Create script
    script = Script(
        name=script_data.name,
        description=script_data.description,
        content=script_data.content,
        timeout=script_data.timeout,
        created_by=current_user.id
    )

    db.add(script)
    db.commit()
    db.refresh(script)

    logger_service.info(
        db,
        f"Script created: {script.name}",
        category="system"
    )

    return script


@router.get("/{script_id}", response_model=ScriptResponse)
def get_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get script by ID"""

    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")

    return script


@router.put("/{script_id}", response_model=ScriptResponse)
def update_script(
    script_id: int,
    script_data: ScriptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update script"""

    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")

    # Check name uniqueness if updating name
    if script_data.name and script_data.name != script.name:
        existing = db.query(Script).filter(
            Script.name == script_data.name,
            Script.id != script_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Script name already exists"
            )

    # Update fields
    if script_data.name:
        script.name = script_data.name
    if script_data.description is not None:
        script.description = script_data.description
    if script_data.content:
        script.content = script_data.content
    if script_data.timeout:
        script.timeout = script_data.timeout

    db.commit()
    db.refresh(script)

    logger_service.info(
        db,
        f"Script updated: {script.name}",
        category="system"
    )

    return script


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete script"""

    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")

    script_name = script.name
    db.delete(script)
    db.commit()

    logger_service.info(
        db,
        f"Script deleted: {script_name}",
        category="system"
    )

    return None
