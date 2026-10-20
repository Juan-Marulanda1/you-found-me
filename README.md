# You Found Me API

Backend API para publicar productos en venta y anuncios generales de negocios y emprendimientos. El proyecto separa ambos dominios y comparte la persistencia, paginación y gestión de publicaciones.

## Tecnologías

- Python 3.12+, FastAPI y Pydantic
- SQLAlchemy 2 y PostgreSQL
- Alembic para migraciones
- `uv` para dependencias y tareas
- Ruff para estilo y lint

## Estructura

```text
backend/app/
├── api/                 # Composición de routers
├── core/                # Configuración, errores, PIN y paginación
├── database/            # Sesiones, mixins y adaptador SQLAlchemy
└── modules/
    ├── announcement/    # Avisos comerciales y de emprendimientos
    ├── product/         # Productos en venta
    └── publication/     # Contratos compartidos entre publicaciones
```

## Instalación

Requiere Python 3.12+, `uv` y PostgreSQL. Desde `backend/`:

```bash
uv sync
Copy-Item .env.example .env # PowerShell; en macOS/Linux: cp .env.example .env
```

Para iniciar PostgreSQL local desde la raíz del repositorio, ejecuta `docker compose --env-file backend/.env up -d database`. Los valores predeterminados del servicio son solo para desarrollo. Configura `DATABASE_URL` y `ALLOWED_ORIGINS` en `backend/.env`. Antes de actualizar una base de datos que ya tenga avisos, crea un respaldo. La migración actual transforma los PIN existentes en hashes y no permite volver automáticamente al esquema anterior.

```bash
uv run alembic upgrade head
uv run task dev
```

La API queda en `http://localhost:8000`; Swagger UI en `/docs` y ReDoc en `/redoc`.

## Contrato de la API

Todas las rutas llevan el prefijo `/api/v1` y las respuestas usan `{ "success", "message", "data" }`.

| Recurso | Método y ruta | Uso |
| --- | --- | --- |
| Anuncios | `POST /announcements` | Crear un anuncio de negocio o emprendimiento |
| Anuncios | `GET /announcements` | Listar con filtros y paginación |
| Anuncios | `GET /announcements/{id}` | Consultar un anuncio activo |
| Anuncios | `POST /announcements/{id}/manage` | Consultar datos privados y estados no activos con su PIN |
| Anuncios | `PATCH /announcements/{id}` | Editar con su PIN |
| Anuncios | `DELETE /announcements/{id}` | Borrar con su PIN |
| Productos | `POST /products` | Crear un producto |
| Productos | `GET /products` | Listar con filtros y paginación |
| Productos | `GET /products/{id}` | Consultar un producto activo |
| Productos | `POST /products/{id}/manage` | Consultar datos privados y estados no activos con su PIN |
| Productos | `PATCH /products/{id}` | Editar con su PIN |
| Productos | `DELETE /products/{id}` | Borrar con su PIN |

Los listados públicos muestran solo publicaciones `ACTIVE` y aceptan `page` (empieza en 1), `page_size` (1–100, predeterminado 20), `city`, `category` y `search` (busca en título y descripción; en anuncios también en el nombre del negocio). Los productos aceptan además `min_price` y `max_price`. La respuesta de lista incluye `items`, `page`, `page_size`, `total` y `pages`. No se pueden filtrar publicaciones pausadas o cerradas desde las rutas públicas.

### Crear un anuncio

```json
{
  "admin_pin": "482931",
  "title": "Pan artesanal todos los días",
  "description": "Pan de masa madre preparado en nuestro emprendimiento local.",
  "category": "Alimentos",
  "business_name": "Horno Andino",
  "contact_name": "Ana Pérez",
  "contact_phone": "3001234567",
  "contact_phone_public": false,
  "contact_email": "hola@horno.example",
  "city": "Medellín",
  "address": "Laureles"
}
```

### Crear un producto

