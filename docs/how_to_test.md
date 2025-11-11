# How To Test the Template (Docker Workflow)

Sigue estos pasos exactos. Solo necesitas Docker y una terminal; no hace falta saber programar.

## 1. Requisitos
- Docker Desktop (Windows/macOS) o Docker Engine + Docker Compose v2 (Linux).
- Clonar el repositorio y moverte a `app_template/`.

## 2. Preparar variables de entorno
```bash
cp .env.example .env
```
Abre `.env` y confirma:
- `AUTH_MODE=built_in`
- `AUTO_BUILD_PERMISSIONS=true`
- `ENABLE_SEED_DATA=true`

## 3. Construir e iniciar con Docker Compose
```bash
docker compose up --build
```
La primera vez tarda unos minutos. Cuando veas mensajes como `Service Running` o `Finished initializing base data`, la API está lista.

## 4. Verificar que responde
1. Abre un navegador y visita `http://localhost:8000/` → debería mostrar `{"message":"Service Running"}`.
2. Visita `http://localhost:8000/docs` → Swagger tiene que cargar sin errores.

## 5. Probar el login (modo built_in)
En otra terminal:
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin@admin.com" \
  -d "password=admin"
```
Guarda el valor de `access_token`.

## 6. Consumir un endpoint protegido
```bash
curl -H "Authorization: Bearer TOKEN_AQUI" \
     http://localhost:8000/stores
```
Si ves una lista (vacía o con “Base Store”), la lectura funciona.

## 7. Crear un recurso
```bash
curl -X POST http://localhost:8000/stores \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"name":"Store de prueba","address":"Av Siempre Viva 123"}'
```
Debes recibir un JSON con el nuevo store. Esto confirma permisos de escritura y seeds correctos.

## 8. Ver usuarios (requiere token)
```bash
curl -H "Authorization: Bearer TOKEN_AQUI" \
     http://localhost:8000/users
```
Deberías ver al menos el usuario admin. Confirma que el CRUD de usuarios está disponible.

## 9. Cambiar de modo de autenticación (opcional)
1. Edita `.env` y coloca `AUTH_MODE=disabled`.
2. Reinicia la app:
   ```bash
   docker compose down
   docker compose up --build
   ```
3. Accede a `http://localhost:8000/stores` sin token. Si responde, el modo sin auth funciona.

## 10. Apagar contenedores
```bash
docker compose down
```

Si todos los pasos anteriores funcionan sin errores, el template está probado y listo para usarse.
