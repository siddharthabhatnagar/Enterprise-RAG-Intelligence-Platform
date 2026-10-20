from pydantic import BaseModel
from typing import List, Optional
from backend.app.core.security import Role, Department, ClearanceLevel

class UserSchema(BaseModel):
    user_id: str
    name: str
    role: Role
    department: Department
    max_clearance: ClearanceLevel
    allowed_clearance_levels: List[str]

class UserSwitchRequest(BaseModel):
    user_id: str
