export function Notice({ children, tone = 'info' }) {
  if (!children) return null;
  return <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>{children}</div>;
}

export function Busy({ children = 'Cargando…' }) {
  return <div className="busy-state"><span className="spinner" aria-hidden="true" />{children}</div>;
}
