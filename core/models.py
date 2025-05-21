import uuid

from sqlalchemy import Column, String, ForeignKey, Boolean, UUID, Table
from sqlalchemy.orm import Mapped, relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True, unique=True,
                              nullable=False)
    email: Mapped[str] = Column(String, unique=True, index=True)
    name: Mapped[str] = Column(String, nullable=True)
    hashed_password: Mapped[str] = Column(String)
    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    role_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    scope: Mapped[str] = Column(String, nullable=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True, unique=True,
                              nullable=False)
    name: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(String, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
    routes: Mapped[list["Route"]] = relationship("Route", secondary="role_route_association", back_populates="roles")


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[UUID] = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True, unique=True,
                              nullable=False)
    name: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    code: Mapped[str] = Column(String, unique=True, index=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    profile: Mapped["Profile"] = relationship("Profile", back_populates="tenant")

class Route(Base):
    __tablename__ = "routes"

    id: Mapped[UUID] = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True, unique=True,
                              nullable=False)
    path: Mapped[str] = Column(String, unique=False, index=True)  # The route path (e.g., "/tasks/")
    method: Mapped[str] = Column(String)  # The HTTP method (e.g., "GET", "POST")
    action: Mapped[str] = Column(String, nullable=False)  # (e.g. delete task)
    name: Mapped[str] = Column(String, nullable=True)

    roles: Mapped[list["Role"]] = relationship("Role", secondary="role_route_association", back_populates="routes")

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True, unique=True,
                              nullable=False)
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