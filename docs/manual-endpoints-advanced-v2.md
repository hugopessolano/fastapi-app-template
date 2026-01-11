# Tutorial Manual v2 (sin UI): circuito avanzado con relaciones

Este tutorial explica el circuito completo de:
- `customers`
- `products`
- `orders`
- `order_items`

La idea es entender por que cada archivo existe y como se conectan modelo, schema, logica y router.

## 0) Diseno y relaciones (conceptos base)

Relaciones esperadas:
- Un `customer` tiene muchas `orders` (has_many).
- Un `order` pertenece a un `customer` (belongs_to).
- Un `order` tiene muchos `order_items` (has_many).
- Un `order_item` pertenece a un `order` y a un `product` (belongs_to).

Diagrama mental:
```
customers 1 --- * orders 1 --- * order_items * --- 1 products
```

Reglas que vas a ver en el codigo:
- `ForeignKey` crea la clave foranea en la tabla hija.
- `relationship` crea el acceso en Python (ORM).
- `back_populates` conecta ambos lados de la relacion.
- `ondelete` define comportamiento en la DB.
- `info={"soft_delete_cascade": True}` habilita cascada logica.

## 1) Modelos (SQLAlchemy)

### 1.1 Customers

Archivo: `app/database/models/customers_models.py`

```python
from sqlalchemy import Column, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class Customers(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=True, unique=False)
    orders: Mapped[List["Orders"]] = relationship("Orders", back_populates="customer")
```

Explicacion corta:
- `__tablename__` es el nombre real en la DB.
- `Mapped[List["Orders"]]` indica que `orders` es una lista de objetos.

### 1.2 Products

Archivo: `app/database/models/products_models.py`

```python
from sqlalchemy import Column, Float, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class Products(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=False)
    sku = Column(String, nullable=False, unique=True)
    price = Column(Float, nullable=False, unique=False)
    order_items: Mapped[List["OrderItems"]] = relationship("OrderItems", back_populates="product")
```

### 1.3 Orders

Archivo: `app/database/models/orders_models.py`

```python
from sqlalchemy import Column, Float, ForeignKey, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, unique=False)
    total = Column(Float, nullable=False, unique=False)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    customer = relationship("Customers", back_populates="orders")
    items: Mapped[List["OrderItems"]] = relationship(
        "OrderItems",
        back_populates="order",
        info={"soft_delete_cascade": True}
    )
```

Por que `soft_delete_cascade` aqui:
- Si borras una order logicamente, tambien se marca deleted_at en sus items.

### 1.4 OrderItems

Archivo: `app/database/models/order_items_models.py`

```python
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class OrderItems(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quantity = Column(Integer, nullable=False, unique=False)
    unit_price = Column(Float, nullable=False, unique=False)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    order = relationship("Orders", back_populates="items")
    product = relationship("Products", back_populates="order_items")
```

Detalle importante:
- `order_id` esta en `OrderItems` porque es la tabla hija.
- `ondelete="CASCADE"` en la DB y `soft_delete_cascade` en el ORM son complementarios.

## 2) Registrar modelos en `__init__.py`

Archivo: `app/database/models/__init__.py`

```python
from .customers_models import Customers
from .products_models import Products
from .orders_models import Orders
from .order_items_models import OrderItems
```

Agrega cada clase a `__all__` para que los imports globales funcionen.

## 3) Schemas (Pydantic)

Reglas simples:
- `Base*` es lo que devolvemos en respuestas.
- `Create` es lo que recibimos al crear.
- `Update` es lo que recibimos al actualizar.
- Los `*Core` sirven para embebido sin recursion.

### 3.1 Customers

`app/schemas/customers_schemas.py`

```python
from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional

class BaseCustomerCore(BaseSchema):
    name: str
    email: str
    phone: Optional[str] = None

class BaseCustomer(BaseCustomerCore):
    pass

class CustomerCreateCore(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

class CustomerCreate(CustomerCreateCore):
    pass

class CustomerUpdateCore(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class CustomerUpdate(CustomerUpdateCore):
    pass

    class Config:
        orm_mode = True
```

### 3.2 Products

`app/schemas/products_schemas.py`

```python
from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional

class BaseProductCore(BaseSchema):
    name: str
    sku: str
    price: float

class BaseProduct(BaseProductCore):
    pass

class ProductCreateCore(BaseModel):
    name: str
    sku: str
    price: float

class ProductCreate(ProductCreateCore):
    pass

class ProductUpdateCore(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None

class ProductUpdate(ProductUpdateCore):
    pass

    class Config:
        orm_mode = True
```

### 3.3 OrderItems

`app/schemas/order_items_schemas.py`

```python
from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional

class BaseOrderItemCore(BaseSchema):
    quantity: int
    unit_price: float
    order_id: str
    product_id: str

class BaseOrderItem(BaseOrderItemCore):
    pass

class OrderItemCreateCore(BaseModel):
    quantity: int
    unit_price: float
    order_id: str
    product_id: str

class OrderItemCreate(OrderItemCreateCore):
    pass

class OrderItemUpdateCore(BaseModel):
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    order_id: Optional[str] = None
    product_id: Optional[str] = None

class OrderItemUpdate(OrderItemUpdateCore):
    pass

    class Config:
        orm_mode = True
```

