import uuid

from sqlalchemy import Column, String, ForeignKey, UUID, Table, Float, DateTime, func, Integer, JSON, Boolean
from sqlalchemy.orm import Mapped, relationship, declared_attr

from core.database import Base


class Model(Base):
    __abstract__ = True

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"

    def __str__(self):
        return f"<{self.__class__.__name__} {self.id}>"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @declared_attr
    def id(self):
        return Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)

    @declared_attr
    def created_at(self):
        return Column(DateTime, default=func.now())

    @declared_attr
    def updated_at(self):
        return Column(DateTime, default=func.now(), onupdate=func.now())


class User(Model):
    __tablename__ = "users"

    email: Mapped[str] = Column(String, unique=True, index=True)
    name: Mapped[str] = Column(String, nullable=True)
    hashed_password: Mapped[str] = Column(String, nullable=True)
    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    role_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    scope: Mapped[str] = Column(String, nullable=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")


class Role(Model):
    __tablename__ = "roles"

    name: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(String, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
    routes: Mapped[list["Route"]] = relationship("Route", secondary="role_route_association", back_populates="roles")


class Tenant(Model):
    __tablename__ = "tenants"

    name: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    code: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = Column(String, nullable=True)
    phone_number: Mapped[str] = Column(String, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    profile: Mapped["Profile"] = relationship("Profile", back_populates="tenant")
    terminals: Mapped[list["Terminal"]] = relationship("Terminal", back_populates="tenant")


class Route(Model):
    __tablename__ = "routes"

    path: Mapped[str] = Column(String, unique=False, index=True)  # The route path (e.g., "/tasks/")
    method: Mapped[str] = Column(String)  # The HTTP method (e.g., "GET", "POST")
    action: Mapped[str] = Column(String, nullable=False)  # (e.g. delete task)
    name: Mapped[str] = Column(String, nullable=True)

    roles: Mapped[list["Role"]] = relationship("Role", secondary="role_route_association", back_populates="routes")


class Profile(Model):
    __tablename__ = "profiles"

    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tin: Mapped[str] = Column(String, nullable=True)
    version: Mapped[str] = Column(String, nullable=True)
    vat_registered: Mapped[bool] = Column(Boolean, nullable=True)
    activated_tax_rate_ids: Mapped[list[str]] = Column(JSON, nullable=True)
    tax_office_code: Mapped[str] = Column(String, nullable=True)
    tax_office_name: Mapped[str] = Column(String, nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="profile")


role_route_association = Table(
    "role_route_association",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("route_id", UUID(as_uuid=True), ForeignKey("routes.id"), primary_key=True),
)


class Terminal(Model):
    __tablename__ = "terminals"

    terminal_id: Mapped[str] = Column(String)
    secret_key: Mapped[str] = Column(String)
    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    confirmed_at: Mapped[DateTime] = Column(DateTime, nullable=True)
    trading_name: Mapped[str] = Column(String, nullable=True)
    email: Mapped[str] = Column(String, nullable=True)
    phone_number: Mapped[str] = Column(String)
    label: Mapped[str] = Column(String, nullable=True)
    version: Mapped[str] = Column(Integer, nullable=True)
    address_lines: Mapped[list[str]] = Column(JSON, nullable=True)
    offline_limit_hours: Mapped[int] = Column(Integer, nullable=True)
    offline_limit_amount: Mapped[float] = Column(Float, nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="terminals")


class TaxRate(Model):
    __tablename__ = "tax_rates"

    rate_id: Mapped[str] = Column(String)
    name: Mapped[str] = Column(String)
    rate: Mapped[float | None] = Column(Float, nullable=True)
    ordinal: Mapped[int] = Column(Integer)
    charge_mode: Mapped[str] = Column(String)
