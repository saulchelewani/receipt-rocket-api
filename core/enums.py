from enum import Enum


class Scope(str, Enum):
    TENANT = "tenant"
    GLOBAL = "global"
    ALL = "all"

class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    GLOBAL_ADMIN = "global_admin"