from enum import Enum


class Scope(int, Enum):
    TENANT = 2002
    GLOBAL = 2001
    ALL = 2003


class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    GLOBAL_ADMIN = "global_admin"


class StatusEnum(int, Enum):
    ACTIVE = 1001
    SUSPENDED = 1003
    DELETED = 1004
    PENDING = 1005
    CHANGE_PASSWORD = 1002


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
