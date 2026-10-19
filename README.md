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
| Anuncios | `GET /announcements/{id}` | Consultar un anuncio |
| Anuncios | `PATCH /announcements/{id}` | Editar con su PIN |
| Anuncios | `DELETE /announcements/{id}` | Borrar con su PIN |
| Productos | `POST /products` | Crear un producto |
| Productos | `GET /products` | Listar con filtros y paginación |
| Productos | `GET /products/{id}` | Consultar un producto |
| Productos | `PATCH /products/{id}` | Editar con su PIN |
| Productos | `DELETE /products/{id}` | Borrar con su PIN |

Los listados aceptan `page` (empieza en 1), `page_size` (1–100, predeterminado 20), `city`, `category`, `status` y `search` (busca en título y descripción; en anuncios también en el nombre del negocio). Los productos aceptan además `min_price` y `max_price`. La respuesta de lista incluye `items`, `page`, `page_size`, `total` y `pages`.

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

Los estados de anuncios son `ACTIVE`, `PAUSED` y `CLOSED`; en productos son `ACTIVE`, `SOLD` y `CLOSED`. Las respuestas públicas nunca incluyen el hash del PIN.

### Sección “Tus publicaciones”

El PIN es individual para cada anuncio o producto. Para una interfaz sencilla sin cuentas, el frontend puede guardar en `localStorage` pares `{ "kind": "product", "id": "..." }` o `{ "kind": "announcement", "id": "..." }` al recibir una creación exitosa. La sección carga cada elemento con su ruta `GET`, y solicita el PIN al editar o borrar. No guardes el PIN en el navegador. Esta lista solo existe en ese navegador; no recupera publicaciones en otro dispositivo ni después de borrar los datos locales.

La API devuelve los campos de contacto en consultas públicas. Antes de publicar en producción, define qué datos deben mostrarse y cuáles deben reservarse para contacto privado.

## Desarrollo

Desde `backend/`:

```bash
uv run task dev
uv run task lint
uv run task format
uv run task test
```

Las migraciones se ejecutan con `uv run alembic upgrade head`. Alembic carga todos los modelos registrados para que la autogeneración compare el esquema completo.
