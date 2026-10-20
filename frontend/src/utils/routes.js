// Rutas públicas de la aplicación web; deben coincidir con las definidas en App.jsx.

export function publicationPath(kind, id) {
  return `/${kind === 'product' ? 'productos' : 'avisos'}/${id}`;
}

export function managementPath(kind, id) {
  return `/gestionar/${kind}/${id}`;
}
