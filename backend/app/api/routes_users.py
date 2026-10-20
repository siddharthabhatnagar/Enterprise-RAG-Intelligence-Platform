from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.core.security import DEMO_USERS, User

router = APIRouter(prefix="/api/users", tags=["Users & RBAC"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_available_users():
    """Lists pre-configured enterprise users for role-switching in the UI."""
    user_list = []
    for key, u in DEMO_USERS.items():
        user_list.append({
            "key": key,
            "user_id": u.user_id,
            "name": u.name,
            "role": u.role.value,
            "department": u.department.value,
            "max_clearance": u.max_clearance.value,
            "allowed_clearance_levels": u.allowed_clearance_levels
        })
    return user_list

@router.get("/{user_key}", response_model=Dict[str, Any])
async def get_user_profile(user_key: str):
    """Retrieves an individual user profile and clearance definition."""
    user = DEMO_USERS.get(user_key.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User key '{user_key}' not found."
        )
    return {
        "key": user_key.lower(),
        "user_id": user.user_id,
        "name": user.name,
        "role": user.role.value,
        "department": user.department.value,
        "max_clearance": user.max_clearance.value,
        "allowed_clearance_levels": user.allowed_clearance_levels
    }
