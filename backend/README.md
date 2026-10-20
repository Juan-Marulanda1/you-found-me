# Backend API

API modular para productos y avisos comerciales. El backend no depende de React: puede consumirse desde otro frontend o utilizarse como base para una aplicación con otros dominios.

## Arquitectura

FastAPI recibe las solicitudes HTTP y delega en rutas de dominio. Las rutas validan el contrato y la autorización; los servicios aplican reglas de negocio; los repositorios encapsulan consultas SQLAlchemy. Las integraciones externas, como Supabase Auth y Storage, quedan separadas de los módulos de producto y anuncio.

~~~text
backend/
  app/
    api/             Composición y prefijo de las rutas
    core/            Configuración, seguridad, errores (RFC 9457) y utilidades comunes
    database/        Modelos compartidos, sesión y repositorios genéricos
    integrations/    Adaptadores de servicios externos
    modules/
      account/       Invitaciones, cuenta y publicaciones propias
      product/       Dominio de productos
      announcement/  Dominio de avisos
      publication/   Contratos e imágenes compartidos
  alembic/           Migraciones versionadas
  tests/             Pruebas automatizadas
  server.py          Entrada de Uvicorn con configuración de proxy
~~~

Los flujos completos están en [docs/flujos.md](docs/flujos.md); las rutas y sus requisitos de acceso están en [docs/api.md](docs/api.md).

## Requisitos

- Python 3.12 o superior.
- uv.
- PostgreSQL 17 para desarrollo local (la versión de Docker Compose).
- Docker Desktop o Docker Engine si se usa la base local en contenedor.
- Un proyecto Supabase si se habilitan Auth y Storage.

## Instalación local

Desde la raíz del repositorio:

~~~powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
docker compose --env-file backend/.env up -d database
~~~

Luego, desde backend:

~~~powershell
uv sync
uv run alembic upgrade head
uv run task dev
~~~

La API queda en http://localhost:8000. Swagger UI está en http://localhost:8000/docs y ReDoc en http://localhost:8000/redoc. Para iniciar el frontend, consulta [su guía local](../frontend/README.md#instalacion-local).

Si usas una base externa en lugar del contenedor, configura DATABASE_URL con una URL PostgreSQL compatible con psycopg y ejecuta las migraciones contra esa base. Antes de migrar una base con datos existentes, respáldala y valida la migración en un entorno de pruebas.

## Variables de entorno

El archivo .env.example contiene valores de desarrollo y no contiene credenciales reales.

| Variable | Uso |
| --- | --- |
| DATABASE_URL | Conexión SQLAlchemy a PostgreSQL. |
| APP_NAME, APP_VERSION, PROJECT_DESCRIPTION | Metadatos de OpenAPI y de la aplicación. |
| DEBUG | Activa diagnósticos detallados; déjalo desactivado en producción. |
| HOST, PORT | Dirección y puerto donde escucha Uvicorn. Usa 0.0.0.0 dentro de contenedores. |
| ALLOWED_ORIGINS | Orígenes exactos autorizados por CORS, sin rutas. |
| FORWARDED_ALLOW_IPS | IP o CIDR de los proxies confiables que pueden enviar encabezados de IP. No configures un comodín. |
| API_PREFIX | Prefijo común de las rutas; por defecto, /api/v1. |
| SUPABASE_URL | URL del proyecto Supabase. |
| SUPABASE_PUBLISHABLE_KEY | Clave publicable usada para verificar sesiones de usuario. |
| SUPABASE_SECRET_KEY | Clave privada del servidor para operaciones administrativas de Auth y Storage. Nunca va en el frontend. |
| SUPABASE_SERVICE_ROLE_KEY | Compatibilidad temporal con proyectos que aún usan la clave service_role. Mantén solo una clave administrativa activa. |
| SUPABASE_AUTH_REDIRECT_URL | URL del frontend a la que regresan los enlaces de invitación; debe estar permitida en Supabase Auth. |
| PUBLICATION_CREATION_KEY | Clave privada compartida que autoriza solicitar invitaciones. No es necesaria para crear cada publicación una vez autenticado. |
| SUPABASE_PRODUCT_IMAGES_BUCKET | Nombre del bucket de Storage. |
| PRODUCT_IMAGE_MAX_BYTES | Tamaño máximo por imagen, en bytes. |
| PRODUCT_IMAGE_MAX_COUNT | Máximo de imágenes por producto. |
| ANNOUNCEMENT_IMAGE_MAX_COUNT | Máximo de imágenes por aviso. |
| POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD | Credenciales que Docker Compose usa solo para inicializar PostgreSQL local. |

Las variables de Supabase se pueden dejar vacías si el despliegue no usa Auth ni Storage. La API responderá que esas funciones no están configuradas cuando se soliciten.

## Desarrollo y migraciones

Desde backend:

~~~powershell
uv run task dev
uv run task lint
uv run task format
uv run task test
uv run alembic upgrade head
~~~

La prueba de migraciones requiere una base PostgreSQL local descartable. Define MIGRATION_TEST_DATABASE_URL con una base cuyo nombre incluya test; la prueba crea un esquema temporal y rechaza servidores remotos. La prueba se omite si la variable no está configurada.

Para ejecutar la API con la configuración de producción, usa uv run task start y configura HOST=0.0.0.0 si corre en un contenedor. El proxy inverso debe coincidir con FORWARDED_ALLOW_IPS.

Para cambiar el esquema, crea una revisión nueva con Alembic, inspecciona el SQL autogenerado y prueba la migración sobre una base descartable antes de aplicarla en un entorno compartido. No edites revisiones ya aplicadas. La migración de propiedad agrega cuentas e invitaciones sin borrar los avisos existentes; estos quedan sin propietario para que puedan reclamarse con su PIN.

## Adaptar esta plantilla

1. Cambia APP_NAME, APP_VERSION, PROJECT_DESCRIPTION y API_PREFIX según el proyecto.
2. Conserva solo los dominios necesarios o agrega un módulo en app/modules/nombre-del-dominio.
3. Dentro del módulo, separa modelo, esquemas Pydantic, repositorio, servicio, dependencias y rutas siguiendo product/ o announcement/.
4. Registra los modelos en app/database/models.py para que Alembic los vea y agrega el router en app/api/router.py.
5. Crea migraciones nuevas para los cambios de persistencia y añade pruebas del dominio.
6. Declara los errores nuevos como subclases de AppException en app/core/exceptions.py, con code estable y mensaje en español; no lances HTTPException desde rutas o servicios.
7. Ajusta CORS, Auth, Storage y límites de carga según el despliegue. No copies secretos entre proyectos.

Documenta cada endpoint con una docstring breve: FastAPI la publica como descripción en Swagger (/docs). Mantén las reglas de negocio en servicios y las consultas en repositorios. Evita que una ruta de FastAPI implemente directamente consultas SQL o lógica de Storage.
