import { useContext, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Field from '../components/Field.jsx';
import { Notice } from '../components/Feedback.jsx';
import { PublicationAccessContext } from '../App.jsx';
import { createPublication, verifyCreationKey } from '../services/publications.js';
import { uploadPublicationImage } from '../services/imageUpload.js';
import { rememberPublication } from '../services/publicationRefs.js';

const initialForm = {
  title: '', description: '', category: '', price: '', quantity: '', currency: 'COP',
  business_name: '', website_url: '', contact_name: '', contact_phone: '',
  contact_email: '', city: '', address: '', admin_pin: '', contact_phone_public: false,
};

export default function PublishPage() {
  const { creationKey, setCreationKey } = useContext(PublicationAccessContext);
  const navigate = useNavigate();
  const [kind, setKind] = useState('product');
  const [keyInput, setKeyInput] = useState('');
  const [form, setForm] = useState(initialForm);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
  }

  function selectKind(nextKind) {
    setKind(nextKind);
    setFiles([]);
  }

  async function unlock(event) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await verifyCreationKey(keyInput.trim());
      setCreationKey(keyInput.trim());
      setKeyInput('');
    } catch (requestError) {
      setError(requestError.status === 403 ? 'La clave no es correcta.' : requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitPublication(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    const body = {
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category.trim(),
      contact_name: form.contact_name.trim(),
      contact_phone: form.contact_phone.trim(),
      contact_email: form.contact_email.trim() || null,
      city: form.city.trim(),
      address: form.address.trim() || null,
      admin_pin: form.admin_pin,
      contact_phone_public: form.contact_phone_public,
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
      const created = await createPublication(kind, body, creationKey);
      try { rememberPublication(kind, created.id, created); } catch { /* Publication remains created even if browser storage is unavailable. */ }

      if (files.length) {
        const failures = [];
        for (const file of files) {
          try { await uploadPublicationImage(kind, created.id, file, form.admin_pin); }
          catch (uploadError) { failures.push(`${file.name}: ${uploadError.message}`); }
        }
        if (failures.length) {
          setNotice(`La publicación se creó. No se pudieron subir ${failures.length} imagen(es); puedes intentarlo desde “Tus publicaciones”.`);
          window.setTimeout(() => navigate(`/${kind === 'product' ? 'productos' : 'avisos'}/${created.id}`), 1800);
        } else {
          navigate(`/${kind === 'product' ? 'productos' : 'avisos'}/${created.id}`);
        }
      } else {
        navigate(`/${kind === 'product' ? 'productos' : 'avisos'}/${created.id}`);
      }
    } catch (requestError) {
      if (requestError.status === 403) {
        setCreationKey('');
        setError('La clave de publicación ya no es válida. Ingresa la clave activa para continuar.');
      } else setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  if (!creationKey) {
    return (
      <section className="access-page">
        <div className="access-illustration" aria-hidden="true"><span>✳</span><span>＋</span></div>
        <span className="eyebrow">Espacio para publicar</span>
        <h1>¿Tienes algo<br /><em>para compartir?</em></h1>
        <p>Esta sección es privada. Ingresa la clave que te compartió quien administra You Found Me.</p>
        <form className="access-form" onSubmit={unlock}>
          <Field label="Clave de publicación" name="publication-key" type="password" autoComplete="off" value={keyInput} onChange={(event) => setKeyInput(event.target.value)} required />
          <Notice tone="error">{error}</Notice>
          <button className="button button-primary button-wide" disabled={busy}>{busy ? 'Verificando…' : 'Entrar a publicar'} <span aria-hidden="true">→</span></button>
        </form>
        <Link className="back-link access-back" to="/">← Volver al catálogo</Link>
      </section>
    );
  }

  return (
    <section className="publish-page">
      <div className="page-heading">
        <Link className="back-link" to="/">← Volver al catálogo</Link>
        <span className="eyebrow">Lo local se encuentra aquí</span>
        <h1>Comparte algo <em>bueno.</em></h1>
        <p>Cuéntale a tu comunidad qué ofreces. Los datos de contacto se comparten con cuidado.</p>
      </div>
      <div className="publish-kind" role="tablist" aria-label="Tipo de publicación">
        <button type="button" className={kind === 'product' ? 'publish-kind-option selected' : 'publish-kind-option'} onClick={() => selectKind('product')}><span>✳</span><strong>Vender un producto</strong><small>Un artículo que alguien puede comprar</small></button>
        <button type="button" className={kind === 'announcement' ? 'publish-kind-option selected' : 'publish-kind-option'} onClick={() => selectKind('announcement')}><span>⌂</span><strong>Publicar un aviso</strong><small>Dar a conocer un negocio o servicio</small></button>
      </div>

      <form className="publication-form" onSubmit={submitPublication}>
        <div className="form-section">
          <div className="form-section-heading"><span>01</span><div><h2>Cuéntanos qué publicas</h2><p>Lo esencial para que las personas lo encuentren.</p></div></div>
          <div className="form-grid">
            <Field label={kind === 'product' ? 'Nombre del producto' : 'Título del aviso'} name="title" value={form.title} onChange={updateField} required minLength={kind === 'product' ? 3 : 5} maxLength={150} placeholder={kind === 'product' ? 'Ej. Mesa de madera restaurada' : 'Ej. Clases de guitarra en el barrio'} />
            <Field label="Categoría" name="category" value={form.category} onChange={updateField} required minLength={2} maxLength={80} placeholder="Ej. Hogar, comida, servicios" />
            {kind === 'product' ? <>
              <Field label="Precio (COP)" name="price" type="number" value={form.price} onChange={updateField} required min="1" step="100" placeholder="25000" />
              <Field label="Unidades disponibles" name="quantity" type="number" value={form.quantity} onChange={updateField} min="0" step="1" placeholder="Opcional" />
            </> : <>
              <Field label="Nombre del negocio" name="business_name" value={form.business_name} onChange={updateField} maxLength={150} placeholder="Opcional" />
              <Field label="Sitio web" name="website_url" type="url" value={form.website_url} onChange={updateField} maxLength={2048} placeholder="https://" />
            </>}
            <Field label="Descripción" name="description" as="textarea" rows="5" value={form.description} onChange={updateField} required minLength={10} maxLength={10000} placeholder="Describe lo que ofreces con los detalles que te gustaría encontrar." className="input field-wide" />
            <label className="field field-wide"><span className="field-label">{kind === 'product' ? 'Fotos del producto' : 'Imagen del aviso'}</span><input className="file-input" type="file" accept="image/jpeg,image/png,image/webp" multiple={kind === 'product'} onChange={(event) => setFiles(Array.from(event.target.files || []).slice(0, kind === 'product' ? 8 : 1))} /><span className="field-hint">JPG, PNG o WebP · hasta 5 MB por imagen. {kind === 'product' ? 'Máximo 8 fotos.' : 'Puedes adjuntar 1 imagen.'}</span>{files.length > 0 && <span className="file-summary">{files.length} {files.length === 1 ? 'imagen seleccionada' : 'imágenes seleccionadas'}</span>}</label>
          </div>
        </div>

        <div className="form-section">
          <div className="form-section-heading"><span>02</span><div><h2>Cómo pueden contactarte</h2><p>Tu correo y dirección exacta no se muestran en público.</p></div></div>
          <div className="form-grid">
            <Field label="Tu nombre" name="contact_name" value={form.contact_name} onChange={updateField} required minLength={2} maxLength={100} autoComplete="name" />
            <Field label="Teléfono" name="contact_phone" type="tel" value={form.contact_phone} onChange={updateField} required minLength={7} maxLength={20} autoComplete="tel" placeholder="+57 300 000 0000" />
            <Field label="Correo electrónico" name="contact_email" type="email" value={form.contact_email} onChange={updateField} maxLength={254} autoComplete="email" placeholder="Opcional, privado" />
            <Field label="Ciudad" name="city" value={form.city} onChange={updateField} required minLength={2} maxLength={100} autoComplete="address-level2" />
            <Field label="Dirección exacta" name="address" value={form.address} onChange={updateField} maxLength={255} autoComplete="street-address" placeholder="Opcional, privada" />
            <label className="consent-field"><input type="checkbox" name="contact_phone_public" checked={form.contact_phone_public} onChange={updateField} /><span><strong>Mostrar mi teléfono en el aviso público</strong><small>Si no lo marcas, el teléfono solo se conservará para administrar la publicación.</small></span></label>
          </div>
        </div>

        <div className="form-section">
          <div className="form-section-heading"><span>03</span><div><h2>Protege tu publicación</h2><p>Con este PIN podrás editarla o borrarla desde “Tus publicaciones”.</p></div></div>
          <div className="form-grid pin-grid">
            <Field label="PIN de administración" name="admin_pin" type="password" inputMode="numeric" autoComplete="new-password" value={form.admin_pin} onChange={updateField} required minLength={6} maxLength={12} pattern="[0-9]{6,12}" placeholder="Entre 6 y 12 números" />
            <p className="pin-reminder">Guárdalo en un lugar seguro. No podremos recuperarlo si lo pierdes.</p>
          </div>
        </div>
        <Notice tone="error">{error}</Notice>
        {notice && <Notice>{notice}</Notice>}
        <div className="form-submit-row"><span>Al publicar aceptas que los datos marcados como públicos puedan ser vistos por cualquiera.</span><button className="button button-primary" disabled={busy}>{busy ? 'Publicando…' : 'Publicar ahora'} <span aria-hidden="true">↗</span></button></div>
      </form>
    </section>
  );
}
