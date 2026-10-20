# You Found Me

You Found Me es un monorepositorio con dos aplicaciones coordinadas: una API para productos y avisos, y un frontend para explorar, publicar y administrar esos contenidos. La API conserva los límites entre los dominios de producto y anuncio, para que el proyecto pueda adaptarse como plantilla a otros catálogos o sitios de venta.

## Aplicaciones

| Aplicación | Tecnologías | Guía |
| --- | --- | --- |
| API | Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL y Alembic | [backend/README.md](backend/README.md) |
| Web | Node.js 22.12+, React y Vite | [frontend/README.md](frontend/README.md) |

## Estructura del repositorio

~~~text
backend/
  app/             API, reglas de negocio, persistencia e integraciones
  alembic/         historial de migraciones SQL
  tests/           pruebas automatizadas del backend
  docs/            flujos y contrato de la API
frontend/
  src/             aplicación React
  docs/            flujos de la aplicación web
docker-compose.yml PostgreSQL local para desarrollo
~~~

## Inicio rápido

Clona el repositorio y entra en su carpeta:

~~~sh
git clone URL_DEL_REPOSITORIO mi-proyecto
cd mi-proyecto
~~~

1. Configura el backend siguiendo [su guía](backend/README.md#instalacion-local).
2. Configura el frontend siguiendo [su guía](frontend/README.md#instalacion-local).
3. Abre la aplicación web en http://localhost:5173. La API y su contrato OpenAPI están en http://localhost:8000/docs.

No compartas archivos .env. Usa los archivos .env.example como referencia y guarda las credenciales privadas solo en el entorno del backend.

## Usar como plantilla

Empieza con una copia completa de este repositorio. Renombra la marca y la configuración de la aplicación, define los dominios que conservarás y adapta los módulos del backend y las pantallas del frontend. La [guía del backend](backend/README.md#adaptar-esta-plantilla) y la [guía del frontend](frontend/README.md#adaptar-esta-plantilla) describen los puntos de extensión.

Las migraciones aplicadas son parte del historial de datos: para adaptar el esquema crea migraciones nuevas; no edites una migración que ya se haya ejecutado en una base compartida.

## Flujos y contrato

- [Flujos del backend](backend/docs/flujos.md)
- [Contrato HTTP de la API](backend/docs/api.md)
- [Flujos del frontend](frontend/docs/flujos.md)
