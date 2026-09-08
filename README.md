# You Found Me

API para publicar y consultar avisos de objetos, mascotas o personas perdidas y encontradas. Cada aviso puede incluir información de contacto y un PIN de administración de cuatro dígitos para autorizar su eliminación, sin necesidad de crear una cuenta.

> El backend está funcional. El frontend todavía se encuentra en una etapa inicial y no incluye una interfaz implementada.

## Funcionalidades actuales

- Crear avisos de tipo `LOST` o `FOUND`.
- Consultar un aviso por su UUID.
- Listar todos los avisos.
- Eliminar un aviso mediante su PIN de administración.
- Estados de aviso: `OPEN`, `RESOLVED` y `CLOSED`.
- Validación de datos con Pydantic.
- Persistencia en PostgreSQL con SQLAlchemy.
- Migraciones de base de datos con Alembic.
- Documentación interactiva OpenAPI/Swagger generada por FastAPI.

## Tecnologías

- Python 3.12+
- FastAPI y Uvicorn
- SQLAlchemy 2
- PostgreSQL y `psycopg`
- Alembic
- Pydantic Settings
- `uv` para dependencias y tareas
- Ruff para linting y formateo
- React, como base del frontend en desarrollo

## Estructura

```text
you-found-me/
├── backend/
│   ├── app/
│   │   ├── api/                 # Router principal
│   │   ├── core/                # Configuración y respuestas comunes
│   │   ├── database/            # Sesión, modelos base y mixins
│   │   └── modules/announcement/ # Avisos: rutas, servicio, repositorio y esquemas
│   ├── alembic/                 # Migraciones
│   ├── .env.example             # Plantilla de configuración
│   └── pyproject.toml           # Dependencias y tareas
└── frontend/                    # Cliente React en construcción
```

## Requisitos

- Python 3.12 o superior
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL disponible localmente o mediante un proveedor

## Instalación y ejecución

Desde la raíz del repositorio:

```bash
cd backend
uv sync
```

Crea tu archivo local de variables de entorno a partir de la plantilla:

```bash
cp .env.example .env
```

En Windows PowerShell, usa `Copy-Item .env.example .env`. Completa al menos `DATABASE_URL` en `.env`:

```env
APP_NAME=You Found Me API
APP_VERSION=1.0.0
DEBUG=True
DATABASE_URL=postgresql+psycopg://usuario:contrasena@localhost:5432/you_found_me
API_PREFIX=/api/v1
ALLOWED_ORIGINS=["http://localhost:3000"]
```


Aplica las migraciones y levanta el servidor:

```bash
uv run alembic upgrade head
uv run task dev
```

La API estará disponible en `http://localhost:8000`. La documentación se encuentra en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API

El prefijo actual es `/api/v1` y todas las respuestas usan una envoltura con `message` y `data`.

| Método   | Ruta                                      | Descripción                          |
| -------- | ----------------------------------------- | ------------------------------------ |
| `POST`   | `/api/v1/announcements`                   | Crea un aviso.                       |
| `GET`    | `/api/v1/announcements`                   | Lista los avisos.                    |
| `GET`    | `/api/v1/announcements/{announcement_id}` | Obtiene un aviso por UUID.           |
| `DELETE` | `/api/v1/announcements/{announcement_id}` | Elimina un aviso usando `admin_pin`. |

### Crear un aviso

```bash
curl -X POST http://localhost:8000/api/v1/announcements \
	-H "Content-Type: application/json" \
	-d '{
		"title": "Perro encontrado en Laureles",
		"description": "Perro mediano, color café, encontrado cerca del parque.",
		"type": "FOUND",
		"admin_pin": "1234",
		"contact_name": "Ana Pérez",
		"contact_phone": "3001234567",
		"city": "Medellín",
		"address": "Carrera 76 #34-20"
	}'
```

El campo `admin_pin` debe contener exactamente cuatro dígitos. Los campos `title`, `description`, `contact_name`, `contact_phone` y `city` también tienen validaciones de longitud; la documentación de Swagger muestra el contrato completo.

### Eliminar un aviso

```bash
curl -X DELETE http://localhost:8000/api/v1/announcements/<UUID> \
	-H "Content-Type: application/json" \
	-d '{"admin_pin": "1234"}'
```

## Tareas de desarrollo

Ejecuta estos comandos desde `backend/`:

```bash
uv run task dev      # Servidor con recarga automática
uv run task start    # Servidor sin recarga
uv run task lint     # Comprueba el código con Ruff
uv run task format   # Formatea el código
uv run task check    # Aplica correcciones automáticas de Ruff
```

## Próximos pasos

- [ ] Implementar la interfaz web de React.
- [ ] Añadir actualización de avisos mediante `PATCH`.
- [ ] Incorporar filtros por ciudad, tipo y estado.
- [ ] Añadir subida de imágenes.
- [ ] Añadir pruebas automatizadas para la API.
- [ ] Añadir autenticación o un mecanismo más robusto que el PIN de cuatro dígitos.

## Contribuir

1. Crea una rama para tu cambio: `git checkout -b feature/nombre-del-cambio`.
2. Instala las dependencias y ejecuta `uv run task lint`.
3. Haz un commit descriptivo.
4. Abre un Pull Request con el contexto y las pruebas realizadas.

## Licencia

Este proyecto todavía no tiene una licencia definida.
