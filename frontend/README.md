# You Found Me — frontend

Frontend React + Vite para el catálogo público de productos y avisos. La interfaz y los textos están en español.

## Iniciar en local

1. Instala Node.js 22.12 o superior.
2. Desde `frontend`, ejecuta `npm install`.
3. Copia `.env.example` como `.env.local` y configura las variables de frontend.
4. Inicia la API con su configuración local y ejecuta `npm run dev`.
5. Abre `http://localhost:5173`.

Vite carga las variables `VITE_*` durante la compilación. Son visibles en el navegador: aquí solo deben ir la URL de Supabase y su clave publicable. La clave secreta de Supabase, la clave de publicación y la configuración JWKS pertenecen exclusivamente al backend; el navegador no verifica tokens de Supabase.

## Variables del frontend

| Variable | Uso |
| --- | --- |
| `VITE_API_BASE_URL` | URL base de FastAPI, incluyendo `/api/v1`. |
| `VITE_SUPABASE_URL` | URL pública del proyecto; se usa para cargar imágenes mediante una URL firmada emitida por la API. |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Clave publicable para inicializar el cliente de Storage. Las políticas y las URLs firmadas limitan las operaciones; nunca poner aquí la clave secreta/service role. |

La configuración local del usuario vive en `.env.local`, que no se incluye en Git. `SUPABASE_JWKS_URL` no es necesaria para este frontend.

## Acceso para crear publicaciones

El botón de publicar abre una pantalla que pide una clave compartida. La API la valida con `POST /publication-access/verify` y también protege `POST /products` y `POST /announcements` con el encabezado `X-Publication-Key`. La clave se guarda solo en la memoria de la aplicación mientras está abierta y nunca se compila en el bundle.

Configura `PUBLICATION_CREATION_KEY` en el entorno privado del backend (`backend/.env` en local y el gestor de secretos al desplegar). Si falta, el backend rechaza las verificaciones y la creación con `503`. Comparte esa clave solo con quienes puedan publicar. Esta puerta controla la creación, pero es una clave compartida: no identifica a cada persona ni reemplaza un sistema de usuarios.

## Límites actuales y siguiente plan

### Entrega 1 — MVP implementado

- Catálogo público separado en productos y avisos, búsqueda por texto, ciudad y categoría, y paginación.
- Página de detalle con privacidad del teléfono sujeta a consentimiento; correo y dirección exacta permanecen ocultos.
- Formulario de publicación protegido por clave del backend y PIN por publicación.
- “Tus publicaciones” conserva solo tipo e identificador en el almacenamiento local del navegador; pide el PIN antes de abrir la administración.
- Edición, cambio de estado, rotación del PIN y eliminación con el PIN.
- Imágenes de productos y avisos subidas desde el navegador al bucket Supabase con URL firmada; las credenciales de servicio permanecen en la API. Los avisos admiten una imagen.

### Entrega 2 — validar con el entorno real

- Configurar la clave de publicación en local y en el entorno de despliegue.
- Arrancar frontend y API con el proyecto Supabase real; publicar un producto y un aviso de prueba.
- Confirmar carga, visualización y borrado de imágenes, además de los permisos del bucket.
- Revisar que una sesión sin clave no pueda crear publicaciones y que la API responda con mensajes claros.
- Verificar móvil, teclado, contraste y errores de red con la persona que administra el sitio.

### Entrega 3 — preparar catálogo reutilizable

- Definir configuración por sitio (marca, categorías, moneda y tipos de publicación) sin duplicar el cliente HTTP ni los formularios.
- Decidir si cada página derivada tendrá su propia clave de creación o si la clave pasará a un panel de administración con usuarios y roles.
- Evaluar si “Tus publicaciones” debe sincronizarse entre dispositivos. Hoy es una lista local; borrar los datos del navegador elimina las referencias, aunque los avisos se conservan en la API.
- Añadir moderación, reporte de avisos y políticas de retención antes de abrir la creación a un público amplio.

## Estructura

- `src/pages`: pantallas y flujos de catálogo, detalle, publicación y gestión.
- `src/services`: cliente HTTP, endpoints del dominio, Storage y referencias locales.
- `src/components`: campos, tarjetas y estados visuales reutilizables.
- `src/utils`: formato de precios, fechas y etiquetas.
