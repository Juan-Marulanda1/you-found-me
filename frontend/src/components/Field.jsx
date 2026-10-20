export default function Field({ label, name, value, onChange, as = 'input', hint, required, ...props }) {
  const Element = as;
  return (
    <label className="field" htmlFor={name}>
      <span className="field-label">{label}{required && <span className="required-mark"> *</span>}</span>
      <Element
        className="input"
        id={name}
        name={name}
        value={value ?? ''}
        onChange={onChange}
        required={required}
        {...props}
      />
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}
