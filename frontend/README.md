# You Found Me Web

Aplicación React para explorar productos y avisos, crear publicaciones y administrar publicaciones asociadas a una cuenta.

## Arquitectura

~~~text
frontend/src/
  App.jsx              Rutas y estado de sesión de Supabase Auth
  pages/               Pantallas de catálogo, detalle, cuenta, publicación y gestión
  components/          Elementos visuales reutilizables
  services/            Cliente HTTP, Auth, Storage y referencias locales
  utils/               Formatos, etiquetas de estado y rutas internas (routes.js)
  styles.css           Estilos globales y de componentes
~~~

Las páginas coordinan el estado de pantalla y llaman a los servicios. services/api.js adjunta el token de sesión a la API y convierte los errores Problem Details en ApiError; los servicios de publicaciones conocen las rutas HTTP, y imageUpload.js coordina la carga firmada en Supabase Storage. Consulta [docs/flujos.md](docs/flujos.md) para los diagramas de sesión, solicitudes e imágenes.

## Requisitos

- Node.js 22.12 o superior.
- npm incluido con Node.js.
- El backend disponible en la URL configurada.
- Un proyecto Supabase si se usan cuentas o imágenes.

## Instalación local

Desde la raíz del repositorio, copia frontend/.env.example como frontend/.env.local. Luego:

~~~powershell
cd frontend
npm ci
npm run dev
~~~

Abre http://localhost:5173. Para iniciar la API y PostgreSQL, sigue [backend/README.md](../backend/README.md#instalacion-local).

Para compilar y servir una vista previa local:

~~~powershell
npm run build
npm run preview
~~~

## Variables del frontend

| Variable | Uso |
| --- | --- |
| VITE_API_BASE_URL | URL base de la API, incluyendo /api/v1. |
| VITE_SUPABASE_URL | URL pública del proyecto Supabase. |
| VITE_SUPABASE_PUBLISHABLE_KEY | Clave publicable de Supabase Auth y Storage. Puede estar en el frontend. |

Todo valor VITE_* queda incluido en el código descargado por el navegador. Nunca agregues PUBLICATION_CREATION_KEY, SUPABASE_SECRET_KEY ni SUPABASE_SERVICE_ROLE_KEY a este archivo.

## Cuentas e invitaciones

1. La persona administradora entrega la clave privada de invitación a quien autoriza.
2. El invitado abre /cuenta, elige Crear cuenta e ingresa su correo y la clave.
3. La API valida la clave, registra el correo autorizado y pide a Supabase Auth que envíe una invitación.
4. El invitado abre el enlace de correo y vuelve a /cuenta con la sesión iniciada.
5. Las publicaciones nuevas se asocian a esa cuenta; Tus publicaciones puede consultarse desde otros dispositivos.

Para volver a entrar se solicita un enlace de acceso desde Iniciar sesión. El PIN solo se necesita para reclamar publicaciones antiguas que aún no tengan dueño asignado. La clave de invitación se comparte con cuidado: quien la tenga puede autorizar solicitudes de invitación. Cambiarla impide solicitudes futuras con el valor anterior, pero no revoca las cuentas ya autorizadas.

En Supabase Auth, permite las URL de regreso de desarrollo y producción y configura el envío de correo apropiado para el volumen esperado. Deshabilitar el registro público complementa la lista de invitaciones que aplica la API.

## Adaptar esta plantilla

1. Actualiza el título y la descripción en index.html, la marca y textos de las páginas, y los estilos en src/styles.css.
2. Ajusta VITE_API_BASE_URL y las credenciales publicables de Supabase para cada entorno.
3. Agrega o cambia pantallas en src/pages y componentes reutilizables en src/components.
4. Agrega las llamadas HTTP en src/services y mantén la lógica de presentación en las páginas. Las URL internas se construyen con src/utils/routes.js y las etiquetas de estado con src/utils/format.js.
5. Si cambias los límites de imágenes del backend, actualiza MAX_IMAGES y MAX_BYTES en src/services/imageUpload.js. El ancho mínimo recomendado (MIN_RECOMMENDED_WIDTH) solo genera un aviso. Los mensajes de error llegan en español desde la API; si agregas campos nuevos, añade su etiqueta en FIELD_LABELS de src/services/api.js.
6. Si se cambia el dominio del backend, coordina sus rutas y esquemas con la API y actualiza su contrato.
7. Ejecuta npm run build antes de publicar y configura el hosting para servir index.html también en rutas internas como /cuenta y /mis-publicaciones.

No incluyas claves administrativas ni lógica de autorización secreta en el bundle web. La API es quien decide si la sesión puede publicar o administrar contenido.
