const $ = (id) => document.getElementById(id);
const state = { mode: 'procedimento', scope: 'ortopedia', query: '', results: [], detail: null, selectedCid: null, items: [], chosenItems: [] };
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const api = async (path) => {
  const response = await fetch(path);
  const data = await response.json();
  if (!response.ok) throw new Error(data.erro || 'Falha na consulta');
  return data;
};
const params = (query = '') => `?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(state.scope)}`;

function updateTabs() {
  document.querySelectorAll('.tab').forEach((tab) => {
    const active = tab.dataset.mode === state.mode;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  $('results-title').textContent = state.mode === 'cid' ? 'CIDs encontrados' : 'Procedimentos';
  $('query').placeholder = state.mode === 'cid' ? 'Digite um código CID, ex.: S72' : 'Busque por palavra ou código, ex.: fêmur';
  $('search-hint').textContent = state.mode === 'cid'
    ? 'A planilha contém códigos CID, sem nomes de diagnósticos. Digite um código para ver os procedimentos relacionados.'
    : 'O grupo 0408 é um recorte inicial da planilha. A seleção final de Traumatologia e Ortopedia pode ser ajustada com a equipe clínica.';
}

async function loadResults() {
  const request = `${state.mode}:${state.scope}:${state.query}`;
  if (state.mode === 'cid' && !state.query) {
    state.results = [];
    $('result-count').textContent = '0';
    $('results').innerHTML = '<div class="empty">Digite um código CID para começar.</div>';
    return;
  }
  $('results').innerHTML = '<div class="empty">Buscando na planilha…</div>';
  try {
    const path = state.mode === 'cid' ? '/api/cids' : '/api/procedimentos';
    const rows = await api(path + params(state.query));
    if (request !== `${state.mode}:${state.scope}:${state.query}`) return;
    state.results = rows;
    $('result-count').textContent = rows.length === 60 ? '60+' : String(rows.length);
    $('results').innerHTML = rows.length ? rows.map((row) => state.mode === 'cid'
      ? `<button class="result" data-cid="${escapeHtml(row.codigo)}"><span class="result-head"><span class="code">CID ${escapeHtml(row.codigo)}</span><span class="chevron">›</span></span><span class="result-name">Ver procedimentos relacionados</span><span class="result-meta">${row.procedimentos} procedimento(s) no recorte</span></button>`
      : `<button class="result ${state.detail?.codigo === row.codigo ? 'active' : ''}" data-procedure="${escapeHtml(row.codigo)}"><span class="result-head"><span class="code">${escapeHtml(row.codigo)}</span><span class="chevron">›</span></span><span class="result-name">${escapeHtml(row.nome)}</span></button>`).join('')
      : '<div class="empty">Nenhum resultado neste recorte. Tente outra palavra ou selecione “Todos os procedimentos”.</div>';
  } catch (error) { $('results').innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`; }
}

async function openProcedure(code) {
  try {
    state.detail = await api(`/api/procedimentos/${encodeURIComponent(code)}`);
    state.selectedCid = null;
    state.chosenItems = [];
    state.items = [];
    renderDetail();
    document.querySelectorAll('[data-procedure]').forEach((element) => element.classList.toggle('active', element.dataset.procedure === code));
    if (window.innerWidth < 850) $('detail').scrollIntoView({behavior:'smooth',block:'start'});
  } catch (error) { $('detail-placeholder').innerHTML = `<p>${escapeHtml(error.message)}</p>`; }
}

async function openCid(code) {
  try {
    const rows = await api(`/api/cids/${encodeURIComponent(code)}/procedimentos?scope=${encodeURIComponent(state.scope)}`);
    state.mode = 'procedimento';
    state.query = '';
    $('query').value = '';
    updateTabs();
    state.results = rows;
    $('results-title').textContent = `Procedimentos · CID ${code}`;
    $('result-count').textContent = rows.length === 60 ? '60+' : String(rows.length);
    $('results').innerHTML = rows.length ? rows.map((row) => `<button class="result" data-procedure="${escapeHtml(row.codigo)}"><span class="result-head"><span class="code">${escapeHtml(row.codigo)}</span><span class="chevron">›</span></span><span class="result-name">${escapeHtml(row.nome)}</span><span class="result-meta">CID ${escapeHtml(row.tipo_cid)}</span></button>`).join('') : '<div class="empty">Nenhum procedimento encontrado no recorte.</div>';
  } catch (error) { $('results').innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`; }
}

function renderDetail() {
  const row = state.detail;
  if (!row) return;
  const statusLabel = row.status_dados === 'importado_com_pendencias' ? 'importado com pendências' : row.status_dados.replaceAll('_', ' ');
  $('detail-placeholder').hidden = true;
  $('detail').hidden = false;
  const cids = row.cids.map((cid) => `<button class="cid-chip ${state.selectedCid === cid.codigo ? 'selected' : ''}" data-select-cid="${escapeHtml(cid.codigo)}" title="Grafia na planilha: ${escapeHtml(cid.grafia_original)}">${escapeHtml(cid.codigo)}<small>${cid.tipo === 'principal' ? 'Principal' : 'Secundário'}</small></button>`).join('');
  const chosenCid = row.cids.find((cid) => cid.codigo === state.selectedCid);
  const cidDescription = chosenCid ? `<div class="cid-description"><strong>CID ${escapeHtml(chosenCid.codigo)}</strong><span>${chosenCid.descricao ? escapeHtml(chosenCid.descricao) : 'A planilha não informa o nome deste diagnóstico. Os resultados abaixo descrevem procedimentos associados ao código, não o significado clínico do CID.'}</span>${chosenCid.fonte_descricao ? `<small>Fonte: ${escapeHtml(chosenCid.fonte_descricao)}</small>` : ''}<div id="cid-related" class="cid-related">Carregando procedimentos relacionados…</div></div>` : '';
  $('detail').innerHTML = `
    <div class="detail-top"><span class="pill">PROCEDIMENTO ${escapeHtml(row.codigo)}</span><button class="link-button" data-copy-code="${escapeHtml(row.codigo)}">Copiar código</button></div>
    <h2 class="detail-title">${escapeHtml(row.nome)}</h2>
    <p class="muted">${escapeHtml(row.descricao || 'A planilha não traz descrição para este procedimento.')}</p>
    <div class="detail-section"><h3>CIDs relacionados <span class="count">${row.cids.length}</span></h3><p class="section-intro">Selecione um CID para incluir no resumo. A relação e o tipo vêm da planilha.</p><div class="cid-list">${cids || '<span class="muted">Nenhum CID informado.</span>'}</div>${cidDescription}</div>
    <div class="detail-section"><h3>Itens OPM com CID em comum</h3><p class="section-intro">${state.selectedCid ? `Sugestões do grupo 07 que também citam o CID ${escapeHtml(state.selectedCid)}. A coincidência de CID não comprova compatibilidade ou autorização para esta cirurgia.` : 'Selecione um CID acima para ver sugestões do grupo 07. A ausência de um item nesta lista não comprova que ele seja proibido.'}</p><form id="item-form" class="item-search"><input id="item-query" type="search" placeholder="Filtrar sugestões por nome ou código" aria-label="Buscar OPM" ${state.selectedCid ? '' : 'disabled'}><button type="submit" ${state.selectedCid ? '' : 'disabled'}>Filtrar</button></form><div id="item-results" class="item-results" ${state.selectedCid ? '' : 'hidden'}>${state.selectedCid ? '<div class="empty">Carregando sugestões…</div>' : ''}</div><div id="chosen-items"></div></div>
    <div class="detail-section"><h3>Resumo para copiar</h3><p class="section-intro">Competência informada: ${escapeHtml(row.competencia)} · Status: ${escapeHtml(statusLabel)}</p><div id="summary" class="summary"></div><button id="copy-summary" class="primary-button">Copiar resumo</button><span id="copy-feedback" class="feedback"></span></div>`;
  renderChosenItems();
  renderSummary();
}

function renderItems() {
  const box = $('item-results');
  if (!box) return;
  box.hidden = false;
  box.innerHTML = state.items.length ? state.items.map((item) => `<div class="item-result"><div><strong>${escapeHtml(item.codigo)} · ${escapeHtml(item.nome)}</strong><span>${item.qtd_maxima_item ? `Qtd. máxima do item: ${item.qtd_maxima_item}` : 'Sem quantidade máxima informada no item'}</span></div><button type="button" data-add-item="${escapeHtml(item.codigo)}" ${item.qtd_maxima_item ? '' : 'disabled'}>Adicionar</button></div>`).join('') : '<div class="empty">Nenhum item com este CID e termo de busca foi encontrado na planilha. Isso não comprova proibição ou incompatibilidade.</div>';
}

function renderChosenItems() {
  const box = $('chosen-items');
  if (!box) return;
  box.innerHTML = state.chosenItems.length ? `<p class="section-intro">Itens selecionados a partir de CIDs em comum · compatibilidade com o procedimento não verificada</p>${state.chosenItems.map((item) => `<div class="selection"><div class="selection-name"><strong>${escapeHtml(item.codigo)}</strong>${escapeHtml(item.nome)}<br><span class="muted">Máximo do item: ${item.qtd_maxima_item}</span></div><div class="selection-actions"><label>Quantidade <span class="quantity-control"><button type="button" aria-label="Diminuir ${escapeHtml(item.codigo)}" data-decrease-item="${escapeHtml(item.codigo)}" ${item.quantidade <= 1 ? 'disabled' : ''}>−</button><input type="number" min="1" max="${item.qtd_maxima_item}" value="${item.quantidade}" data-item-quantity="${escapeHtml(item.codigo)}"><button type="button" aria-label="Aumentar ${escapeHtml(item.codigo)}" data-increase-item="${escapeHtml(item.codigo)}" ${item.quantidade >= item.qtd_maxima_item ? 'disabled' : ''}>+</button></span></label><button class="remove-item" type="button" data-remove-item="${escapeHtml(item.codigo)}">Remover</button></div></div>`).join('')}` : '';
}

function summaryText() {
  const row = state.detail;
  if (!row) return '';
  const lines = [`eaSIGTAP — consulta à planilha SIGTAP`, `Competência informada: ${row.competencia}`, `Procedimento: ${row.codigo} — ${row.nome}`, `CID selecionado: ${state.selectedCid || 'não selecionado'}`];
  if (state.chosenItems.length) {
    lines.push('Itens OPM sugeridos por CID em comum e selecionados manualmente (compatibilidade com o procedimento não verificada):');
    state.chosenItems.forEach((item) => lines.push(`- ${item.codigo} — ${item.nome} | quantidade ${item.quantidade} | máximo informado para o item ${item.qtd_maxima_item}`));
  } else lines.push('Itens OPM: nenhum selecionado');
  lines.push('Fonte: planilha Sigtap - UGPIA.xlsx; confirmar adequação clínica antes do uso.');
  return lines.join('\n');
}

function renderSummary() { if ($('summary')) $('summary').textContent = summaryText(); }

document.addEventListener('click', async (event) => {
  const tab = event.target.closest('[data-mode]');
  if (tab) { state.mode = tab.dataset.mode; state.query = ''; $('query').value = ''; updateTabs(); loadResults(); return; }
  const procedure = event.target.closest('[data-procedure]');
  if (procedure) { openProcedure(procedure.dataset.procedure); return; }
  const cid = event.target.closest('[data-cid]');
  if (cid) { openCid(cid.dataset.cid); return; }
  const selected = event.target.closest('[data-select-cid]');
  if (selected) {
    const code = selected.dataset.selectCid;
    state.selectedCid = code;
    state.items = [];
    state.chosenItems = [];
    renderDetail();
    loadSuggestedItems('');
    try {
      const rows = await api(`/api/cids/${encodeURIComponent(code)}/procedimentos?scope=${encodeURIComponent(state.scope)}`);
      const box = $('cid-related');
      if (state.selectedCid !== code || !box) return;
      box.innerHTML = `<strong>Procedimentos relacionados neste recorte (${rows.length}${rows.length === 60 ? '+' : ''})</strong>${rows.slice(0, 8).map((row) => `<button type="button" class="related-procedure" data-procedure="${escapeHtml(row.codigo)}"><span>${escapeHtml(row.codigo)} · ${escapeHtml(row.nome)}</span>${row.descricao ? `<small>${escapeHtml(row.descricao.slice(0, 150))}</small>` : ''}</button>`).join('') || '<span>Nenhum procedimento neste recorte.</span>'}`;
    } catch (error) { if ($('cid-related')) $('cid-related').textContent = error.message; }
    return;
  }
  const add = event.target.closest('[data-add-item]');
  if (add) { const item = state.items.find((row) => row.codigo === add.dataset.addItem); if (item && item.qtd_maxima_item && !state.chosenItems.some((row) => row.codigo === item.codigo)) { state.chosenItems.push({...item, quantidade:1}); renderChosenItems(); renderSummary(); } return; }
  const remove = event.target.closest('[data-remove-item]');
  if (remove) { state.chosenItems = state.chosenItems.filter((item) => item.codigo !== remove.dataset.removeItem); renderChosenItems(); renderSummary(); return; }
  const increase = event.target.closest('[data-increase-item]');
  if (increase) { const item = state.chosenItems.find((row) => row.codigo === increase.dataset.increaseItem); if (item) { item.quantidade = Math.min(item.qtd_maxima_item, item.quantidade + 1); renderChosenItems(); renderSummary(); } return; }
  const decrease = event.target.closest('[data-decrease-item]');
  if (decrease) { const item = state.chosenItems.find((row) => row.codigo === decrease.dataset.decreaseItem); if (item) { item.quantidade = Math.max(1, item.quantidade - 1); renderChosenItems(); renderSummary(); } return; }
  const copyCode = event.target.closest('[data-copy-code]');
  if (copyCode) { await navigator.clipboard.writeText(copyCode.dataset.copyCode); copyCode.textContent = 'Copiado'; setTimeout(() => copyCode.textContent = 'Copiar código', 1500); return; }
  if (event.target.id === 'copy-summary') { await navigator.clipboard.writeText(summaryText()); $('copy-feedback').textContent = 'Copiado'; setTimeout(() => { if ($('copy-feedback')) $('copy-feedback').textContent = ''; }, 1800); }
});

document.addEventListener('submit', async (event) => {
  if (event.target.id !== 'item-form') return;
  event.preventDefault();
  const query = $('item-query').value.trim();
  loadSuggestedItems(query);
});

async function loadSuggestedItems(query) {
  if (!state.detail || !state.selectedCid) return;
  const procedure = state.detail.codigo;
  const cid = state.selectedCid;
  if ($('item-results')) { $('item-results').hidden = false; $('item-results').innerHTML = '<div class="empty">Buscando itens com CID em comum…</div>'; }
  try {
    const rows = await api(`/api/itens?q=${encodeURIComponent(query)}&procedimento=${encodeURIComponent(procedure)}&cid=${encodeURIComponent(cid)}`);
    if (state.detail?.codigo !== procedure || state.selectedCid !== cid) return;
    state.items = rows;
    renderItems();
  } catch (error) { if ($('item-results')) $('item-results').innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`; }
}

function updateQuantity(target, finalize = false) {
  const item = state.chosenItems.find((row) => row.codigo === target.dataset.itemQuantity);
  if (!item) return;
  if (!finalize && target.value === '') return;
  const value = Number(target.value);
  item.quantidade = Number.isInteger(value) ? Math.max(1, Math.min(item.qtd_maxima_item, value)) : 1;
  if (finalize) target.value = item.quantidade;
  renderSummary();
}
document.addEventListener('change', (event) => {
  if (event.target.id === 'scope') { state.scope = event.target.value; loadResults(); return; }
  if (event.target.matches('[data-item-quantity]')) { updateQuantity(event.target, true); renderChosenItems(); }
});
document.addEventListener('input', (event) => {
  if (event.target.matches('[data-item-quantity]')) updateQuantity(event.target);
});

let timer;
$('query').addEventListener('input', (event) => { clearTimeout(timer); state.query = event.target.value.trim(); timer = setTimeout(loadResults, 220); });
updateTabs();
loadResults();
