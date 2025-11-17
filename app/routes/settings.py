"""Settings management routes"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.user import User
from app.models.settings import Settings
from app.utils.auth import get_current_user
from app.services.settings_service import settings_service
from app.services.logger_service import logger_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    """Schema for updating a setting"""
    value: Any = Field(..., description="New value for the setting")


@router.get("")
def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all application settings"""
    return settings_service.get_all(db)


@router.get("/category/{category}")
def get_settings_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get settings by category"""
    return settings_service.get_by_category(category, db)


@router.get("/{key}")
def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific setting by key"""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    return {
        "key": setting.key,
        "value": setting.get_typed_value(),
        "value_type": setting.value_type,
        "category": setting.category,
        "description": setting.description
    }


@router.put("/{key}")
def update_setting(
    key: str,
    setting_update: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a setting value"""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    # Validate value type
    try:
        if setting.value_type == "int":
            value = int(setting_update.value)
        elif setting.value_type == "float":
            value = float(setting_update.value)
        elif setting.value_type == "bool":
            if isinstance(setting_update.value, bool):
                value = setting_update.value
            else:
                value = str(setting_update.value).lower() in ('true', '1', 'yes')
        else:
            value = str(setting_update.value)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value type. Expected {setting.value_type}: {str(e)}"
        )

    # Update setting
    old_value = setting.get_typed_value()
    setting.set_typed_value(value)
    db.commit()

    # Reload settings service cache
    settings_service.reload()

    # Log change
    logger_service.info(
        db,
        f"Setting '{key}' updated: {old_value} -> {value}",
        category="system"
    )

    return {
        "success": True,
        "message": f"Setting '{key}' updated successfully",
        "old_value": old_value,
        "new_value": value
    }


@router.post("/reload")
def reload_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reload settings from database"""
    settings_service.reload()

    logger_service.info(
        db,
        "Settings reloaded from database",
        category="system"
    )

    return {
        "success": True,
        "message": "Settings reloaded successfully"
    }
