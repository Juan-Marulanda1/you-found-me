# Flujos del frontend

## Sesión e invitaciones

~~~mermaid
sequenceDiagram
    participant P as Publicador
    participant W as Aplicacion React
    participant A as API
    participant S as Supabase Auth
    P->>W: Abre /cuenta y escribe correo y clave
    W->>A: POST /account-access/invite
    A->>S: Envia invitacion si la clave es valida
    S-->>P: Correo con enlace
    P->>S: Abre el enlace
    S-->>W: Regresa a /cuenta con sesion
    W->>W: Actualiza AuthContext
    P->>W: Abre Tus publicaciones o Publicar
~~~

AccountPage.jsx presenta la solicitud de invitación y el acceso por enlace de correo. La clave se conserva solo en el estado temporal del formulario y se envía a la API en el encabezado X-Publication-Key; no se guarda en localStorage ni en el bundle. Al cargar la app y al cambiar el estado de Supabase Auth, App.jsx actualiza AuthContext.

## Solicitudes a la API

~~~mermaid
flowchart LR
    P[Pagina] --> D[Servicio de dominio]
    D --> H[services/api.js]
    H --> T[Obtiene token de sesion]
    T --> F[fetch a FastAPI]
    F -->|Authorization Bearer si existe| A[API]
    A --> R[JSON de respuesta]
    R --> N[Traduccion de errores y estado de pagina]
~~~

El cliente HTTP adjunta el token de Supabase cuando hay sesión, convierte errores de red y HTTP en ApiError y entrega el campo data a la página. Los servicios de publicaciones concentran las rutas; no deben duplicarse en componentes.

## Publicación y administración

Una ruta de publicación sin sesión muestra el acceso a cuenta. Con sesión, PublishPage valida los campos, crea la publicación mediante la API y luego carga las imágenes seleccionadas. La API asocia el nuevo registro a la identidad del token.

MyPublicationsPage consulta las publicaciones del servidor para que la lista funcione entre dispositivos. Las publicaciones anteriores pueden aparecer como reclamables y requieren validar su PIN antes de asociarse a la cuenta. ManagePage usa la sesión del propietario para registros nuevos y conserva el PIN para administrar publicaciones antiguas que todavía no se han reclamado.

El almacenamiento local contiene referencias de compatibilidad y vistas previas, no credenciales ni autoridad de acceso. La autorización siempre se decide en el backend.

## Carga de imágenes

El servicio imageUpload.js solicita primero una ruta firmada a la API, carga el archivo directamente a Supabase Storage y llama al endpoint de confirmación. Si falla la carga, la API puede conservar un registro pendiente para que la pantalla de gestión permita reintentar o limpiar la operación.

La clave de Storage presente en el frontend es publicable. La firma de cargas y las operaciones administrativas usan credenciales del backend y no deben trasladarse al navegador.
