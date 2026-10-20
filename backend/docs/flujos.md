# Flujos del backend

## Capas de una solicitud

~~~mermaid
flowchart LR
    C[Cliente web o integracion] --> M[FastAPI: CORS y manejadores]
    M --> R[Router de API]
    R --> V[Validacion Pydantic y dependencias]
    V --> S[Servicio del dominio]
    S --> RP[Repositorio SQLAlchemy]
    RP --> DB[(PostgreSQL)]
    S --> I[Adaptador de integracion]
    I --> SB[Supabase Auth o Storage]
    V -->|error| EH[Respuesta de error uniforme]
    S -->|error de dominio| EH
    EH --> C
    DB --> C
~~~

1. app/main.py crea la aplicación, configura CORS y registra los manejadores globales de excepciones.
2. app/api/router.py incorpora los routers de cuenta, productos y avisos bajo API_PREFIX.
3. Cada router valida ruta, query y cuerpo con FastAPI y Pydantic, y resuelve servicios mediante dependencias.
4. El servicio aplica reglas de negocio y usa repositorios para consultar o cambiar el estado persistido.
5. get_db abre una sesión SQLAlchemy por solicitud y la cierra al terminar.
6. Las respuestas exitosas usan el formato success/message/data. Los errores de dominio, HTTP y validación se transforman en Problem Details (RFC 9457) con mensajes en español. Las excepciones no previstas se registran en el servidor y devuelven un mensaje genérico.

## Invitación, sesión y propiedad

~~~mermaid
sequenceDiagram
    participant P as Publicador
    participant W as Frontend
    participant A as API
    participant S as Supabase Auth
    participant D as PostgreSQL
    P->>W: Correo y clave de invitacion
    W->>A: POST /account-access/invite + X-Publication-Key
    A->>A: Compara la clave en tiempo constante
    A->>S: Solicita invitacion por correo
    A->>D: Guarda el correo autorizado
    S-->>P: Enlace de invitacion
    P->>S: Confirma correo e inicia sesion
    W->>A: Solicitud con token Bearer
    A->>S: Valida token y correo confirmado
    A->>D: Comprueba invitacion y registra identidad
    A-->>W: Operacion autorizada
~~~

La clave compartida solo autoriza solicitar invitaciones; las rutas de creación no la reciben. La API comprueba la sesión contra Supabase Auth y luego exige que el correo confirmado esté en publication_invitations. Al crear la primera publicación, guarda el identificador autenticado como owner_id. Las operaciones de una publicación nueva se autorizan por propietario.

Los registros anteriores a la propiedad conservan owner_id nulo y sus hashes de PIN. La lista de cuenta ofrece los registros cuyo correo de contacto coincide; POST /account-access/me/claim valida el PIN antes de asignar owner_id. Los PIN antiguos siguen habilitando la gestión de registros que aún no se han reclamado.

## Imágenes

~~~mermaid
sequenceDiagram
    participant W as Navegador
    participant A as API
    participant D as PostgreSQL
    participant S as Supabase Storage
    W->>A: Solicita URL firmada con sesion
    A->>A: Autoriza propietario o PIN antiguo
    A->>D: Guarda carga pendiente y metadatos esperados
    A->>S: Pide capacidad firmada de subida
    A-->>W: Ruta y token temporal
    W->>S: Sube archivo directamente
    W->>A: Confirma image_id
    A->>S: Verifica existencia, tipo y tamaño reales
    A->>D: Marca la imagen como lista
~~~

La API no retransmite el archivo. Supabase Storage entrega una capacidad temporal limitada a una ruta; al confirmar, el backend consulta los metadatos almacenados y solo marca como lista la imagen cuyo tamaño y tipo coinciden con lo esperado (Supabase informa el tipo en content_type). Las imágenes pendientes no se exponen en el catálogo.

## Catálogo y administración

Las rutas públicas de lista filtran por estado activo y devuelven esquemas públicos que omiten correo y dirección exacta. El teléfono se incluye solo si el autor dio consentimiento. Las rutas de administración devuelven un esquema separado y requieren el dueño autenticado o el PIN de un registro heredado.

La IP para los intentos de PIN procede de request.client.host. Uvicorn solo debe confiar encabezados reenviados desde las direcciones declaradas en FORWARDED_ALLOW_IPS.

El limitador de PIN vive en memoria por proceso: un reinicio borra sus contadores y varias instancias no comparten bloqueos. Para escalar la API, mueve ese estado a Redis o al proxy de entrada.

## Errores y observabilidad

Las rutas, dependencias y servicios lanzan subclases de AppException (core/exceptions.py), cada una con estado HTTP, code estable y mensaje en español. Los manejadores de core/exception_handlers.py las convierten, junto con los errores del framework (404, 405) y los de validación de Pydantic, en respuestas application/problem+json construidas por core/problems.py. Los errores de validación se traducen campo por campo según el tipo de error de Pydantic. Los errores inesperados se registran con la ruta y el detalle técnico queda en los logs, no en la respuesta pública. El contrato completo y la lista de códigos están en [api.md](api.md#errores).

Los adaptadores de Supabase aíslan el protocolo del proveedor. Si se sustituye Supabase, se puede cambiar esa integración conservando los contratos de los servicios, siempre que el nuevo adaptador cumpla las mismas operaciones.
