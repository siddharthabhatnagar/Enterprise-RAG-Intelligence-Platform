from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ClearanceLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class Department(str, Enum):
    ALL = "all"
    GENERAL = "general"
    ENGINEERING = "engineering"
    HR = "hr"
    FINANCE = "finance"
    LEGAL = "legal"
    EXECUTIVE = "executive"

class Role(str, Enum):
    ADMIN = "admin"
    EXECUTIVE = "executive"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"

# Hierarchy of clearance levels
CLEARANCE_HIERARCHY = {
    ClearanceLevel.PUBLIC: 1,
    ClearanceLevel.INTERNAL: 2,
    ClearanceLevel.CONFIDENTIAL: 3,
    ClearanceLevel.RESTRICTED: 4,
}

# Role to maximum allowed clearance level
ROLE_MAX_CLEARANCE = {
    Role.ADMIN: ClearanceLevel.RESTRICTED,
    Role.EXECUTIVE: ClearanceLevel.RESTRICTED,
    Role.MANAGER: ClearanceLevel.CONFIDENTIAL,
    Role.EMPLOYEE: ClearanceLevel.INTERNAL,
    Role.CONTRACTOR: ClearanceLevel.PUBLIC,
}

class User(BaseModel):
    user_id: str
    name: str
    role: Role
    department: Department
    custom_clearance: Optional[ClearanceLevel] = None

    @property
    def max_clearance(self) -> ClearanceLevel:
        if self.custom_clearance:
            return self.custom_clearance
        return ROLE_MAX_CLEARANCE.get(self.role, ClearanceLevel.PUBLIC)

    @property
    def allowed_clearance_levels(self) -> List[str]:
        max_rank = CLEARANCE_HIERARCHY[self.max_clearance]
        return [
            level.value for level, rank in CLEARANCE_HIERARCHY.items()
            if rank <= max_rank
        ]

# Default demo enterprise users for instant testing in UI
DEMO_USERS: Dict[str, User] = {
    "admin": User(
        user_id="usr_admin",
        name="Elena Vance (Chief Security & IT Admin)",
        role=Role.ADMIN,
        department=Department.EXECUTIVE,
    ),
    "exec": User(
        user_id="usr_exec",
        name="Marcus Sterling (CEO / Executive)",
        role=Role.EXECUTIVE,
        department=Department.EXECUTIVE,
    ),
    "eng_manager": User(
        user_id="usr_eng_mgr",
        name="Alex Rivera (Engineering Manager)",
        role=Role.MANAGER,
        department=Department.ENGINEERING,
    ),
    "eng_dev": User(
        user_id="usr_eng_dev",
        name="Chloe Zhang (Software Engineer)",
        role=Role.EMPLOYEE,
        department=Department.ENGINEERING,
    ),
    "hr_director": User(
        user_id="usr_hr_dir",
        name="Sarah Jenkins (HR Director)",
        role=Role.MANAGER,
        department=Department.HR,
    ),
    "finance_controller": User(
        user_id="usr_fin_ctrl",
        name="Raj Patel (Finance Controller)",
        role=Role.MANAGER,
        department=Department.FINANCE,
    ),
    "contractor": User(
        user_id="usr_contractor",
        name="David Miller (External Contractor)",
        role=Role.CONTRACTOR,
        department=Department.ENGINEERING,
    ),
}

def can_access_chunk(user: User, chunk_metadata: Dict[str, Any]) -> bool:
    """
    Evaluates whether a user is authorized to read a specific document chunk.
    Enforces Document-Level Role-Based Access Control (RBAC):
    1. Superusers (Admin / Executive) can access all departmental docs up to their clearance.
    2. Document clearance level must be <= user's maximum clearance.
    3. Document department must match user's department OR be 'all' / 'general'
       (Unless user is Admin/Exec).
    """
    # 1. Superuser override
    if user.role in (Role.ADMIN, Role.EXECUTIVE):
        # Admins & Execs can access any department, limited only by clearance
        doc_clearance = chunk_metadata.get("access_level", ClearanceLevel.PUBLIC.value).lower()
        return doc_clearance in user.allowed_clearance_levels

    # 2. Check Clearance Level
    doc_clearance = chunk_metadata.get("access_level", ClearanceLevel.PUBLIC.value).lower()
    if doc_clearance not in user.allowed_clearance_levels:
        return False

    # 3. Check Departmental boundary
    doc_dept = chunk_metadata.get("department", Department.GENERAL.value).lower()
    user_dept = user.department.value.lower()

    if doc_dept in [Department.ALL.value, Department.GENERAL.value]:
        return True

    return doc_dept == user_dept
