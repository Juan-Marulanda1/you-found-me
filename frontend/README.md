# You Found Me - frontend

Frontend React + Vite para el catalogo publico de productos y avisos.

## Iniciar en local

1. Instala Node.js 22.12 o superior.
2. Desde frontend, ejecuta npm install.
3. Copia .env.example como .env.local y configura las variables.
4. Inicia la API y ejecuta npm run dev.
5. Abre http://localhost:5173.

Las variables VITE_* son visibles en el navegador. Solo configura la URL de Supabase y su clave publicable. Nunca pongas SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY ni PUBLICATION_CREATION_KEY en el frontend.

## Variables

| Variable | Uso |
| --- | --- |
| VITE_API_BASE_URL | URL base de FastAPI, incluyendo /api/v1. |
| VITE_SUPABASE_URL | URL publica de Supabase para Auth y carga de imagenes firmadas. |
| VITE_SUPABASE_PUBLISHABLE_KEY | Clave publicable para Supabase Auth y Storage. |

## Cuentas e invitaciones

La ruta /cuenta permite pedir una invitacion o iniciar sesion con un enlace de correo. Para pedir cuenta se necesita PUBLICATION_CREATION_KEY; el frontend la envia una vez a POST /account-access/invite y no la guarda. Supabase Auth envia el enlace. Para iniciar sesion se usa un enlace de correo sin crear cuentas nuevas.

Configura en el backend SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY y SUPABASE_AUTH_REDIRECT_URL. Agrega la URL de redireccion a Authentication > URL Configuration en Supabase. Deshabilita el registro publico si el acceso debe ser solo por invitacion.

La API envia el token de sesion como Authorization: Bearer. Las publicaciones nuevas quedan asociadas a la identidad del usuario. Tus publicaciones consulta el backend, asi que se sincroniza entre dispositivos. Las publicaciones anteriores se pueden reclamar desde una cuenta con correo confirmado y validando cada PIN. Las publicaciones antiguas sin correo coincidente se pueden abrir con una referencia local previa y reclamar con su PIN.

## Estado y siguientes pasos

- Catalogo publico de productos y avisos, busqueda y paginacion.
- Privacidad para correo y direccion exacta; el telefono publico depende del consentimiento.
- Publicacion y administracion asociadas a una cuenta invitada.
- Reclamacion de publicaciones existentes con PIN, conservando sus datos y hashes.
- Imagenes en Supabase Storage con URL firmada.

Antes de desplegar, configura los remitentes de correo de Supabase y las URL de redireccion de cada entorno. Valida con datos de prueba que los avisos existentes sigan visibles y se puedan reclamar.

## Estructura

- src/pages: pantallas de catalogo, detalle, cuenta, publicacion y gestion.
- src/services: cliente HTTP, Auth, endpoints del dominio, Storage y referencias locales.
- src/components: campos, tarjetas y estados visuales.
- src/utils: formato de precios, fechas y etiquetas.
