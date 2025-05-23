import uuid

from sqlalchemy import Column, String, ForeignKey, UUID, Table, Float, DateTime, func
from sqlalchemy.orm import Mapped, relationship, declared_attr

from core.database import Base


class TimestampMixin:
    @declared_attr
    def id(self):
        return Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)

    @declared_attr
    def created_at(self):
        return Column(DateTime, default=func.now())

    @declared_attr
    def updated_at(self):
        return Column(DateTime, default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = Column(String, unique=True, index=True)
    name: Mapped[str] = Column(String, nullable=True)
    hashed_password: Mapped[str] = Column(String)
    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    role_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    scope: Mapped[str] = Column(String, nullable=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(String, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
    routes: Mapped[list["Route"]] = relationship("Route", secondary="role_route_association", back_populates="roles")


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    code: Mapped[str] = Column(String, unique=True, index=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    profile: Mapped["Profile"] = relationship("Profile", back_populates="tenant")
    terminals: Mapped[list["Terminal"]] = relationship("Terminal", back_populates="tenant")


class Route(Base, TimestampMixin):
    __tablename__ = "routes"

    path: Mapped[str] = Column(String, unique=False, index=True)  # The route path (e.g., "/tasks/")
    method: Mapped[str] = Column(String)  # The HTTP method (e.g., "GET", "POST")
    action: Mapped[str] = Column(String, nullable=False)  # (e.g. delete task)
    name: Mapped[str] = Column(String, nullable=True)

    roles: Mapped[list["Role"]] = relationship("Role", secondary="role_route_association", back_populates="routes")


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    business_name: Mapped[str] = Column(String, nullable=True)
    address: Mapped[str] = Column(String, nullable=True)
    phone: Mapped[str] = Column(String, nullable=True)
    email: Mapped[str] = Column(String, nullable=True)
    website: Mapped[str] = Column(String, nullable=True)
    tin: Mapped[str] = Column(String, nullable=True)
    logo: Mapped[str] = Column(String, nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="profile")


role_route_association = Table(
    "role_route_association",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("route_id", UUID(as_uuid=True), ForeignKey("routes.id"), primary_key=True),
)


class Terminal(Base, TimestampMixin):
    __tablename__ = "terminals"

    terminal_id: Mapped[str] = Column(String)
    secret_key: Mapped[str] = Column(String)
    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    confirmed_at: Mapped[DateTime] = Column(DateTime, nullable=True)

    configurations: Mapped["TerminalConfiguration"] = relationship("TerminalConfiguration", back_populates="terminal",
                                                                   uselist=False)
    tax_rates: Mapped[list["TaxRate"]] = relationship("TaxRate", back_populates="terminal")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="terminals")


class TerminalConfiguration(Base, TimestampMixin):
    __tablename__ = "terminal_configurations"

    terminal_id: Mapped[str] = Column(String, ForeignKey("terminals.terminal_id"))
    label: Mapped[str] = Column(String)
    email: Mapped[str] = Column(String)
    phone: Mapped[str] = Column(String)
    trading_name: Mapped[str] = Column(String)

    terminal: Mapped["Terminal"] = relationship("Terminal", back_populates="configurations")


class TaxRate(Base, TimestampMixin):
    __tablename__ = "tax_rates"

    rate_id: Mapped[str] = Column(String)
    name: Mapped[str] = Column(String)
    rate: Mapped[float] = Column(Float)
    charge_mode: Mapped[str] = Column(String)
    terminal_id: Mapped[str] = Column(String, ForeignKey("terminals.terminal_id"))

    terminal: Mapped["Terminal"] = relationship("Terminal", back_populates="tax_rates")
