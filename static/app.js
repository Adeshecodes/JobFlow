const state = { applications: [], selectedId: null };
const elements = {
  body: document.querySelector('#applications'), empty: document.querySelector('#empty-state'), template: document.querySelector('#application-row'),
  search: document.querySelector('#search'), filter: document.querySelector('#status-filter'), dialog: document.querySelector('#application-dialog'), form: document.querySelector('#application-form'),
  id: document.querySelector('#application-id'), company: document.querySelector('#company'), role: document.querySelector('#role'), location: document.querySelector('#location'), status: document.querySelector('#status'), date: document.querySelector('#date-applied'), notes: document.querySelector('#notes'),
  total: document.querySelector('#total-count'), applied: document.querySelector('#applied-count'), interview: document.querySelector('#interview-count'), offer: document.querySelector('#offer-count'), saved: document.querySelector('#saved-count'),
  title: document.querySelector('#form-title'), kicker: document.querySelector('#form-kicker'), remove: document.querySelector('#delete-application')
};

const statusClass = (status) => `status-${status.toLowerCase()}`;
const formatDate = (value) => value ? new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(`${value}T12:00:00`)) : '—';

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) { const message = await response.json().catch(() => ({})); throw new Error(message.error || 'Something went wrong.'); }
  return response.status === 204 ? null : response.json();
}

async function loadApplications() {
  const params = new URLSearchParams();
  if (elements.search.value.trim()) params.set('search', elements.search.value.trim());
  if (elements.filter.value) params.set('status', elements.filter.value);
  state.applications = await request(`/api/applications?${params}`);
  renderApplications();
}

function renderApplications() {
  elements.body.innerHTML = '';
  elements.empty.hidden = state.applications.length > 0;
  state.applications.forEach((application) => {
    const row = elements.template.content.cloneNode(true);
    const company = row.querySelector('.company-button');
    company.textContent = application.company;
    company.addEventListener('click', () => openEditor(application));
    row.querySelector('.row-notes').textContent = application.notes || 'No notes added';
    row.querySelector('.role-cell').textContent = application.role;
    row.querySelector('.location-cell').textContent = application.location || '—';
    const status = row.querySelector('.status-pill');
    status.textContent = application.status;
    status.classList.add(statusClass(application.status));
    row.querySelector('.date-cell').textContent = formatDate(application.date_applied);
    row.querySelector('.more-button').addEventListener('click', () => openEditor(application));
    elements.body.append(row);
  });
}

async function loadStats() {
  const stats = await request('/api/stats');
  elements.total.textContent = stats.total;
  elements.applied.textContent = stats.Applied;
  elements.interview.textContent = stats.Interview;
  elements.offer.textContent = stats.Offer;
  elements.saved.textContent = stats.Saved;
}

function openEditor(application = null) {
  state.selectedId = application?.id ?? null;
  elements.form.reset();
  elements.id.value = application?.id ?? '';
  elements.company.value = application?.company ?? '';
  elements.role.value = application?.role ?? '';
  elements.location.value = application?.location ?? '';
  elements.status.value = application?.status ?? 'Saved';
  elements.date.value = application?.date_applied ?? '';
  elements.notes.value = application?.notes ?? '';
  elements.title.textContent = application ? 'Edit application' : 'Add application';
  elements.kicker.textContent = application ? 'Update opportunity' : 'New opportunity';
  elements.remove.hidden = !application;
  elements.dialog.showModal();
}

async function saveApplication(event) {
  event.preventDefault();
  const data = { company: elements.company.value, role: elements.role.value, location: elements.location.value, status: elements.status.value, date_applied: elements.date.value, notes: elements.notes.value };
  try {
    const url = state.selectedId ? `/api/applications/${state.selectedId}` : '/api/applications';
    await request(url, { method: state.selectedId ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    elements.dialog.close();
    await Promise.all([loadApplications(), loadStats()]);
  } catch (error) { window.alert(error.message); }
}

async function removeApplication() {
  if (!state.selectedId || !window.confirm('Delete this application?')) return;
  await request(`/api/applications/${state.selectedId}`, { method: 'DELETE' });
  elements.dialog.close();
  await Promise.all([loadApplications(), loadStats()]);
}

document.querySelector('#new-application').addEventListener('click', () => openEditor());
document.querySelector('#empty-add').addEventListener('click', () => openEditor());
document.querySelector('#close-dialog').addEventListener('click', () => elements.dialog.close());
document.querySelector('#cancel-dialog').addEventListener('click', () => elements.dialog.close());
elements.form.addEventListener('submit', saveApplication);
elements.remove.addEventListener('click', removeApplication);
elements.search.addEventListener('input', () => loadApplications());
elements.filter.addEventListener('change', loadApplications);

Promise.all([loadApplications(), loadStats()]).catch((error) => { elements.empty.hidden = false; elements.empty.innerHTML = `<p>${error.message}</p>`; });
