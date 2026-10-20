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
| Productos | `GET /products` | Listar con filtros, paginación e imagen principal |
| Productos | `GET /products/{id}` | Consultar un producto activo con su imagen principal |
| Productos | `POST /products/{id}/manage` | Consultar datos privados y estados no activos con su PIN |
| Productos | `PATCH /products/{id}` | Editar con su PIN |
| Productos | `DELETE /products/{id}` | Borrar con su PIN |
| Imágenes de productos | `POST /products/{id}/images/upload-url` | Autorizar con PIN y emitir una carga firmada |
| Imágenes de productos | `POST /products/{id}/images/{image_id}/complete` | Confirmar y publicar una imagen cargada |
| Imágenes de productos | `GET /products/{id}/images` | Listar imágenes de un producto activo |
| Imágenes de productos | `POST /products/{id}/images/manage` | Listar imágenes, incluidas pendientes, con PIN |
| Imágenes de productos | `DELETE /products/{id}/images/{image_id}` | Borrar o cancelar una imagen con PIN |

Los listados públicos muestran solo publicaciones `ACTIVE` y aceptan `page` (empieza en 1), `page_size` (1–100, predeterminado 20), `city`, `category` y `search` (busca en título y descripción; en anuncios también en el nombre del negocio). Los productos aceptan además `min_price` y `max_price`. La respuesta de lista incluye `items`, `page`, `page_size`, `total` y `pages`. Cada producto incluye `cover_image`: la primera imagen confirmada o `null`. El catálogo obtiene las portadas con una sola consulta adicional por página y evita solicitudes por cada tarjeta. No se pueden filtrar publicaciones pausadas o cerradas desde las rutas públicas.

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

### Carga de imágenes de productos con Supabase Storage

El backend entrega una capacidad de carga firmada solo después de validar el PIN del producto. La imagen se carga desde el navegador directamente a Supabase Storage; el backend no recibe ni retransmite sus bytes. La API permite JPG, PNG y WebP, hasta 5 MiB y 8 imágenes por producto. El bucket debe configurarse en Supabase como público para que el sitio pueda mostrar las fotos, con los tipos MIME `image/jpeg`, `image/png` y `image/webp` y un límite de 5 MiB. Los archivos quedan en `products/{product_id}/{uuid}.{ext}`; PostgreSQL guarda su ruta y metadatos, no la URL pública.

Configura en `backend/.env`:

| Parámetro | Valor | Función |
| --- | --- | --- |
| `SUPABASE_URL` | URL del proyecto, por ejemplo `https://<project-ref>.supabase.co` | Dirección base de la API de Storage. |
| `SUPABASE_SECRET_KEY` | Clave secreta del backend de Supabase (`sb_secret_...`) | Firma cargas y elimina archivos. Nunca debe incluirse en el frontend ni en Git. |
| `SUPABASE_PRODUCT_IMAGES_BUCKET` | `product-images` | Nombre exacto del bucket que creaste. |
| `PRODUCT_IMAGE_MAX_BYTES` | `5242880` | Límite de tamaño validado por la API en bytes (5 MiB). |
| `PRODUCT_IMAGE_MAX_COUNT` | `8` | Máximo de imágenes asociadas a un producto; las cargas pendientes también cuentan. |

Flujo del cliente:

1. Enviar a `POST /products/{id}/images/upload-url` el PIN, `content_type`, `size_bytes` y opcionalmente `alt_text`. Guardar temporalmente el `id`, `bucket`, `path` y `token` recibidos. La respuesta incluye `signed_upload_url` para clientes que prefieran usar la URL firmada directamente.
2. Con el cliente JavaScript de Supabase configurado con `SUPABASE_URL` y la clave pública `anon`/publishable del proyecto, subir el archivo con `supabase.storage.from(bucket).uploadToSignedUrl(path, token, file, { contentType: file.type, upsert: false })`. No usar la clave secreta del servidor en el navegador. Supabase indica que el token de carga vence en dos horas.
3. Llamar a `POST /products/{id}/images/{image_id}/complete` con el PIN. El servidor verifica que el objeto exista y que el tipo y tamaño coincidan antes de marcarlo como público.
4. Consultar `GET /products/{id}/images` para obtener las URLs públicas de las imágenes confirmadas. En “Tus publicaciones”, usar `POST /products/{id}/images/manage` con el PIN para ver fotos y cargas pendientes, incluso si el producto está cerrado o vendido. Si se abandona una carga, borrar su `image_id` con `DELETE /products/{id}/images/{image_id}` y el PIN para liberar el cupo.

El permiso público del bucket permite leer cualquier imagen cuyo URL se conozca; el PIN y la URL firmada controlan la carga, y el backend controla el borrado. Mantén el límite del bucket igual o menor que `PRODUCT_IMAGE_MAX_BYTES` y que el límite global configurado en Supabase. Si `SUPABASE_URL` o la clave están vacíos, las rutas de carga responden `503` y el resto de la API sigue funcionando. Los proyectos que aún usan la clave antigua pueden ponerla en `SUPABASE_SERVICE_ROLE_KEY`; al migrar, usa `SUPABASE_SECRET_KEY`. Las imágenes de anuncios generales todavía no están incluidas en este flujo.

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
