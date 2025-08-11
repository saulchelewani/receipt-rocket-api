import json
import os
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
import rstr
from sqlalchemy import create_engine, StaticPool, insert
from sqlalchemy.orm import sessionmaker, Session
from starlette.testclient import TestClient

from apps.main import app
from core.auth import create_access_token
from core.database import Base, get_db
from core.enums import RoleEnum, Scope, StatusEnum
from core.models import Tenant, Role, User, Terminal, Profile, role_route_association, Route, Product, Item, TaxRate, \
    GlobalConfig, OfflineTransaction, Dictionary
from core.settings import settings
from core.utils.helpers import get_sequence_number, get_random_number

# Use an in-memory SQLite database for testing
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)


def override_get_db():
    db: Session = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    yield TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def auth_header_global_admin(test_global_admin):
    token = create_access_token(data={"sub": test_global_admin.email}, expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header(test_user):
    token = create_access_token(data={"sub": test_user.email}, expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def device_headers(test_user, test_terminal):
    token = create_access_token(data={"sub": test_user.email}, expires_delta=timedelta(minutes=15))
    return {
        "Authorization": f"Bearer {token}",
        "x-device-id": test_terminal.device_id
    }


@pytest.fixture()
def tenant_user_headers(test_user, test_terminal):
    token = create_access_token(data={"sub": test_user.email}, expires_delta=timedelta(minutes=15))
    return {
        "Authorization": f"Bearer {token}",
        "x-device-id": test_terminal.device_id
    }


@pytest.fixture()
def auth_header_tenant_admin(test_tenant_admin, test_tenant: Tenant):
    token = create_access_token(data={"sub": test_tenant_admin.email},
                                expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {token}"}


def create_role(test_db: Session, name: str) -> Role:
    role = Role(name=name)
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def test_role(test_db: Session) -> Role:
    role = Role(name=RoleEnum.USER.value)
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def test_admin_user(client, test_db: Session, test_tenant, test_user):
    role = create_role(test_db, "admin")
    test_user.role_id = role.id
    test_db.commit()
    return test_user


@pytest.fixture
def test_user_with_routes(client, test_db: Session, test_tenant, test_route, test_user):
    stmt = insert(role_route_association).values(
        role_id=test_user.role_id,
        route_id=test_route.id
    )
    test_db.execute(stmt)
    test_db.commit()
    return test_user


@pytest.fixture
def auth_header_admin(test_admin_user, test_tenant: Tenant):
    token = create_access_token(data={"sub": test_admin_user.email, "tenant_id": str(test_tenant.id)},
                                expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_route(test_db: Session) -> Route:
    route = Route(path='/', method='GET', action='GET:/', name="Get user list")
    test_db.add(route)
    test_db.commit()
    test_db.refresh(route)
    return route


@pytest.fixture
def test_terminal(test_db: Session, test_tenant: Tenant):
    terminal = test_db.query(Terminal).first()
    if terminal: return terminal
    terminal = Terminal(
        terminal_id='Terminal 1',
        secret_key=settings.SECRET_KEY,
        tenant_id=test_tenant.id,
        config_version=1,
        site_id=str(uuid.uuid4()),
        site_name='Site 1',
        label='Terminal 1',
        token=get_sequence_number(),
        trading_name='Business name',
        address_lines=['Address line 1', 'Address line 2'],
        email='7VtZG@example.com',
        activation_code=get_sequence_number(),
        position=1,
        phone_number='1234567890',
        device_id=get_sequence_number()
    )

    test_db.add(terminal)
    test_db.commit()
    test_db.refresh(terminal)
    return terminal


@pytest.fixture
def test_product(test_db: Session, test_tenant: Tenant, test_terminal: Terminal, test_tax_rate):
    product = test_db.query(Product).filter(Product.tenant_id == test_tenant.id).first()
    if product: return product
    product = Product(
        tenant_id=test_tenant.id,
        quantity=10,
        site_id=test_terminal.site_id,
        name="Test Product",
        code=get_random_number(12),
        unit_of_measure="kg",
        unit_price=100,
        description="test product",
        tax_rate_id=str(test_tax_rate.rate_id),
        is_product=True,
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


@pytest.fixture
def test_item(test_db: Session):
    item = test_db.query(Item).first()
    if item: return item
    item = Item(code=get_random_number(), name="Salima Sugar 1kg", description="Salima Sugar 1kg")
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)
    return item


@pytest.fixture
def test_tax_rate(test_db: Session):
    tax_rate = test_db.query(TaxRate).first()
    if tax_rate: return tax_rate
    tax_rate = TaxRate(name="VAT-A", rate=16.5, rate_id="A")
    test_db.add(tax_rate)
    test_db.commit()
    test_db.refresh(tax_rate)
    return tax_rate


@pytest.fixture
def test_global_config(test_db: Session):
    config = test_db.query(GlobalConfig).first()
    if config: return config
    config = GlobalConfig(version=1)
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)
    return config


@pytest.fixture
def test_tenant(test_db: Session):
    tenant = test_db.query(Tenant).first()
    if tenant: return tenant
    tenant = Tenant(
        name="test",
        code=rstr.xeger(r"^[A-Z]+[0-9]{4}$"),
        email="test@example.com",
        phone_number="0886265490",
        tin="31699145",
        config_version=0,
        taxpayer_id=2345
    )
    test_db.add(tenant)
    test_db.commit()
    test_db.refresh(tenant)
    return tenant


@pytest.fixture
def test_admin(client, test_db: Session, test_tenant):
    role = test_db.query(Role).filter(Role.name == RoleEnum.ADMIN).first()
    if not role:
        role = Role(name=RoleEnum.ADMIN)
        test_db.add(role)
        test_db.commit()
    return role


@pytest.fixture
def test_tenant_admin(client, test_db: Session, test_tenant, test_admin):
    user = test_db.query(User).filter(User.tenant_id == test_tenant.id).first()
    if user: return user
    user = User(
        email="admin@example.com",
        hashed_password=settings.TEST_HASH,
        phone_number="0886265490",
        role_id=test_admin.id,
        tenant_id=test_tenant.id
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user(client, test_db: Session, test_tenant):
    role = get_role(test_db, RoleEnum.USER)

    user = test_db.query(User).filter(User.tenant_id == test_tenant.id).first()
    if user: return user
    user = User(
        email="user@example.com",
        hashed_password=settings.TEST_HASH,
        phone_number="0886265490",
        name="John Doe",
        role_id=role.id,
        tenant_id=test_tenant.id
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# @pytest.fixture
# def test_non_admin_user(test_db: Session):
#     role = create_role(test_db, "not_admin")
#     user = create_user(test_db, "test@example.io", get_config("TEST_SECRET"), role.id)
#     return user
#
#

@pytest.fixture
def test_profile(client, test_db: Session, test_tenant):
    profile = test_db.query(Profile).first()
    if profile: return profile
    profile = Profile(tenant_id=test_tenant.id)
    test_db.add(profile)
    test_db.commit()
    test_db.refresh(profile)
    return profile


def get_role(test_db: Session, role_name: str):
    role = test_db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        test_db.add(role)
        test_db.commit()
    return role


@pytest.fixture
def test_global_admin(client, test_db: Session):
    role = get_role(test_db, RoleEnum.GLOBAL_ADMIN)
    user = test_db.query(User).filter(User.role_id == role.id).first()
    if user: return user
    user = User(
        email="global_admin@example.com",
        hashed_password=settings.TEST_HASH,
        phone_number="0886265490",
        name="Global Admin",
        role_id=role.id,
        scope=Scope.GLOBAL,
        status=StatusEnum.ACTIVE
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def get_test_file(filename: str):
    response_file_path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(response_file_path, "r") as file:
        return file.read()


def get_mock_data(filename: str):
    mock_path = Path(__file__).parent / "data" / filename
    return json.loads(mock_path.read_text())


@pytest.fixture
def test_offline_transaction(test_db: Session, test_tenant, test_terminal):
    offline_transaction = test_db.query(OfflineTransaction).first()
    if offline_transaction: return offline_transaction
    offline_transaction = OfflineTransaction(
        transaction_id="test_transaction_id",
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        details={},
        submitted_at=None,
    )
    test_db.add(offline_transaction)
    test_db.commit()
    test_db.refresh(offline_transaction)
    return offline_transaction


@pytest.fixture
def test_dictionary(test_db: Session):
    dictionary = test_db.query(Dictionary).first()
    if dictionary: return dictionary
    dictionary = Dictionary(term=1001, definition="Active")
    test_db.add(dictionary)
    test_db.commit()
    test_db.refresh(dictionary)
    return dictionary
