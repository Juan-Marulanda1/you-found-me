# You Found Me API

Backend API para publicar productos en venta y anuncios generales de negocios y emprendimientos. El proyecto separa ambos dominios y comparte la persistencia, paginación y gestión de publicaciones.

El frontend React inicial está en [`frontend/`](frontend/). Consulta su [guía de instalación, configuración y plan de evolución](frontend/README.md).

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

Para iniciar PostgreSQL local desde la raiz del repositorio, ejecuta docker compose --env-file backend/.env up -d database. Los valores predeterminados solo sirven para desarrollo. Configura DATABASE_URL y ALLOWED_ORIGINS en backend/.env. Antes de migrar una base que ya tenga avisos, crea un respaldo. La migracion de propiedad agrega el registro de invitaciones y owner_id nullable; no cambia ni borra avisos existentes. Sus PIN hashes quedan disponibles para reclamarlos.

```bash
uv run alembic upgrade head
uv run task dev
```

La API queda en `http://localhost:8000`; Swagger UI en `/docs` y ReDoc en `/redoc`.

## Contrato de la API

Todas las rutas llevan el prefijo `/api/v1` y las respuestas usan `{ "success", "message", "data" }`.

### Cuentas, invitaciones y publicaciones propias

PUBLICATION_CREATION_KEY se conserva como clave privada para solicitar una invitacion. POST /account-access/invite recibe X-Publication-Key y un correo; Supabase Auth envia el enlace. La clave nunca va en variables VITE_* ni queda guardada en el navegador.

POST /products y POST /announcements requieren Authorization: Bearer <access_token> y asocian cada nuevo registro al usuario autenticado. GET /account-access/me/publications lista las publicaciones de la cuenta y las antiguas que coincidan con el correo confirmado. POST /account-access/me/claim recibe kind, publication_id y el PIN existente; el backend solo asigna el registro despues de validar ese PIN.

La API guarda los correos autorizados en publication_invitations y solo permite iniciar sesion con un correo verificado incluido alli. Esto tambien impide crear publicaciones con una cuenta que se registro directamente en Supabase. La nueva migracion conserva los avisos y sus hashes existentes, dejandolos sin asignar para que sus duenos los reclamen. Los nuevos registros se administran con la sesion del propietario. Los registros antiguos mantienen el PIN hasta reclamarse; al abrir uno con sesion y PIN valido se vincula a la cuenta. Para validar sesiones, el backend consulta Supabase Auth. Configura SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL y SUPABASE_AUTH_REDIRECT_URL en el entorno privado. Agrega la URL de redireccion permitida en Supabase Auth y deshabilita el auto-registro publico para que todas las cuentas pasen por invitacion.

| Recurso | Metodo y ruta | Uso |
| --- | --- | --- |
| Cuentas | POST /account-access/invite | Enviar invitacion con X-Publication-Key |
| Cuentas | GET /account-access/me/publications | Listar propias y antiguas reclamables; requiere sesion |
| Cuentas | POST /account-access/me/claim | Reclamar antigua validando el PIN; requiere sesion |
| Anuncios | POST /announcements | Crear con sesion autenticada |
| Anuncios | GET /announcements | Listar avisos activos |
| Anuncios | GET /announcements/{id} | Consultar aviso activo |
| Anuncios | POST /announcements/{id}/manage | Consultar datos privados; propietario o PIN de aviso antiguo |
| Anuncios | PATCH /announcements/{id} | Editar; propietario o PIN de aviso antiguo |
| Anuncios | DELETE /announcements/{id} | Borrar; propietario o PIN de aviso antiguo |
| Imagen de aviso | POST /announcements/{id}/images/upload-url | Autorizar con sesion del propietario o PIN antiguo |
| Imagen de aviso | POST /announcements/{id}/images/{image_id}/complete | Confirmar carga con sesion o PIN antiguo |
| Imagen de aviso | GET /announcements/{id}/images | Listar imagenes de aviso activo |
| Imagen de aviso | POST /announcements/{id}/images/manage | Administrar imagenes con sesion o PIN antiguo |
| Imagen de aviso | DELETE /announcements/{id}/images/{image_id} | Borrar imagen con sesion o PIN antiguo |
| Productos | POST /products | Crear con sesion autenticada |
| Productos | GET /products | Listar productos activos |
| Productos | GET /products/{id} | Consultar producto activo |
| Productos | POST /products/{id}/manage | Consultar datos privados; propietario o PIN de publicacion antigua |
| Productos | PATCH /products/{id} | Editar; propietario o PIN de publicacion antigua |
| Productos | DELETE /products/{id} | Borrar; propietario o PIN de publicacion antigua |
| Imagenes de productos | POST /products/{id}/images/upload-url | Autorizar con sesion del propietario o PIN antiguo |
| Imagenes de productos | POST /products/{id}/images/{image_id}/complete | Confirmar carga con sesion o PIN antiguo |
| Imagenes de productos | GET /products/{id}/images | Listar imagenes de producto activo |
| Imagenes de productos | POST /products/{id}/images/manage | Administrar imagenes con sesion o PIN antiguo |
| Imagenes de productos | DELETE /products/{id}/images/{image_id} | Borrar imagen con sesion o PIN antiguo |

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

