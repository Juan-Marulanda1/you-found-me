import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Field from '../components/Field.jsx';
import { Busy, Notice } from '../components/Feedback.jsx';
import { deletePublication, deletePublicationImage, getPublicationForManagement, listPublicationImagesForManagement, updatePublication } from '../services/publications.js';
import { uploadPublicationImage } from '../services/imageUpload.js';
import { forgetPublication, rememberPublication } from '../services/publicationRefs.js';
import { formatDate, formatPrice, kindLabel } from '../utils/format.js';

function editableFields(kind, item) {
  return {
    title: item.title || '', description: item.description || '', category: item.category || '',
    city: item.city || '', contact_name: item.contact_name || '', contact_phone: item.contact_phone || '',
    contact_email: item.contact_email || '', address: item.address || '',
    contact_phone_public: Boolean(item.contact_phone_public), status: item.status || 'ACTIVE',
    ...(kind === 'product' ? { price: String(item.price), currency: item.currency, quantity: item.quantity ?? '' } : {
      business_name: item.business_name || '', website_url: item.website_url || '',
    }),
  };
}

export default function ManagePage() {
  const { kind, id } = useParams();
  const navigate = useNavigate();
  const validKind = ['product', 'announcement'].includes(kind);
  const [pin, setPin] = useState('');
  const [item, setItem] = useState(null);
  const [form, setForm] = useState(null);
  const [images, setImages] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const maxImageCount = kind === 'product' ? 8 : 1;

  useEffect(() => {
    if (!validKind) setError('El tipo de publicación no es válido.');
  }, [validKind]);

  async function loadManagement(event) {
    event?.preventDefault();
    setBusy(true);
    setError('');
    try {
      const data = await getPublicationForManagement(kind, id, pin);
      setItem(data);
      setForm(editableFields(kind, data));
      try { rememberPublication(kind, id); } catch { /* Browser storage is optional for managing this publication. */ }
      setLoaded(true);
      try { setImages(await listPublicationImagesForManagement(kind, id, pin)); }
      catch { setNotice('La publicación abrió correctamente, pero no pudimos cargar sus imágenes.'); }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  function change(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
  }

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    const body = {
      admin_pin: pin,
      title: form.title.trim(), description: form.description.trim(), category: form.category.trim(),
      city: form.city.trim(), contact_name: form.contact_name.trim(), contact_phone: form.contact_phone.trim(),
      contact_email: form.contact_email.trim() || null, address: form.address.trim() || null,
      contact_phone_public: form.contact_phone_public, status: form.status,
    };
    if (kind === 'product') {
      body.price = Number(form.price);
      body.currency = form.currency;
      body.quantity = form.quantity === '' ? null : Number(form.quantity);
    } else {
      body.business_name = form.business_name.trim() || null;
      body.website_url = form.website_url.trim() || null;
    }

    try {
      const newPin = form.new_admin_pin?.trim();
      if (newPin) body.new_admin_pin = newPin;
      const saved = await updatePublication(kind, id, body);
      if (newPin) setPin(newPin);
      setItem(saved);
      setForm(editableFields(kind, saved));
      setNotice('Cambios guardados.');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function removePublication() {
    if (!window.confirm('¿Quieres borrar esta publicación y sus imágenes? Esta acción no se puede deshacer.')) return;
    setBusy(true);
    setError('');
    try {
      await deletePublication(kind, id, pin);
      forgetPublication(kind, id);
      navigate('/mis-publicaciones', { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function addImages(event) {
    const files = Array.from(event.target.files || []).slice(0, maxImageCount);
    event.target.value = '';
    if (!files.length) return;
    setBusy(true);
    setError('');
    const failures = [];
    for (const file of files) {
      try { await uploadPublicationImage(kind, id, file, pin); }
      catch (uploadError) { failures.push(`${file.name}: ${uploadError.message}`); }
    }
    try { setImages(await listPublicationImagesForManagement(kind, id, pin)); }
    catch (listError) { setError(listError.message); }
    if (failures.length) setNotice(`No se pudieron subir ${failures.length} imagen(es). Puedes volver a intentarlo.`);
    else setNotice('Imágenes actualizadas.');
    setBusy(false);
  }

  async function removeImage(imageId) {
    setBusy(true);
    setError('');
    try {
      await deletePublicationImage(kind, id, imageId, pin);
      setImages((current) => current.filter((image) => image.id !== imageId));
      setNotice('Imagen eliminada.');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  if (!validKind) return <section className="content-page"><Notice tone="error">El tipo de publicación no es válido.</Notice></section>;

  if (!loaded) return (
    <section className="access-page manage-gate">
      <div className="access-illustration" aria-hidden="true"><span>⌂</span><span>✓</span></div>
      <span className="eyebrow">Administración privada</span>
      <h1>Vuelve a tu<br /><em>publicación.</em></h1>
      <p>Ingresa el PIN que creaste al publicar este {kindLabel(kind).toLowerCase()}.</p>
      <form className="access-form" onSubmit={loadManagement}>
        <Field label="PIN de administración" name="management-pin" type="password" inputMode="numeric" autoComplete="current-password" value={pin} onChange={(event) => setPin(event.target.value)} required minLength={4} maxLength={12} pattern="[0-9]{4,12}" />
        <Notice tone="error">{error}</Notice>
        <button className="button button-primary button-wide" disabled={busy}>{busy ? 'Verificando…' : 'Abrir publicación'} <span aria-hidden="true">→</span></button>
      </form>
      <Link className="back-link access-back" to="/mis-publicaciones">← Volver a tus publicaciones</Link>
    </section>
  );

  return (
    <section className="manage-page">
      <div className="manage-topline"><Link className="back-link" to="/mis-publicaciones">← Tus publicaciones</Link><span className="pill">{kindLabel(kind)} · {item.status}</span></div>
      <div className="page-heading manage-heading"><span className="eyebrow">Actualizado {formatDate(item.updated_at)}</span><h1>Administra tu <em>publicación.</em></h1><p>Estos cambios se reflejan en el catálogo público.</p></div>
      <Notice tone="error">{error}</Notice>
      <Notice>{notice}</Notice>
      <form className="publication-form manage-form" onSubmit={save}>
        <div className="form-section">
          <div className="form-section-heading"><span>01</span><div><h2>Contenido</h2><p>Revisa que la información esté al día.</p></div></div>
          <div className="form-grid">
            <Field label="Título" name="title" value={form.title} onChange={change} required minLength={kind === 'product' ? 3 : 5} maxLength={150} />
            <Field label="Categoría" name="category" value={form.category} onChange={change} required minLength={2} maxLength={80} />
            {kind === 'product' ? <>
              <Field label="Precio (COP)" name="price" type="number" value={form.price} onChange={change} required min="1" step="100" />
              <Field label="Unidades disponibles" name="quantity" type="number" value={form.quantity} onChange={change} min="0" step="1" />
            </> : <>
              <Field label="Nombre del negocio" name="business_name" value={form.business_name} onChange={change} maxLength={150} />
              <Field label="Sitio web" name="website_url" type="url" value={form.website_url} onChange={change} maxLength={2048} />
            </>}
            <Field label="Descripción" name="description" as="textarea" rows="5" className="input field-wide" value={form.description} onChange={change} required minLength={10} maxLength={10000} />
            <label className="field"><span className="field-label">Estado</span><select className="input" name="status" value={form.status} onChange={change}>{(kind === 'product' ? ['ACTIVE', 'SOLD', 'CLOSED'] : ['ACTIVE', 'PAUSED', 'CLOSED']).map((status) => <option key={status} value={status}>{({ ACTIVE: 'Activo', SOLD: 'Vendido', PAUSED: 'Pausado', CLOSED: 'Cerrado' })[status]}</option>)}</select></label>
          </div>
        </div>
        <div className="form-section">
          <div className="form-section-heading"><span>02</span><div><h2>{kind === 'product' ? 'Fotos' : 'Imagen del aviso'}</h2><p>{kind === 'product' ? 'Sube hasta 8 fotos.' : 'Sube 1 imagen para mostrar con el aviso.'} Aceptamos JPG, PNG y WebP de hasta 5 MB cada una.</p></div></div>
          <div className="manage-images">
            {images.map((image) => <figure className="manage-image" key={image.id}><img src={image.url} alt={image.alt_text || item.title} /><button type="button" className="image-remove" onClick={() => removeImage(image.id)} disabled={busy} aria-label="Eliminar foto">×</button>{image.status === 'PENDING' && <figcaption>Subida pendiente</figcaption>}</figure>)}
            {images.length < maxImageCount && <label className="image-add"><span>＋</span><strong>{kind === 'product' ? 'Añadir fotos' : 'Añadir imagen'}</strong><small>{kind === 'product' ? 'Selecciona hasta 8' : 'Selecciona una imagen'}</small><input type="file" accept="image/jpeg,image/png,image/webp" multiple={kind === 'product'} onChange={addImages} disabled={busy} /></label>}
          </div>
        </div>
        <div className="form-section">
          <div className="form-section-heading"><span>03</span><div><h2>Contacto y privacidad</h2><p>El teléfono público depende de tu autorización.</p></div></div>
          <div className="form-grid">
            <Field label="Nombre de contacto" name="contact_name" value={form.contact_name} onChange={change} required minLength={2} maxLength={100} />
            <Field label="Teléfono" name="contact_phone" type="tel" value={form.contact_phone} onChange={change} required minLength={7} maxLength={20} />
            <Field label="Correo privado" name="contact_email" type="email" value={form.contact_email} onChange={change} maxLength={254} />
            <Field label="Ciudad" name="city" value={form.city} onChange={change} required minLength={2} maxLength={100} />
            <Field label="Dirección privada" name="address" value={form.address} onChange={change} maxLength={255} />
            <label className="consent-field"><input type="checkbox" name="contact_phone_public" checked={form.contact_phone_public} onChange={change} /><span><strong>Mostrar mi teléfono públicamente</strong><small>Si lo desmarcas, se ocultará en el detalle.</small></span></label>
          </div>
        </div>
        <div className="form-section">
          <div className="form-section-heading"><span>04</span><div><h2>Actualizar PIN</h2><p>Opcional. Solo cambia el PIN si escribes uno nuevo.</p></div></div>
          <div className="form-grid pin-grid"><Field label="Nuevo PIN" name="new_admin_pin" type="password" inputMode="numeric" autoComplete="new-password" value={form.new_admin_pin || ''} onChange={change} minLength={6} maxLength={12} pattern="[0-9]{6,12}" placeholder="Dejar vacío para conservarlo" /></div>
        </div>
        <div className="form-submit-row"><span>Creada el {formatDate(item.created_at)} · {kind === 'product' && <strong>{formatPrice(item.price, item.currency)}</strong>}</span><button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Guardando…' : 'Guardar cambios'} <span aria-hidden="true">✓</span></button></div>
      </form>
      <div className="danger-zone"><div><strong>Eliminar publicación</strong><p>Se quitará del catálogo y sus imágenes también se borrarán.</p></div><button type="button" className="button button-danger" onClick={removePublication} disabled={busy}>Eliminar</button></div>
    </section>
  );
}
