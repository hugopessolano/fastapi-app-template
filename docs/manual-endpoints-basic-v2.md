# Tutorial Manual v2 (sin UI): crear un endpoint simple

Este tutorial explica el flujo manual original de este template con mas contexto tecnico. No es solo "copiar y pegar": vas a entender por que existe cada archivo, como se conectan, y como adaptar cada parte.

Objetivo: crear un endpoint `categories` con los campos `name` y `description`.

## 0) Definir el recurso (nombre, rutas, archivos)

Decidimos:
- Nombre singular: `category`
- Nombre plural (ruta): `categories`
- Version API: `v1`

Archivos a crear:
- `app/database/models/categories_models.py` (modelo SQLAlchemy)
- `app/schemas/categories_schemas.py` (schemas Pydantic)
- `app/endpoints_logic/v1/categories.py` (logica del endpoint)
- `app/routers/v1/categories.py` (router FastAPI)

Base a copiar: `products` es simple y completo.

## 1) Modelo (SQLAlchemy): que significa cada parte

El modelo representa una tabla de base de datos. En este repo:
- `Base` agrega `created_at`, `updated_at` y `deleted_at` (soft delete).
- `__tablename__` define el nombre real de la tabla.
- `Mapped[T]` es una anotacion de tipo para el ORM (SQLAlchemy 2.0).
- `mapped_column` es la version tipada de `Column` y se usa en el id.
- `Column(...)` define columnas normales, con tipo, nullability y unique.

Crea `app/database/models/categories_models.py`:

```python
from sqlalchemy import Column, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class Categories(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True, unique=False)
```

Como adaptar:
- `name` es obligatorio (`nullable=False`) y unico.
- `description` puede ser nulo (`nullable=True`).
- Usa tipos SQLAlchemy compatibles: `String`, `Integer`, `Float`, `Boolean`, `DateTime`.

## 2) Schemas (Pydantic): entrada vs salida

Los schemas controlan validacion y salida JSON:
- `BaseSchema` incluye `id`, `created_at`, `updated_at`.
- `BaseModel` se usa para payloads de entrada (create/update).
- Los `*Core` evitan recursion si el schema se embebe dentro de otro.
- `Optional[T]` marca campos opcionales.

Crea `app/schemas/categories_schemas.py`:

```python
from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional

class BaseCategoryCore(BaseSchema):
    name: str
    description: Optional[str] = None

class BaseCategory(BaseCategoryCore):
    pass

class CategoryCreateCore(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryCreateCore):
    pass

class CategoryUpdateCore(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryUpdate(CategoryUpdateCore):
    pass

    class Config:
        orm_mode = True
```

Como adaptar:
- En `Create`, los campos obligatorios deben ser no-optional.
- En `Update`, todo suele ser optional (patch).
- En `Base`, define lo que quieres devolver en respuestas.

## 3) Logica del endpoint (endpoints_logic)

Esta capa contiene las operaciones reales:
- `list_*`: paginacion, orden, query base.
- `get_*`: buscar por id con 404 si no existe.
- `create_*`: crear desde `payload`.
- `update_*`: actualizar con `exclude_unset`.
- `delete_*`: usa soft delete (no borra fisico).

La logica de paginacion y orden ya esta estandarizada:
- `calculate_next_and_last_pages` agrega headers de paginacion.
- `order_by_parameter` solo permite campos en `SORTABLE_FIELDS`.

Crea `app/endpoints_logic/v1/categories.py`:

