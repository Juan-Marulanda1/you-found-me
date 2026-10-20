import { useContext, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Field from '../components/Field.jsx';
import { Notice } from '../components/Feedback.jsx';
import { AuthContext } from '../App.jsx';
import { createPublication } from '../services/publications.js';
import { ACCEPTED_IMAGE_TYPES, LOW_RESOLUTION_HINT, findLowResolutionImages, maxImagesFor, uploadPublicationImage } from '../services/imageUpload.js';
import { rememberPublication } from '../services/publicationRefs.js';
import { publicationPath } from '../utils/routes.js';

const initialForm = {
  title: '', description: '', category: '', price: '', quantity: '', currency: 'COP',
  business_name: '', website_url: '', contact_name: '', contact_phone: '',
  contact_email: '', city: '', address: '', contact_phone_public: false,
};

// Formulario de publicación. Requiere sesión: la API asocia el registro a la cuenta.
export default function PublishPage() {
  const { session } = useContext(AuthContext);
  const navigate = useNavigate();
  const [kind, setKind] = useState('product');
  const [form, setForm] = useState(initialForm);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [createdPath, setCreatedPath] = useState('');
  const [lowResolution, setLowResolution] = useState([]);
  const maxImages = maxImagesFor(kind);

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
  }

  function selectKind(nextKind) {
    setKind(nextKind);
    setFiles([]);
    setLowResolution([]);
  }

  async function selectFiles(event) {
    const selected = Array.from(event.target.files || []).slice(0, maxImages);
    setFiles(selected);
    setLowResolution(await findLowResolutionImages(selected));
  }

  async function submitPublication(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    // Normaliza el formulario al contrato de la API: textos recortados y opcionales en null.
    const body = {
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category.trim(),
      contact_name: form.contact_name.trim(),
      contact_phone: form.contact_phone.trim(),
      contact_email: form.contact_email.trim() || null,
      city: form.city.trim(),
      address: form.address.trim() || null,
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
      const created = await createPublication(kind, body);
      try { rememberPublication(kind, created.id, created); } catch { /* La vista previa local es opcional. */ }

      // La publicación ya existe; las imágenes se suben una a una y un fallo no la revierte.
      const failures = [];
      for (const file of files) {
        try { await uploadPublicationImage(kind, created.id, file); }
        catch (uploadError) { failures.push(`${file.name}: ${uploadError.message}`); }
      }
      const path = publicationPath(kind, created.id);
      if (failures.length) {
        // Se queda en la página para que el motivo no desaparezca con la redirección.
        setCreatedPath(path);
        setError(`La publicación se creó, pero no se pudieron subir ${failures.length} imagen(es). ${failures.join(' ')} Puedes añadirlas desde Tus publicaciones.`);
      } else navigate(path);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  if (!session) return (
    <section className="access-page">
      <div className="access-illustration" aria-hidden="true"><span>✳</span><span>＋</span></div>
      <span className="eyebrow">Espacio para publicar</span>
      <h1>¿Tienes algo<br /><em>para compartir?</em></h1>
      <p>Inicia sesión para publicar y administrar tus avisos. La persona administradora puede invitarte con una clave privada.</p>
      <div className="account-actions">
        <Link className="button button-primary button-wide" to="/cuenta">Crear cuenta o iniciar sesión <span aria-hidden="true">→</span></Link>
      </div>
      <Link className="back-link access-back" to="/">← Volver al catálogo</Link>
    </section>
  );

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
              <Field label="Precio (COP)" name="price" type="number" value={form.price} onChange={updateField} required min="1000" step="1" placeholder="25000" />
              <Field label="Unidades disponibles" name="quantity" type="number" value={form.quantity} onChange={updateField} min="0" step="1" placeholder="Opcional" />
            </> : <>
              <Field label="Nombre del negocio" name="business_name" value={form.business_name} onChange={updateField} maxLength={150} placeholder="Opcional" />
              <Field label="Sitio web" name="website_url" type="url" value={form.website_url} onChange={updateField} maxLength={2048} placeholder="https://" />
            </>}
            <Field label="Descripción" name="description" as="textarea" rows="5" value={form.description} onChange={updateField} required minLength={10} maxLength={10000} placeholder="Describe lo que ofreces con los detalles que te gustaría encontrar." className="input field-wide" />
            <label className="field field-wide"><span className="field-label">{kind === 'product' ? 'Fotos del producto' : 'Imagen del aviso'}</span><input className="file-input" type="file" accept={ACCEPTED_IMAGE_TYPES} multiple={maxImages > 1} onChange={selectFiles} /><span className="field-hint">JPG, PNG o WebP · hasta 5 MB por imagen. {maxImages > 1 ? `Máximo ${maxImages} fotos.` : 'Puedes adjuntar 1 imagen.'}</span>{files.length > 0 && <span className="file-summary">{files.length} {files.length === 1 ? 'imagen seleccionada' : 'imágenes seleccionadas'}</span>}{lowResolution.length > 0 && <span className="field-hint" role="status">⚠ {lowResolution.join(', ')} {lowResolution.length === 1 ? 'tiene' : 'tienen'} poca resolución y podría verse borrosa. {LOW_RESOLUTION_HINT}</span>}</label>
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
        <Notice tone="error">{error}</Notice>
        {notice && <Notice>{notice}</Notice>}
        {createdPath && <Link className="button" to={createdPath}>Ver la publicación creada →</Link>}
        <div className="form-submit-row"><span>La publicación quedará asociada a tu cuenta. Al publicar aceptas que los datos marcados como públicos puedan ser vistos por cualquiera.</span><button className="button button-primary" disabled={busy}>{busy ? 'Publicando…' : 'Publicar ahora'} <span aria-hidden="true">↗</span></button></div>
      </form>
    </section>
  );
}