### Carga de imágenes con Supabase Storage

El backend entrega una capacidad de carga firmada solo después de validar el PIN de la publicación. La imagen se carga desde el navegador directamente a Supabase Storage; el backend no recibe ni retransmite sus bytes. Se aceptan JPG, PNG y WebP de hasta 5 MiB. Cada producto admite hasta 8 imágenes y cada anuncio 1. El mismo bucket público existente sirve para ambos tipos; el límite del bucket en Supabase debe ser de 5 MiB. Los archivos quedan en `products/{product_id}/{uuid}.{ext}` o `announcements/{announcement_id}/{uuid}.{ext}`. PostgreSQL guarda la ruta y los metadatos, no la URL pública.

Configura en `backend/.env`:

| Parámetro | Valor | Función |
| --- | --- | --- |
| SUPABASE_URL | URL del proyecto Supabase | Base de Auth y Storage. |
| SUPABASE_PUBLISHABLE_KEY | Clave publicable del proyecto | Identifica el proyecto al verificar la sesion del usuario. |
| SUPABASE_AUTH_REDIRECT_URL | URL permitida de frontend, por ejemplo http://localhost:5173/cuenta | Destino del enlace de invitacion. |
| `SUPABASE_SECRET_KEY` | Clave secreta del backend de Supabase (`sb_secret_...`) | Firma cargas y elimina archivos. Nunca debe incluirse en el frontend ni en Git. |
| `SUPABASE_PRODUCT_IMAGES_BUCKET` | `product-images` | Nombre exacto del bucket que creaste. |
| `PRODUCT_IMAGE_MAX_BYTES` | `5242880` | Límite de tamaño validado por la API en bytes (5 MiB). |
| `PRODUCT_IMAGE_MAX_COUNT` | `8` | Máximo de imágenes asociadas a un producto; las cargas pendientes también cuentan. |
| `ANNOUNCEMENT_IMAGE_MAX_COUNT` | `1` | Máximo de imágenes asociadas a un anuncio; una carga pendiente también cuenta. |

Flujo del cliente:

1. Para un producto, solicitar POST /products/{id}/images/upload-url; para un aviso, POST /announcements/{id}/images/upload-url. Incluir content_type, size_bytes y, opcionalmente, alt_text. La API autoriza con la sesion del propietario o con el PIN si el registro antiguo aun no se reclama.
2. Con el cliente JavaScript de Supabase configurado con `SUPABASE_URL` y la clave pública `anon`/publishable del proyecto, subir el archivo con `supabase.storage.from(bucket).uploadToSignedUrl(path, token, file, { contentType: file.type, upsert: false })`. No usar la clave secreta del servidor en el navegador. Supabase indica que el token de carga vence en dos horas.
3. Llamar a POST /products/{id}/images/{image_id}/complete o POST /announcements/{id}/images/{image_id}/complete con la sesion del propietario o, para registros antiguos no reclamados, con el PIN. La API verifica que el objeto exista y que coincidan el tipo y el tamano antes de publicarlo.
4. Consultar GET /products/{id}/images o GET /announcements/{id}/images para obtener las URLs de imagenes confirmadas. Para ver cargas pendientes o borrar una imagen, usar las rutas /images/manage y DELETE /images/{image_id} con la sesion del propietario o el PIN antiguo.

El permiso publico del bucket permite leer cualquier imagen cuyo URL se conozca; una URL firmada controla la carga y la API autoriza las operaciones con sesion de propietario o con el PIN de avisos antiguos. Mantener el limite del bucket igual o menor que PRODUCT_IMAGE_MAX_BYTES y el limite global de Supabase. Si SUPABASE_URL o las claves requeridas estan vacias, las operaciones relacionadas responden 503. Los proyectos que aun usan la clave anterior pueden ponerla en SUPABASE_SERVICE_ROLE_KEY; al migrar, usar SUPABASE_SECRET_KEY.

### Sección “Tus publicaciones”

Tus publicaciones consulta la API con la cuenta autenticada y esta disponible en otros dispositivos. Las publicaciones antiguas que coincidan con el correo verificado se muestran para reclamarlas con el PIN. Las antiguas sin correo coincidente se pueden abrir desde una referencia local que ya exista y reclamar con su PIN. El PIN nunca se guarda en el navegador.

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