### 3.4 Orders (embebiendo customer e items)

`app/schemas/orders_schemas.py`

```python
from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional, List
from app.schemas.customers_schemas import BaseCustomerCore
from app.schemas.order_items_schemas import BaseOrderItemCore, OrderItemCreateCore, OrderItemUpdateCore

class BaseOrderCore(BaseSchema):
    order_number: str
    status: str
    total: float
    customer_id: str

class BaseOrder(BaseOrderCore):
    customer: Optional[BaseCustomerCore] = None
    items: Optional[List[BaseOrderItemCore]] = None

class OrderCreateCore(BaseModel):
    order_number: str
    status: str
    total: float
    customer_id: str

class OrderCreate(OrderCreateCore):
    items: Optional[List[OrderItemCreateCore]] = None

class OrderUpdateCore(BaseModel):
    order_number: Optional[str] = None
    status: Optional[str] = None
    total: Optional[float] = None
    customer_id: Optional[str] = None

class OrderUpdate(OrderUpdateCore):
    items: Optional[List[OrderItemUpdateCore]] = None

    class Config:
        orm_mode = True
```

Por que `*Core`:
- Evita que `Order` embeba `Customer` que embeba `Order` de nuevo.

## 4) Logica de endpoints

### 4.1 Customers y Products (basico)

Puedes copiar `products.py` y reemplazar nombres.
Puntos importantes:
- `SORTABLE_FIELDS_*` define los campos permitidos para ordenar.
- `soft_delete_by_id` evita borrado fisico.

### 4.2 OrderItems (basico)

Tambien puedes copiar el patron de products. En `OrderItems` solo recuerda que tiene `order_id` y `product_id`.

### 4.3 Orders (con nested relations)

Archivo: `app/endpoints_logic/v1/orders.py`

```python
from app.endpoints_logic.nested import NestedRelationConfig, apply_nested_relations

NESTED_CREATE_RELATIONS = [
    NestedRelationConfig(name="items", relation_type="has_many", target_model=OrderItems),
]

NESTED_UPDATE_RELATIONS = [
    NestedRelationConfig(name="items", relation_type="has_many", target_model=OrderItems),
]

def create_order(payload: OrderCreate, db: Session) -> Orders:
    data = payload.model_dump()
    nested_payloads = {
        "items": data.pop("items", None),
    }
    item = Orders(**data)
    apply_nested_relations(item, nested_payloads, NESTED_CREATE_RELATIONS, db, mode="create")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def update_order(item_id: str, payload: OrderUpdate, db: Session) -> Orders:
    item = db.query(Orders).filter(Orders.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    data = payload.model_dump(exclude_unset=True)
    nested_payloads = {
        "items": data.pop("items", None),
    }
    for key, value in data.items():
        setattr(item, key, value)
    apply_nested_relations(item, nested_payloads, NESTED_UPDATE_RELATIONS, db, mode="update")
    db.commit()
    db.refresh(item)
    return item
```

Que hace `apply_nested_relations`:
- Si recibe objetos en `items`, los crea y los asocia al Order.
- En `update` hace append por default.

## 5) Routers (FastAPI)

Crea routers en:
- `app/routers/v1/customers.py`
- `app/routers/v1/products.py`
- `app/routers/v1/orders.py`
- `app/routers/v1/order_items.py`

Patron:
- `APIRouter` con `prefix` y `tags`.
- `Depends(get_db)` y `Depends(get_auth_context)` si hay auth.
- `response_model` para validar la salida.

## 6) Registrar routers en `registry_data.json`

Archivo: `app/routers/registry_data.json`

Ejemplo:
```json
{
  "name": "orders",
  "module": "app.routers.v1.orders",
  "requires_auth": true,
  "requires_tenants": false,
  "enabled": true
}
```

## 7) Crear tablas y probar

Opciones:
- Desarrollo rapido: iniciar la app y dejar que `Base.metadata.create_all` cree tablas.
- Produccion: Alembic (ver `docs/alembic-guide.md`).

Pruebas manuales (flujo real):
1) Login `POST /v1/auth/login` con `admin@admin.com` / `admin`.
2) Crear customer:
```json
{"name": "Acme", "email": "acme@example.com", "phone": "555-0100"}
```
3) Crear product:
```json
{"name": "Widget", "sku": "W-100", "price": 50.0}
```
4) Crear order con items embebidos:
```json
{
  "order_number": "ORD-1001",
  "status": "open",
  "total": 100.0,
  "customer_id": "<customer_id>",
  "items": [
    {"quantity": 2, "unit_price": 50.0, "order_id": "", "product_id": "<product_id>"}
  ]
}
```
5) Update order agregando items:
```json
{"items": [{"quantity": 1, "unit_price": 50.0, "order_id": "", "product_id": "<product_id>"}]}
```

## 8) Checklist rapido (errores comunes)

- `back_populates` no coincide entre modelos.
- `__tablename__` no coincide con el nombre usado en `ForeignKey`.
- `order_id` o `product_id` faltan en `OrderItems`.
- `SORTABLE_FIELDS_*` no incluye un campo y el orden falla.
- No agregaste el router en `registry_data.json` y la ruta no aparece.

Si sigues este flujo, el circuito completo queda funcionando y es facil de extender.