```json
{
  "admin_pin": "482931",
  "title": "Mesa de madera",
  "description": "Mesa artesanal para comedor, en excelente estado.",
  "category": "Hogar",
  "price": "250000.00",
  "currency": "COP",
  "quantity": 1,
  "contact_name": "Ana Pérez",
  "contact_phone": "3001234567",
  "contact_phone_public": false,
  "city": "Medellín"
}
```

Los PIN nuevos deben tener entre 6 y 12 dígitos. La base de datos almacena hashes con sal, nunca el PIN original. Los avisos existentes conservan sus PIN de cuatro dígitos hasta que el usuario decida cambiarlos; el contrato de actualización y borrado los acepta durante esa transición.

Después de cinco PIN incorrectos para la misma publicación desde la misma dirección de origen, la API bloquea nuevos intentos durante 15 minutos. El contador está en memoria por proceso; un despliegue con varias instancias debe mover esta limitación a Redis o al proxy de entrada.

### Editar y borrar

`PATCH` incluye el PIN actual y al menos un campo modificable. Puede incluir `new_admin_pin` para cambiarlo; el nuevo PIN debe tener entre 6 y 12 dígitos. `DELETE` recibe solamente el PIN actual:

```json
{ "admin_pin": "482931", "title": "Nuevo título", "new_admin_pin": "731846" }
```

```json
{ "admin_pin": "482931" }
```

Los estados de anuncios son `ACTIVE`, `PAUSED` y `CLOSED`; en productos son `ACTIVE`, `SOLD` y `CLOSED`. Las respuestas públicas no incluyen correo ni dirección exacta. El teléfono se devuelve solo si al crear o editar se envió `contact_phone_public: true`; por defecto queda privado. Las respuestas públicas nunca incluyen el hash del PIN.

### Sección “Tus publicaciones”

El PIN es individual para cada anuncio o producto. Para una interfaz sencilla sin cuentas, el frontend puede guardar en `localStorage` pares `{ "kind": "product", "id": "..." }` o `{ "kind": "announcement", "id": "..." }` al recibir una creación exitosa. La sección solicita el PIN y lo envía a `POST /{id}/manage` para ver datos privados y publicaciones no activas. No guardes el PIN en el navegador. Esta lista solo existe en ese navegador; no recupera publicaciones en otro dispositivo ni después de borrar los datos locales.

El servidor usa `request.client.host` después de que Uvicorn valide los encabezados del proxy. Ejecuta `uv run task start` en producción para que la configuración de la aplicación se aplique a Uvicorn; en un contenedor configura también `HOST=0.0.0.0`. Configura `FORWARDED_ALLOW_IPS` en el entorno de ejecución con las IP/CIDR exactas de los proxies confiables. No uses `*` en producción: la aplicación rechaza ese valor porque permitiría falsificar `X-Forwarded-For` si el backend fuera accesible fuera del proxy. Si el proxy cambia o escala, actualiza esa lista en el despliegue.

La migración de Marketplace transforma los PIN almacenados anteriormente en texto y no permite restaurar el esquema previo. Pruébala primero contra una base PostgreSQL desechable con datos de la revisión `1b159c348e7e`; la prueba de integración se activa con `MIGRATION_TEST_DATABASE_URL` y solo acepta una base PostgreSQL local cuyo nombre incluya `test`.

## Desarrollo

Desde `backend/`:

```bash
uv run task dev
uv run task lint
uv run task format
uv run task test
```

Las migraciones se ejecutan con `uv run alembic upgrade head`. Alembic carga todos los modelos registrados para que la autogeneración compare el esquema completo.

La prueba de migración de integración necesita una base PostgreSQL descartable local. Define `MIGRATION_TEST_DATABASE_URL` con una base cuyo nombre incluya `test` (por ejemplo `you_found_me_test`); la prueba crea y elimina un esquema temporal aislado y rechaza hosts remotos para evitar tocar Supabase o producción.
