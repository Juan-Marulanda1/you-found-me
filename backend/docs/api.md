# Contrato HTTP

La API usa el prefijo configurado en API_PREFIX, por defecto /api/v1. Las respuestas exitosas siguen { "success": true, "message": "...", "data": ... }. Los errores usan el estándar Problem Details (RFC 9457), descrito en la sección [Errores](#errores). Los detalles de cada esquema se publican también en /docs.

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
| GET | /products | Público | Buscar y paginar productos activos; permite filtros de ciudad, categoría, texto y precio. El precio de un producto debe ser de al menos 1000. |
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

## Errores

Todos los errores responden con `Content-Type: application/problem+json` según el [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457). Los textos están en español y pensados para mostrarse a quien usa la aplicación.

~~~json
{
  "type": "about:blank",
  "title": "Datos no válidos",
  "status": 422,
  "detail": "«admin_pin»: Debe tener al menos 4 caracteres.",
  "instance": "/api/v1/products/7c1e.../manage",
  "code": "validation_error",
  "errors": [
    { "field": "admin_pin", "location": "body", "message": "Debe tener al menos 4 caracteres." }
  ]
}
~~~

| Miembro | Significado |
| --- | --- |
| type | Siempre about:blank: el tipo de problema se identifica con code. |
| title | Frase del estado HTTP en español. |
| status | Código HTTP, igual al de la respuesta. |
| detail | Explicación concreta para mostrar al usuario. |
| instance | Ruta de la solicitud que falló. |
| code | Extensión: identificador estable en snake_case. Los clientes deben decidir con este valor, nunca comparando detail. |
| errors | Extensión, solo en 422 de validación: field (null si el error es del cuerpo completo), location (body, query, path o header) y message. |

Las respuestas 401 incluyen `WWW-Authenticate: Bearer` y las 405 incluyen `Allow`. Los errores 500 no exponen detalles internos; el detalle técnico queda en los logs.

| code | Estado | Cuándo ocurre |
| --- | --- | --- |
| validation_error | 422 | Un campo, parámetro o cuerpo no cumple el contrato. |
| bad_request | 400 | La solicitud no tiene un formato válido. |
| not_found | 404 | La ruta no existe. |
| method_not_allowed | 405 | El método HTTP no aplica a la ruta. |
| publication_not_found | 404 | La publicación no existe, no está activa o pertenece a otra cuenta. |
| invalid_price_range | 422 | min_price es mayor que max_price. |
| invalid_admin_pin | 403 | El PIN heredado es incorrecto o falta. |
| too_many_pin_attempts | 429 | Se superó el límite de intentos de PIN. |
| authentication_required | 401 | Falta la sesión o el token no es válido. |
| email_not_confirmed | 403 | El correo de la cuenta no está confirmado. |
| account_not_invited | 403 | El correo no figura en la lista de invitaciones. |
| invalid_invitation_key | 403 | X-Publication-Key es incorrecta o falta. |
| account_already_exists | 409 | Supabase ya tiene una cuenta con ese correo. |
| email_not_invitable | 422 | Supabase rechazó el correo. |
| too_many_invitations | 429 | Supabase limitó el envío de invitaciones. |
| image_not_found | 404 | La imagen no existe o no pertenece a la publicación. |
| image_limit_reached | 409 | La publicación alcanzó su máximo de imágenes, contando las pendientes. |
| image_upload_pending | 409 | Se confirmó una imagen que aún no está en Storage. |
| invalid_image | 422 | Tipo o tamaño no permitido, o el archivo no coincide con lo declarado. |
| auth_not_configured, invitations_not_configured, invitation_key_not_configured | 503 | Falta configuración del servidor. |
| auth_unavailable, invitations_unavailable, image_storage_unavailable | 503 | Supabase no respondió o falló. |
| internal_error | 500 | Error no previsto. |

Para agregar un error, crea una subclase de AppException en app/core/exceptions.py con status_code, code y detail en español; el manejador global lo convierte sin más cambios. tests/test_errors.py verifica que cada error tenga un código válido y un mensaje en español.