```python
from __future__ import annotations

from typing import List, TYPE_CHECKING

from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database.models import Categories
from app.database.soft_delete import soft_delete_by_id
from app.routers.utils import calculate_next_and_last_pages, order_by_parameter, filter_by_tenant
from app.schemas.categories_schemas import CategoryCreate, CategoryUpdate

if TYPE_CHECKING:
    from app.auth.context import AuthContext

_router_logger = None

def _get_logger():
    global _router_logger
    if _router_logger is None:
        from app.logging import child_logger

        _router_logger = child_logger.bind(router="categories")
    return _router_logger

SORTABLE_FIELDS_CATEGORIES = {
    "name": Categories.name,
    "description": Categories.description,
    "created_at": Categories.created_at,
    "updated_at": Categories.updated_at,
}

def list_categories(
    request: Request,
    response: Response,
    db: Session,
    auth: AuthContext,
    page: int,
    page_size: int,
    order_by: str,
    order_dir: str
) -> List[Categories]:
    offset = (page - 1) * page_size
    query = db.query(Categories)
    calculate_next_and_last_pages(query, page_size, page, request, response)
    query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_CATEGORIES, query)
    items = query.offset(offset).limit(page_size).all()
    _get_logger().bind(action="list").info("Retrieved records")
    return items

def get_category(item_id: str, db: Session) -> Categories:
    item = db.query(Categories).filter(Categories.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

def create_category(payload: CategoryCreate, db: Session) -> Categories:
    data = payload.model_dump()
    item = Categories(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    _get_logger().bind(action="create").info("Created record")
    return item

def update_category(item_id: str, payload: CategoryUpdate, db: Session) -> Categories:
    item = db.query(Categories).filter(Categories.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    _get_logger().bind(action="update").info("Updated record")
    return item

def delete_category(item_id: str, db: Session) -> None:
    deleted = soft_delete_by_id(db, Categories, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")
    _get_logger().bind(action="delete").info("Deleted record")
```

## 4) Router (FastAPI)

El router conecta HTTP con la logica:
- `Depends(get_db)` crea una Session por request.
- `Depends(get_auth_context)` obliga autenticacion.
- `Query(...)` define validaciones de query params.
- `response_model` valida la salida.

Crea `app/routers/v1/categories.py`:

```python
from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.context import AuthContext, get_auth_context
from app.database.database import get_db
from app.endpoints_logic.v1.categories import (
    list_categories,
    create_category,
    update_category,
    delete_category,
    get_category,
)
from app.schemas.categories_schemas import BaseCategory, CategoryCreate, CategoryUpdate
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/categories",
    tags=["Categories"],
)

@router.get("", response_model=List[BaseCategory])
async def get_items(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc")
):
    return list_categories(
        request=request,
        response=response,
        db=db,
        auth=auth,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir
    )

@router.get("/{item_id}", response_model=BaseCategory)
async def get_item(
    item_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return get_category(item_id=item_id, db=db)

@router.post("", response_model=BaseCategory, status_code=201)
async def post_item(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return create_category(payload=payload, db=db)

@router.put("/{item_id}", response_model=BaseCategory)
async def put_item(
    item_id: str,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return update_category(item_id=item_id, payload=payload, db=db)

@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return delete_category(item_id=item_id, db=db)
```

## 5) Registrar modelo y router

### 5.1 Modelo

En `app/database/models/__init__.py` agrega:

```python
from .categories_models import Categories
```

Y agrega `"Categories"` a `__all__`.

### 5.2 Router

En `app/routers/registry_data.json` agrega:

```json
{
  "name": "categories",
  "module": "app.routers.v1.categories",
  "requires_auth": true,
  "requires_tenants": false,
  "enabled": true
}
```

Notas:
- Si `AUTH_MODE=disabled`, los routers con `requires_auth=true` no se cargan.

## 6) Crear tabla y probar

Opciones:
- Desarrollo rapido: iniciar la app y dejar que `Base.metadata.create_all` cree la tabla.
- Produccion: usar Alembic (ver `docs/alembic-guide.md`).

Prueba minima:
1) Login en `/v1/auth/login`
2) `POST /v1/categories` con:

```json
{
  "name": "Hardware",
  "description": "Partes fisicas"
}
```

3) `GET /v1/categories`

Listo: endpoint simple, con logica clara y estructura del template respetada.
