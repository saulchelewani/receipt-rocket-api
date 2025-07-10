import uuid
from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, UUID, Table, Float, DateTime, func, Integer, JSON, Boolean, Text, \
    Enum
from sqlalchemy.orm import Mapped, relationship, declared_attr

from core.database import Base
from core.enums import BillingCycle, PaymentStatus


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
    phone_number: Mapped[str] = Column(String, nullable=False)
    hashed_password: Mapped[str] = Column(String, nullable=True)
    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    role_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    scope: Mapped[int] = Column(Integer, nullable=True)
    status: Mapped[int] = Column(Integer, nullable=True, default=1001)
    last_login: Mapped[DateTime] = Column(DateTime, nullable=True)
    last_logout: Mapped[DateTime] = Column(DateTime, nullable=True)
    refresh_token_version = Column(Integer, default=0)

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
    tin: Mapped[str] = Column(String, nullable=True)
    config_version: Mapped[float] = Column(Integer, nullable=True)
    taxpayer_id: Mapped[int] = Column(Integer, nullable=True)
    vat_registered: Mapped[bool] = Column(Boolean, nullable=True)
    activated_tax_rate_ids: Mapped[list[str]] = Column(JSON, nullable=True)
    tax_office_code: Mapped[str] = Column(String, nullable=True)
    tax_office_name: Mapped[str] = Column(String, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    profile: Mapped["Profile"] = relationship("Profile", back_populates="tenant")
    terminals: Mapped[list["Terminal"]] = relationship("Terminal", back_populates="tenant")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="tenant")
    offline_transactions: Mapped[list["OfflineTransaction"]] = relationship(
        "OfflineTransaction", back_populates="tenant"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="tenant")


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
    position: Mapped[int] = Column(Integer, nullable=True)
    secret_key: Mapped[str] = Column(String)
    token: Mapped[str] = Column(String, nullable=True)
    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    confirmed_at: Mapped[DateTime] = Column(DateTime, nullable=True)
    trading_name: Mapped[str] = Column(String, nullable=True)
    email: Mapped[str] = Column(String, nullable=True)
    phone_number: Mapped[str] = Column(String)
    label: Mapped[str] = Column(String, nullable=True)
    config_version: Mapped[int] = Column(Integer, nullable=True)
    address_lines: Mapped[list[str]] = Column(JSON, nullable=True)
    offline_limit_hours: Mapped[int] = Column(Integer, nullable=True)
    offline_limit_amount: Mapped[float] = Column(Float, nullable=True)
    device_id: Mapped[str] = Column(String, nullable=True)
    activation_code: Mapped[str] = Column(String, nullable=True)
    site_id: Mapped[str] = Column(String, nullable=False)
    site_name: Mapped[str] = Column(String, nullable=True)
    is_blocked: Mapped[bool] = Column(Boolean, nullable=True)
    blocking_reason: Mapped[str | None] = Column(String, nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="terminals")
    offline_transactions: Mapped[list["OfflineTransaction"]] = relationship(
        "OfflineTransaction", back_populates="terminal"
    )


class Subscription(Model):
    __tablename__ = "subscriptions"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    billing_cycle = Column(Enum(BillingCycle))
    device_limit = Column(Integer)
    price = Column(Float)
    start_date = Column(DateTime, default=datetime.now())
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=False)
    payment = relationship("Payment", back_populates="subscription", uselist=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscriptions")


class Payment(Model):
    __tablename__ = "payments"

    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    proof_url = Column(String)  # Link to uploaded proof (e.g., in S3, local storage)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    admin_id = Column(UUID(as_uuid=True), nullable=True)  # Optionally track who approved

    subscription = relationship("Subscription", back_populates="payment")


class OfflineTransaction(Model):
    __tablename__ = "offline_transactions"

    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    terminal_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("terminals.id"), nullable=False)
    transaction_id: Mapped[str] = Column(String, nullable=False)
    details: Mapped[dict] = Column(JSON, nullable=False)
    submitted_at: Mapped[DateTime] = Column(DateTime, nullable=True)
    status: Mapped[str] = Column(String, nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="offline_transactions")
    terminal: Mapped["Terminal"] = relationship("Terminal", back_populates="offline_transactions")


class TaxRate(Model):
    __tablename__ = "tax_rates"

    rate_id: Mapped[str] = Column(String, nullable=False)
    name: Mapped[str] = Column(String)
    rate: Mapped[float] = Column(Float, nullable=False)
    ordinal: Mapped[int] = Column(Integer)
    charge_mode: Mapped[str] = Column(String)


class Product(Model):
    __tablename__ = "products"

    tenant_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    description: Mapped[str] = Column(String)
    name: Mapped[str] = Column(String)
    unit_price: Mapped[float] = Column(Float, nullable=False)
    quantity: Mapped[int] = Column(Integer, nullable=False)
    unit_of_measure: Mapped[str] = Column(String, nullable=False)
    site_id: Mapped[str] = Column(String, nullable=True)
    expiry_date: Mapped[datetime] = Column(DateTime, nullable=True)
    minimum_stock_level: Mapped[int] = Column(Integer, nullable=True)
    tax_rate_id: Mapped[str] = Column(String, nullable=False)
    is_product: Mapped[bool] = Column(Boolean, nullable=False)
    code: Mapped[str] = Column(String, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="products")


class Item(Model):
    __tablename__ = "items"

    code: Mapped[str] = Column(String, nullable=False)
    name: Mapped[str] = Column(String, nullable=False)
    description: Mapped[str] = Column(String, nullable=True)
    is_product: Mapped[bool] = Column(Boolean, default=True)


class GlobalConfig(Model):
    __tablename__ = "global_config"

    version: Mapped[int] = Column(Integer, nullable=False)


class ApiLog(Model):
    __tablename__ = "api_logs"

    method = Column(String(10))
    url = Column(Text)
    request_headers = Column(Text)
    request_body = Column(Text)
    response_status = Column(Integer)
    response_headers = Column(Text)
    response_body = Column(Text)


class Dictionary(Model):
    __tablename__ = "dictionaries"

    term: Mapped[int] = Column(Integer, nullable=False, index=True)
    definition: Mapped[str] = Column(String, nullable=False)
