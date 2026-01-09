# Working Notes - Analisis de Problemas

Este documento consolida el estado actual del repo frente a los 8 puntos listados.
Incluye cambios ya aplicados y pendientes, y se actualiza a medida que avanza el plan.

## 1) Acoplamiento entre modulos y permisos/autenticacion
Estado actual
- La seleccion de routers depende del modo de auth via `app/routers/registry.py`.
- Si `AUTH_MODE=disabled`, solo se incluye `tenants` y las rutas de auth quedan fuera del esquema.
- `build_permissions` crea permisos en base a rutas presentes y no depende de `tenants`.

Implicaciones
- Las rutas de auth pueden desactivarse sin tocar `app/main.py`.
- Los permisos se generan solo para rutas activas.

Expansion de lo que se necesita
- Evaluar si `AUTH_MODE=custom` debe ocultar rutas o mantenerlas visibles.


## 2) DELETE fisico vs borrado logico
Estado actual
- Existe `deleted_at` en `Base` y todos los modelos lo heredan (`app/database/models/base_models.py`).
- Las consultas filtran soft delete por defecto via `apply_soft_delete_filter` (`app/database/soft_delete.py`).
- Los endpoints usan soft delete y cascada:
  - La cascada es opt-in por metadata en relaciones `info={"soft_delete_cascade": True}`.
  - El helper `soft_delete_by_id` aplica la cascada segun esas relaciones.
- La vista `tenants_user_counts` excluye registros con `deleted_at`.

Implicaciones
- Las eliminaciones quedan trazadas y recuperables.
- Las queries activas excluyen registros borrados sin necesidad de filtros manuales.

Pendiente
- Revisar la cascada en modelos nuevos y validar si algun flujo requiere restauracion.


## 3) Versionado de endpoints y separacion de logica
Estado actual
- Los endpoints viven en `app/routers/v1/` y se montan con prefijo `/v1`.
- La logica de negocio vive en `app/endpoints_logic/` y los routers delegan.

Implicaciones
- Hay versionado formal (`/v1`) y estructura para futuras versiones.
- La logica esta separada y reutilizable fuera del router.

Expansion de lo que se necesita
- Evaluar como versionar futuras rutas (`v2`, etc.) y el proceso de migracion.


## 4) Creacion manual de endpoints/schemas/modelos
Estado actual
- No hay generadores ni scripts. Agregar un recurso implica crear modelo, schema, router, registrar en `app/main.py` y posiblemente permisos.
- La guia actual es manual (ej. copiar `tenants` y ajustar).

Implicaciones
- Alto costo de repeticion y riesgo de inconsistencias.
- Mayor probabilidad de olvidar pasos (migrations, registro, permisos, docs).

Expansion de lo que se necesita
- Automatizacion que genere estructura completa y consistente (modelo, schema, router, registro, tests/documentacion).


## 5) Alembic no preparado para uso sencillo
Estado actual
- `alembic.ini` esta en la raiz y usa `script_location = app/alembic`.
- `app/alembic/env.py` ajusta `sqlalchemy.url` con `get_migration_database_url()` y evita imports fragiles.
- `docs/alembic-guide.md` contiene pasos simples para crear, aplicar y revertir migraciones.

Implicaciones
- Se reducen errores de ruta y de DB no alineada con `DATABASE_URL`.

Pendiente
- Validar en un entorno distinto a SQLite y ajustar si aparece un caso no cubierto.


## 6) Automatizacion para conexiones a bases externas
Estado actual
- Solo existe un helper opcional (`app/database/external.py`) que expone `get_external_db()` y falla si `EXTERNAL_DB_URL` no esta configurada.
- No hay generacion automatica, ni multiples conexiones, ni gestion de permisos.
- La guia `docs/external-db-guide.md` es manual y no define roles o permisos CRUD para la conexion externa.

Implicaciones
- Cada integracion externa requiere trabajo manual y no queda estandarizada.
- No hay control claro de permisos de acceso por CRUD para la DB externa.

Expansion de lo que se necesita
- Automatizacion para registrar una DB externa (config + helper + docs).
- Opcion de permisos por CRUD (definidos por el sistema o por el usuario de DB).
- Instrucciones generadas que expliquen como usar la conexion en endpoints.


## 7) Retries progresivos y rate limiting
Estado actual
- No hay middleware ni utilidades para reintentos (ej. con Tenacity) ni para rate limiting.
- No hay politica por defecto para endpoints internos o externos.

Implicaciones
- Llamadas a servicios externos pueden fallar sin reintento.
- La API es vulnerable a abuso o picos sin control.

Expansion de lo que se necesita
- Estrategia de retries configurable (backoff progresivo) para integraciones externas.
- Rate limiting a nivel de app (middleware) o por router, con configuracion en `.env`.
- Debe ser opt-in por endpoint (posibilidad de desactivar rate limiting caso a caso).


## 8) Cacheo
Estado actual
- No hay ningun mecanismo de cache (ni in-memory ni Redis).
- No hay headers de cache en respuestas ni invalidaciones.

Implicaciones
- Endpoints con lecturas repetidas no tienen optimizacion.
- Falta de patrones para cache de datos externos o queries costosas.

Expansion de lo que se necesita
- Evaluar una estrategia base (cache in-memory simple o Redis opcional).
- Definir politicas de expiracion e invalidacion.


## Dependencias y orden sugerido
Observaciones de dependencia
- (2) Soft delete depende de (5) porque requiere migraciones confiables y documentadas.
- (3) Versionado y separacion de logica impacta (4) porque la automatizacion debe generar rutas y estructura ya versionadas.
- (1) Desacople de auth/permisos afecta (3) y (4) porque define como registrar/ocultar rutas y permisos en nuevas versiones.
- (6) Conexion a DB externa puede necesitar (7) retries y (8) cache para patrones de lectura intensiva.

Orden sugerido (de menor a mayor impacto global)
1) (5) Alembic y documentacion: base para todos los cambios estructurales.
2) (2) Soft delete: afecta modelos, queries, endpoints y migraciones.
3) (1) Desacople de auth/permisos: define como se comportan los routers y permisos en general.
4) (3) Versionado + capa de logica: organiza el codigo y define estructura futura.
5) (7) Retries y rate limiting: definir patron base para que el generador lo incluya.
6) (8) Cache: definir patron base para que el generador lo incluya.
7) (4) Automatizacion de endpoints: debe alinearse con la estructura final y los patrones de 7/8.
8) (6) Automatizacion de DB externa: puede integrarse luego de definir auth/permisos y patrones globales.

Notas de riesgo
- (2) puede romper comportamiento esperado si no se aplica filtro global `deleted_at` de forma consistente.
- (1) requiere cuidado para no dejar endpoints de auth visibles cuando no se usan.
- (5) es facil de ejecutar mal si la ruta y la URL de DB no quedan alineadas con `DATABASE_URL`.
