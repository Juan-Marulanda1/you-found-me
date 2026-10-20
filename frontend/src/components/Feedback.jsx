// Mensaje informativo o de error; no renderiza nada si no hay contenido.
export function Notice({ children, tone = 'info' }) {
  if (!children) return null;
  return <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>{children}</div>;
}

// Indicador de carga con texto accesible.
export function Busy({ children = 'Cargando…' }) {
  return <div className="busy-state"><span className="spinner" aria-hidden="true" />{children}</div>;
}
