# Tutorial UI (sin codigo): crear un endpoint simple

Este tutorial es el equivalente UI del flujo manual. No vas a escribir codigo: todo se configura desde la interfaz y el template genera el resto.

Objetivo: crear un endpoint `categories` con `name` y `description`.

## 0) Estado de la UI

Antes de empezar, confirma:
- "API Status" dice "Ready".
- No hay indicador "Compiling..." en pantalla. Si aparece, espera a que termine antes de continuar.

## 1) Crear un endpoint nuevo

Pulsa "Nuevo endpoint".

![Nuevo endpoint](images/ui-tutorial/basic-v2/ui-basic-02-new-endpoint.png)

## 2) Completar identidad del endpoint

La seccion "Identidad" define como se llama el recurso y donde se guarda su spec. En la imagen se resaltan los campos clave.

![Identidad](images/ui-tutorial/basic-v2/ui-basic-03-identidad.png)

Que significa cada campo:
- Ruta del spec: archivo JSON donde vive la definicion (ej: `specs/examples/categories.json`).
- Version: prefijo de ruta (`v1`).
- Nombre: singular (`category`).
- Plural: plural y ruta base (`categories`).
- Tabla: nombre real en la base (`categories`).
- Tags: grupo en Swagger (`Categories`).

Valores sugeridos:
- Ruta del spec: `specs/examples/categories.json`
- Version: `v1`
- Nombre: `category`
- Plural: `categories`
- Tabla: `categories`
- Tags: `Categories`

Tip: evita espacios en la ruta del spec y usa nombres consistentes (plural y tabla en minuscula).

## 3) Seguridad y comportamiento

Estos toggles definen el comportamiento general del endpoint.

![Seguridad y comportamiento](images/ui-tutorial/basic-v2/ui-basic-04-security-behavior.png)

Recomendado para un endpoint simple:
- Auth required: activado
- Soft delete: activado
- Pagination / Ordering: activado
- Tests enabled: activado

## 4) Rutas disponibles

Activa las rutas que quieres exponer en la API. En la imagen se resaltan las rutas del CRUD.

![Rutas disponibles](images/ui-tutorial/basic-v2/ui-basic-05-routes.png)

Para un CRUD completo:
- LIST, GET, CREATE, UPDATE, DELETE

## 5) Crear el endpoint

Pulsa "Crear endpoint". Esto genera el spec, el modelo, el schema, el router y la logica.

![Crear endpoint](images/ui-tutorial/basic-v2/ui-basic-06-create-action.png)

Si no aparece en la lista, pulsa "Refresh list".

## 6) Entrar a edicion del endpoint

En la lista, usa "Editar" para abrir el editor del endpoint.

![Editar endpoint](images/ui-tutorial/basic-v2/ui-basic-07-edit-button.png)

## 7) Editar modelos y definir campos

Desde la barra del editor, abre el Model Editor. El icono con forma de base de datos abre modelos, el icono de llaves abre schemas.

![Editar modelos y schemas](images/ui-tutorial/basic-v2/ui-basic-08-edit-icons.png)

En el Model Editor agrega los campos:
- `name`: String, Nullable false, Unique true.
- `description`: String, Nullable true, Unique false.

![Add field](images/ui-tutorial/basic-v2/ui-basic-09-models-add-field.png)

En la imagen se resalta el boton "Add field".

Cuando termines, pulsa "Guardar cambios" en el Model Editor.

## 8) Editar schemas y validaciones

Abre el Schema Editor. Usa las pestanas CREATE/UPDATE/RESPONSE para ajustar:
- Campos requeridos en create.
- Campos opcionales en update.
- Campos que se devuelven en response.

![Schema variants](images/ui-tutorial/basic-v2/ui-basic-10-schemas-variants.png)

En la imagen se resaltan las pestanas de variantes.

Cuando termines, pulsa "Guardar cambios" en el Schema Editor.

## 9) Checklist rapido (errores comunes)

- Nombre/Plural/Tabla no coinciden.
- Auth required activo pero `AUTH_MODE=disabled` en `.env`.
- Se olvidaron de guardar cambios en Model/Schema editor.
- La app estaba en "Compiling..." y el spec no se aplico.

Con esto ya puedes crear endpoints simples desde la UI sin tocar codigo.
