import { useContext, useState } from 'react';
import { Link } from 'react-router-dom';
import Field from '../components/Field.jsx';
import { Notice } from '../components/Feedback.jsx';
import { AuthContext } from '../App.jsx';
import { requestMagicLink, signOut } from '../services/auth.js';
import { requestAccountInvitation } from '../services/publications.js';
import { isSupabaseConfigured } from '../services/supabase.js';

export default function AccountPage() {
  const { session } = useContext(AuthContext);
  const [mode, setMode] = useState('invite');
  const [email, setEmail] = useState('');
  const [key, setKey] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    try {
      if (mode === 'invite') {
        await requestAccountInvitation(email, key);
        setKey('');
        setNotice('Solicitud aceptada. Revisa tu correo; si la cuenta ya está activa, inicia sesión.');
      } else {
        await requestMagicLink(email);
        setNotice('Si la cuenta está activa, recibirás un enlace para iniciar sesión.');
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    setError('');
    try { await signOut(); }
    catch (requestError) { setError(requestError.message); }
  }

  if (session) return (
    <section className="access-page">
      <span className="eyebrow">Tu cuenta</span>
      <h1>Hola,<br /><em>{session.user.email}</em></h1>
      <p>Tu cuenta está activa. Desde aquí puedes administrar tus publicaciones en cualquier navegador.</p>
      <Notice tone="error">{error}</Notice>
      <div className="account-actions">
        <Link className="button button-primary button-wide" to="/mis-publicaciones">Ver mis publicaciones <span aria-hidden="true">→</span></Link>
        <button className="button button-secondary button-wide" type="button" onClick={logout}>Cerrar sesión</button>
      </div>
    </section>
  );

  return (
    <section className="access-page account-page">
      <span className="eyebrow">Acceso de publicadores</span>
      <h1>Tu espacio<br /><em>para publicar.</em></h1>
      <p>{mode === 'invite' ? 'Pide una invitación con la clave que te compartió la persona administradora.' : 'Te enviaremos un enlace seguro al correo de una cuenta que ya esté activada.'}</p>
      {!isSupabaseConfigured && <Notice tone="error">Configura VITE_SUPABASE_URL y VITE_SUPABASE_PUBLISHABLE_KEY para habilitar las cuentas.</Notice>}
      <div className="account-mode-switch" role="tablist" aria-label="Acceso de cuenta">
        <button type="button" role="tab" aria-selected={mode === 'invite'} className={mode === 'invite' ? 'selected' : ''} onClick={() => { setMode('invite'); setError(''); setNotice(''); }}>Crear cuenta</button>
        <button type="button" role="tab" aria-selected={mode === 'login'} className={mode === 'login' ? 'selected' : ''} onClick={() => { setMode('login'); setError(''); setNotice(''); }}>Iniciar sesión</button>
      </div>
      <form className="access-form" onSubmit={submit}>
        <Field label="Correo electrónico" name="account-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required maxLength={254} />
        {mode === 'invite' && <Field label="Clave de invitación" name="account-invite-key" type="password" autoComplete="off" value={key} onChange={(event) => setKey(event.target.value)} required />}
        <Notice tone="error">{error}</Notice>
        <Notice>{notice}</Notice>
        <button className="button button-primary button-wide" disabled={busy || !isSupabaseConfigured}>
          {busy ? 'Enviando…' : mode === 'invite' ? 'Solicitar invitación' : 'Enviar enlace de acceso'} <span aria-hidden="true">→</span>
        </button>
      </form>
      <Link className="back-link access-back" to="/">← Volver al catálogo</Link>
    </section>
  );
}
