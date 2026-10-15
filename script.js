document.getElementById('anio').textContent = new Date().getFullYear();

const form = document.getElementById('form');
const estado = document.getElementById('estado');
const boton = form.querySelector('button');

function mostrar(msg, clase) {
  estado.textContent = msg;
  estado.className = clase;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  form.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));

  const faltan = [...form.elements].filter(el => el.required && !(el.type === 'checkbox' ? el.checked : el.value.trim()));
  const email = form.elements.email;
  if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value) && !faltan.includes(email)) faltan.push(email);
  if (faltan.length) {
    faltan.forEach(el => el.classList.add('invalid'));
    faltan[0].focus();
    return mostrar('Revisa los campos marcados.', 'err');
  }

  boton.disabled = true;
  mostrar('Enviando…', '');
  try {
    const datos = Object.fromEntries(new FormData(form));
    const r = await fetch('/api/contacto', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error || 'No se pudo enviar.');
    form.reset();
    mostrar('¡Gracias! Recibimos tu consulta y te responderemos pronto.', 'ok');
  } catch (err) {
    mostrar(err.message || 'Error de conexión. Intenta nuevamente.', 'err');
  } finally {
    boton.disabled = false;
  }
});
