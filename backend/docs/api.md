# Contrato HTTP

La API usa el prefijo configurado en API_PREFIX, por defecto /api/v1. Las respuestas exitosas siguen { "success": true, "message": "...", "data": ... }; los errores usan success=false y message. Los detalles de cada esquema se publican también en /docs.

## Autenticación

- Las rutas públicas de lectura no requieren sesión.
- Crear productos o avisos y administrar publicaciones propias requiere un token de sesión en Authorization: Bearer.
- POST /account-access/invite requiere X-Publication-Key. La clave autoriza la invitación, no se usa para cada publicación.
- Los endpoints de gestión admiten PIN para conservar el acceso a publicaciones antiguas aún no reclamadas.

## Cuentas

| Método | Ruta | Acceso | Uso |
| --- | --- | --- | --- |
| POST | /account-access/invite | X-Publication-Key | Invitar un correo y agregarlo a la lista autorizada. |
| GET | /account-access/me/publications | Sesión | Listar publicaciones propias y antiguas que podrían reclamarse por correo. |
| POST | /account-access/me/claim | Sesión y PIN | Reclamar una publicación antigua. Cuerpo: kind, publication_id, admin_pin. |

## Productos

| Método | Ruta | Acceso | Uso |
| --- | --- | --- | --- |
| POST | /products | Sesión | Crear producto y asociarlo al usuario. |
| GET | /products | Público | Buscar y paginar productos activos; permite filtros de ciudad, categoría, texto y precio. |
| GET | /products/{product_id} | Público | Consultar producto activo. |
| POST | /products/{product_id}/manage | Propietario o PIN heredado | Obtener datos de administración. |
| PATCH | /products/{product_id} | Propietario o PIN heredado | Editar datos o estado. |
| DELETE | /products/{product_id} | Propietario o PIN heredado | Eliminar producto y sus archivos asociados. |

## Avisos

| Método | Ruta | Acceso | Uso |
| --- | --- | --- | --- |
| POST | /announcements | Sesión | Crear aviso y asociarlo al usuario. |
| GET | /announcements | Público | Buscar y paginar avisos activos. |
| GET | /announcements/{announcement_id} | Público | Consultar aviso activo. |
| POST | /announcements/{announcement_id}/manage | Propietario o PIN heredado | Obtener datos de administración. |
| PATCH | /announcements/{announcement_id} | Propietario o PIN heredado | Editar datos o estado. |
| DELETE | /announcements/{announcement_id} | Propietario o PIN heredado | Eliminar aviso y sus archivos asociados. |

## Imágenes

La API usa las rutas correspondientes bajo /products/{id}/images y /announcements/{id}/images:

| Método | Sufijo de ruta | Acceso | Uso |
| --- | --- | --- | --- |
| POST | /upload-url | Propietario o PIN heredado | Crear metadatos pendientes y recibir capacidad de carga firmada. |
| POST | /{image_id}/complete | Propietario o PIN heredado | Verificar el archivo subido y marcarlo como listo. |
| GET | / | Público | Listar imágenes confirmadas de una publicación activa. |
| POST | /manage | Propietario o PIN heredado | Listar imágenes, incluso cargas pendientes, para administración. |
| DELETE | /{image_id} | Propietario o PIN heredado | Borrar metadatos y objeto de Storage. |

La subida de bytes se hace directamente desde el navegador a Supabase Storage. Cada producto admite hasta PRODUCT_IMAGE_MAX_COUNT imágenes; cada aviso, ANNOUNCEMENT_IMAGE_MAX_COUNT. Los tipos aceptados y el máximo de bytes están definidos en el backend.

## Privacidad y estados

Las respuestas públicas no incluyen correo ni dirección exacta. El teléfono solo aparece si contact_phone_public es true. Los productos usan estados ACTIVE, SOLD y CLOSED; los avisos, ACTIVE, PAUSED y CLOSED. Las búsquedas públicas solo incluyen registros activos.

Los esquemas públicos, administrativos y de escritura son distintos para evitar filtrar datos privados o hashes de PIN. Consulta OpenAPI en /docs para los tipos, restricciones y ejemplos vigentes.
