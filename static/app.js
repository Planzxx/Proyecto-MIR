/* Interfaz de Plazas MIR. Toda la lógica (filtros, resumen, notas, simulador) vive en el servidor Python. */
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
const fmt = n => Number(n).toLocaleString('es-ES');
const num = v => { v = parseInt(v,10); return isNaN(v) ? null : v; };
const dec = v => parseFloat(String(v).replace(',','.'));
const f2 = v => v.toLocaleString('es-ES',{minimumFractionDigits:2,maximumFractionDigits:2});

async function api(url, opts){
  const r = await fetch(url, opts);
  const data = await r.json().catch(()=>({}));
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}
const debounce = (fn, ms) => { let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); }; };

let META = null;
const st = {q:'',e:'',g:'',p:'',c:'',n1:null,n2:null,sort:'a',dir:'asc',view:'list',grp:'e',limit:100,gsort:'nombre',gdir:'asc'};
let seq = 0;   /* descarta respuestas antiguas si llegan desordenadas */

function params(extra){
  const p = new URLSearchParams();
  [['q',st.q],['e',st.e],['g',st.g],['p',st.p],['c',st.c],['n1',st.n1??''],['n2',st.n2??'']].forEach(([k,v])=>{ if (v!=='') p.set(k,v); });
  Object.entries(extra||{}).forEach(([k,v])=>p.set(k,v));
  return p.toString();
}

/* ---------- Desplegables ---------- */
function fillSelect(el, items, first, cur){
  el.innerHTML = '<option value="">'+first+'</option>' + items.map(([v,t])=>'<option value="'+esc(v)+'">'+esc(t)+'</option>').join('');
  el.value = items.some(([v])=>String(v)===String(cur)) ? cur : '';
}
async function buildDependent(){
  const o = await api('/api/opciones?'+new URLSearchParams({g:st.g, p:st.p}));
  fillSelect($('fp'), o.provincias.map(x=>[x,x]), 'Todas las provincias', st.p); st.p = $('fp').value;
  fillSelect($('fh'), o.centros.map(c=>[c.id,c.nombre]), 'Todos los centros', st.c); st.c = $('fh').value;
}
function buildSelects(){
  fillSelect($('fs'), META.especialidades.map(e=>[e.id,e.nombre]), 'Todas las especialidades', st.e);
  fillSelect($('fc'), META.comunidades.map(x=>[x,x]), 'Todas las comunidades', st.g);
  return buildDependent();
}

/* ---------- Resaltado de la búsqueda ---------- */
function hl(text){
  const terms = norm(st.q.trim()).split(/\s+/).filter(Boolean);
  if (!terms.length) return esc(text);
  const n = norm(text);
  if (n.length !== text.length) return esc(text);
  const mask = new Array(text.length).fill(false);
  terms.forEach(t=>{ let i=-1; while((i=n.indexOf(t,i+1))>=0){ for(let k=i;k<i+t.length;k++) mask[k]=true; } });
  let out='', on=false;
  for (let i=0;i<text.length;i++){ if(mask[i]!==on){ out+= on?'</mark>':'<mark>'; on=mask[i]; } out+=esc(text[i]); }
  return out + (on?'</mark>':'');
}

/* ---------- Vistas Plazas y Resumen ---------- */
async function render(){
  $('t-list').setAttribute('aria-pressed', st.view==='list');
  $('t-sum').setAttribute('aria-pressed', st.view==='sum');
  $('t-sim').setAttribute('aria-pressed', st.view==='sim');
  $('bar').hidden = $('meta').hidden = $('out').hidden = st.view==='sim';
  $('sim').hidden = st.view!=='sim';
  if (st.view==='sim'){ simResults(); return; }
  $('gb').hidden = st.view!=='sum';
  const mine = ++seq;
  try {
    const d = st.view==='list'
      ? await api('/api/plazas?'+params({sort:st.sort, dir:st.dir, limit:st.limit}))
      : await api('/api/resumen?'+params({grp:st.grp, sort:st.gsort, dir:st.gdir}));
    if (mine !== seq) return;
    $('k-n').textContent = fmt(d.total);
    $('k-max').textContent = d.ultimo_n ? fmt(d.ultimo_n) : '–';
    $('count').innerHTML = '<b>'+fmt(d.total)+'</b> de '+fmt(META.total)+' plazas';
    $('out').innerHTML = st.view==='list' ? renderList(d) : renderSum(d);
  } catch(e){ $('out').innerHTML = '<div class="list"><div class="empty">'+esc(e.message)+'</div></div>'; }
}

const arrow = (on, dir) => on ? '<span class="arr">'+(dir==='asc'?'↑':'↓')+'</span>' : '';
function renderList(d){
  if (!d.total) return '<div class="list"><div class="empty">Ninguna plaza coincide con estos filtros.</div></div>';
  const th = (k,t)=>'<span><button type="button" data-sort="'+k+'"'+(st.sort===k?' aria-sort="'+(st.dir==='asc'?'ascending':'descending')+'"':'')+'>'+t+arrow(st.sort===k,st.dir)+'</button></span>';
  let h = '<div class="list"><div class="hd">'+th('a','Adj.')+th('n','Nº orden')+th('e','Especialidad')+th('c','Centro')+th('l','Localidad')+'</div>';
  for (const r of d.filas){
    h += '<div class="r"><span class="num"><span class="cap">Adj.</span>'+r.a+'</span><span class="num k"><span class="cap">Nº orden</span>'+r.n+'</span>'
      +'<span class="esp">'+hl(r.especialidad)+'</span><span class="cen">'+hl(r.centro)+'</span>'
      +'<span class="loc">'+hl(r.localidad)+'<small>'+esc(r.provincia===r.comunidad?r.comunidad:r.provincia+' · '+r.comunidad)+'</small></span></div>';
  }
  h += '</div>';
  if (d.total > d.filas.length) h += '<button class="more" type="button" id="more">Mostrar más ('+fmt(d.total-d.filas.length)+' restantes)</button>';
  return h;
}
function renderSum(d){
  const g = d.grupos;
  if (!g.length) return '<div class="list"><div class="empty">Ninguna plaza coincide con estos filtros.</div></div>';
  const top = Math.max(...g.map(o=>o.plazas));
  const th = (k,t)=>'<span><button type="button" data-gsort="'+k+'"'+(st.gsort===k?' aria-sort="'+(st.gdir==='asc'?'ascending':'descending')+'"':'')+'>'+t+arrow(st.gsort===k,st.gdir)+'</button></span>';
  let h = '<div class="list sum"><div class="hd">'+th('nombre','Nombre')+th('plazas','Plazas')+th('min','Primer nº')+th('max','Último nº')+'<span></span></div>';
  for (const o of g){
    h += '<div class="r" data-k="'+esc(o.k)+'" tabindex="0" role="button" title="Ver estas plazas"><span class="name">'+esc(o.nombre)+(o.sub?'<small>'+esc(o.sub)+'</small>':'')+'</span>'
      +'<span class="num k"><span class="cap">Plazas</span>'+o.plazas+'</span><span class="num"><span class="cap">Primer nº</span>'+o.min+'</span><span class="num k"><span class="cap">Último nº</span>'+o.max+'</span>'
      +'<span class="bar-cell"><i style="width:'+Math.max(2,Math.round(o.plazas/top*100))+'%"></i></span></div>';
  }
  return h+'</div>';
}

function onFilter(){ st.limit = 100; render(); }
const onFilterSoon = debounce(onFilter, 180);
$('q').addEventListener('input', e=>{ st.q=e.target.value; onFilterSoon(); });
$('fs').addEventListener('change', e=>{ st.e=e.target.value; onFilter(); });
$('fc').addEventListener('change', async e=>{ st.g=e.target.value; st.p=''; st.c=''; await buildDependent(); onFilter(); });
$('fp').addEventListener('change', async e=>{ st.p=e.target.value; st.c=''; await buildDependent(); onFilter(); });
$('fh').addEventListener('change', e=>{ st.c=e.target.value; onFilter(); });
$('n1').addEventListener('input', e=>{ st.n1=num(e.target.value); onFilterSoon(); });
$('n2').addEventListener('input', e=>{ st.n2=num(e.target.value); onFilterSoon(); });
$('grp').addEventListener('change', e=>{ st.grp=e.target.value; render(); });
$('reset').addEventListener('click', async ()=>{
  Object.assign(st,{q:'',e:'',g:'',p:'',c:'',n1:null,n2:null,limit:100});
  $('q').value=''; $('n1').value=''; $('n2').value=''; await buildSelects(); render();
});
$('t-list').addEventListener('click', ()=>{ st.view='list'; render(); });
$('t-sum').addEventListener('click', ()=>{ st.view='sum'; render(); });
$('t-sim').addEventListener('click', ()=>{ st.view='sim'; render(); window.scrollTo({top:0}); });
$('out').addEventListener('click', e=>{
  const sb = e.target.closest('[data-sort]');
  if (sb){ const k=sb.dataset.sort; if(st.sort===k) st.dir = st.dir==='asc'?'desc':'asc'; else {st.sort=k; st.dir='asc';} return render(); }
  const gb = e.target.closest('[data-gsort]');
  if (gb){ const k=gb.dataset.gsort; if(st.gsort===k) st.gdir = st.gdir==='asc'?'desc':'asc'; else {st.gsort=k; st.gdir=(k==='nombre'?'asc':'desc');} return render(); }
  if (e.target.id==='more'){ st.limit+=200; return render(); }
  const row = e.target.closest('.sum .r'); if (row) drill(row.dataset.k);
});
$('out').addEventListener('keydown', e=>{ if((e.key==='Enter'||e.key===' ')&&e.target.matches('.sum .r')){ e.preventDefault(); drill(e.target.dataset.k); } });
async function drill(k){
  if (st.grp==='e') st.e=k;
  else if (st.grp==='c') st.c=k;
  else if (st.grp==='a'){ st.g=k; st.p=''; st.c=''; }
  else if (st.grp==='p'){ st.p=k; st.c=''; }
  st.view='list'; st.limit=100;
  await buildSelects();
  $('fs').value=st.e; $('fc').value=st.g; $('fp').value=st.p; $('fh').value=st.c;
  render(); window.scrollTo({top:0});
}

/* ---------- Simulador ---------- */
const KEY = 'mirsim1';
let prefs = [];
const centrosCache = new Map();
async function centrosDe(p){
  const key = (p.e??'')+'|'+(p.g||'');
  if (!centrosCache.has(key)) centrosCache.set(key, api('/api/centros?'+new URLSearchParams({e:p.e??'', g:p.g||''})));
  return centrosCache.get(key);
}
const sval = v => (v===null||v===undefined) ? '' : String(v);
function centreOptionsHTML(p, lista){
  if (p.c!==null && !lista.some(c=>c.id===p.c)) p.c = null;
  return '<option value="">Cualquier centro</option>'+lista.map(c=>'<option value="'+c.id+'"'+(c.id===p.c?' selected':'')+'>'+esc(c.etiqueta)+'</option>').join('');
}
async function renderPrefs(){
  const lists = await Promise.all(prefs.map(centrosDe));
  $('prefs').innerHTML = prefs.map((p,i)=>
    '<div class="pref" data-i="'+i+'"><span class="pn">'+(i+1)+'</span>'
    +'<select data-f="e" aria-label="Especialidad de la preferencia '+(i+1)+'"><option value="">Cualquier especialidad</option>'
      +META.especialidades.map(s=>'<option value="'+s.id+'"'+(s.id===p.e?' selected':'')+'>'+esc(s.nombre)+'</option>').join('')+'</select>'
    +'<select data-f="g" aria-label="Comunidad de la preferencia '+(i+1)+'"><option value="">Cualquier comunidad</option>'
      +META.comunidades.map(g=>'<option value="'+esc(g)+'"'+(g===p.g?' selected':'')+'>'+esc(g)+'</option>').join('')+'</select>'
    +'<select data-f="c" aria-label="Centro de la preferencia '+(i+1)+'">'+centreOptionsHTML(p, lists[i])+'</select>'
    +'<span class="pb"><button type="button" data-act="up" aria-label="Subir"'+(i===0?' disabled':'')+'>↑</button>'
      +'<button type="button" data-act="down" aria-label="Bajar"'+(i===prefs.length-1?' disabled':'')+'>↓</button>'
      +'<button type="button" data-act="del" aria-label="Quitar"'+(prefs.length===1?' disabled':'')+'>✕</button></span></div>'
  ).join('');
  const max = META.max_preferencias;
  $('p-add').disabled = prefs.length>=max;
  $('p-msg').textContent = prefs.length>=max ? 'Máximo '+max+' preferencias.' : '';
}

function scenCard(s){
  let body;
  if (s.fuera_de_rango) body = '<p class="muted">Este turno queda después del último nº del listado ('+fmt(META.n_max)+'). No hay datos para simularlo.</p>';
  else if (s.resultado){ const r=s.resultado;
    body = '<div class="esp">'+esc(r.especialidad)+'</div><div>'+esc(r.centro)+'</div><div>'+esc(r.localidad)+' · '+esc(r.comunidad)+'</div>'
      +'<div class="muted">Preferencia '+r.preferencia+' de tu lista. En la realidad la eligió el nº '+fmt(r.n)+'.</div>'; }
  else body = '<p class="muted">Ninguna plaza de tu lista seguía libre. Añade más preferencias.</p>';
  return '<div class="sc'+(s.principal?' main':'')+'"><div class="sc-h"><span>'+s.etiqueta+'</span><b>nº '+fmt(s.orden)+'</b></div>'+body+'</div>';
}
const PILL = {tu_plaza:['ok','Tu plaza'], libre:['free','Libre'], agotada:['bad','Agotada'], sin_datos:['na','Sin datos']};
function renderEstados(list){
  return list.map(s=>{
    let [cls, txt] = PILL[s.estado];
    if (s.estado==='sin_datos' && /fiables|sigue eligiéndose/.test(s.detalle)) txt = 'Sin datos fiables';
    return '<div class="st"><span class="pn">'+s.pref+'</span><span><b>'+esc(s.etiqueta)+'</b></span><span class="pill '+cls+'">'+txt+'</span><span class="why">'+esc(s.detalle)+'</span></div>';
  }).join('');
}
function renderQuedaba(list){
  return list.map(x=>{
    let tag;
    if (x.estado==='libres') tag='<span class="tag">'+(x.mas?'+':'')+x.libres+'</span>';
    else if (x.estado==='agotada') tag='<span class="tag gone">Agotada nº '+fmt(x.ultimo)+'</span>';
    else tag='<span class="tag nd">Sin datos</span>';
    return '<div class="lf"><span>'+esc(x.especialidad)+'</span>'+tag+'</div>';
  }).join('');
}
function renderCercanos(list){
  if (!list.length) return '<div class="empty">Tu turno queda fuera del listado.</div>';
  return list.map(r=>'<div class="r'+(r.tu_turno?' me':'')+'"><span class="num k">'+r.n+'</span><span class="esp">'+esc(r.especialidad)+'</span><span class="cen">'+esc(r.centro)+'<small class="muted" style="display:block">'+esc(r.localidad)+'</small></span></div>').join('');
}

function payload(){
  const n = dec($('sn').value), x = dec($('sx').value);
  return {escala:$('sc').value, netas:isNaN(n)?null:n, expediente:isNaN(x)?null:x,
          orden:num($('so').value), margen:num($('sm').value) ?? 10,
          prefs:prefs.map(p=>({e:p.e, g:p.g||null, c:p.c}))};
}
let simSeq = 0;
async function simResults(){
  const mine = ++simSeq;
  let d;
  try { d = await api('/api/simulador', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload())}); }
  catch(e){ $('sim-res').innerHTML = '<div class="empty">'+esc(e.message)+'</div>'; return; }
  if (mine !== simSeq) return;
  const c = d.calculo;
  if (!c){
    $('o-ord').textContent='–'; $('o-tot').textContent='–'; $('o-rng').textContent='nº de orden estimado';
    $('sim-res').innerHTML='<div class="empty">Escribe tus netas y tu expediente, o tu nº de orden.</div>';
    $('sim-st').innerHTML=''; $('sim-left').innerHTML=''; $('sim-near').innerHTML=''; $('left-hint').textContent='';
    return;
  }
  $('o-ord').textContent = '~'+fmt(c.orden);
  $('o-rng').textContent = c.mejor===c.peor ? 'nº de orden' : 'nº de orden estimado · entre '+fmt(c.mejor)+' y '+fmt(c.peor);
  $('o-tot').textContent = c.nota===null ? 'Nº de orden introducido' : f2(c.nota);
  $('sim-res').innerHTML = '<div class="scen">'+d.escenarios.map(scenCard).join('')+'</div>';
  $('sim-st').innerHTML = renderEstados(d.estados);
  const fuera = c.orden > d.n_max;
  $('left-hint').textContent = fuera ? 'Tu turno queda fuera del listado.' : 'Plazas libres por especialidad al llegar el nº '+fmt(c.orden)+'. El + indica que hay más tras el nº '+fmt(d.n_max)+'.';
  $('sim-left').innerHTML = renderQuedaba(d.quedaba);
  $('sim-near').innerHTML = renderCercanos(d.cercanos);
  $('p-see').dataset.orden = c.orden;
  saveSim();
}
const simSoon = debounce(simResults, 150);

function saveSim(){
  try{ localStorage.setItem(KEY, JSON.stringify({sc:$('sc').value,sa:$('sa').value,se:$('se').value,sn:$('sn').value,sx:$('sx').value,so:$('so').value,sm:$('sm').value,prefs})); }catch(e){}
}
function loadSim(){
  let s=null; try{ s=JSON.parse(localStorage.getItem(KEY)||'null'); }catch(e){}
  const d = s || {sc:META.escalas[0],sa:'150',se:'40',sn:'136,67',sx:'7,5',so:'',sm:'10'};
  ['sc','sa','se','sn','sx','so','sm'].forEach(k=>{ if(d[k]!==undefined) $(k).value=d[k]; });
  const valid = s && Array.isArray(s.prefs) && s.prefs.length;
  prefs = valid ? s.prefs.filter(p=>p&&typeof p==='object').map(p=>({e:p.e??null, g:p.g||'', c:p.c??null}))
                : META.prefs_ejemplo.map(p=>({e:p.e, g:p.g||'', c:null}));
  if (!prefs.length) prefs = [{e:null,g:'',c:null}];
}
function syncNetas(){
  const a=num($('sa').value), e=num($('se').value);
  if (a!==null) $('sn').value = f2(a-(e||0)/3);
}
async function initSim(){
  $('sc').innerHTML = META.escalas.map(e=>'<option value="'+e+'">MIR '+e+'</option>').join('');
  loadSim();
  await renderPrefs();
  ['sc','sx','so','sm','sn'].forEach(k=>$(k).addEventListener('input', simSoon));
  ['sa','se'].forEach(k=>$(k).addEventListener('input', ()=>{ syncNetas(); simSoon(); }));
  $('prefs').addEventListener('change', async e=>{
    const row = e.target.closest('.pref'); if(!row) return;
    const p = prefs[+row.dataset.i], f = e.target.dataset.f; if(!f) return;
    if (f==='e') p.e = e.target.value===''?null:+e.target.value;
    else if (f==='g') p.g = e.target.value;
    else p.c = e.target.value===''?null:+e.target.value;
    if (f==='e' || f==='g'){ p.c=null; row.querySelector('[data-f=c]').innerHTML = centreOptionsHTML(p, await centrosDe(p)); }
    simResults();
  });
  $('prefs').addEventListener('click', async e=>{
    const b = e.target.closest('button[data-act]'); if(!b) return;
    const i = +b.closest('.pref').dataset.i, act = b.dataset.act;
    if (act==='del' && prefs.length>1) prefs.splice(i,1);
    if (act==='up' && i>0) [prefs[i-1],prefs[i]]=[prefs[i],prefs[i-1]];
    if (act==='down' && i<prefs.length-1) [prefs[i+1],prefs[i]]=[prefs[i],prefs[i+1]];
    await renderPrefs(); simResults();
  });
  $('p-add').addEventListener('click', async ()=>{
    if (prefs.length>=META.max_preferencias) return;
    prefs.push({e:null,g:'',c:null}); await renderPrefs(); simResults();
    const last = $('prefs').lastElementChild; if(last) last.querySelector('select').focus();
  });
  $('p-see').addEventListener('click', async ()=>{
    const n = num($('p-see').dataset.orden); if(!n) return;
    Object.assign(st,{q:'',e:'',g:'',p:'',c:'',n1:n,n2:null,view:'list',limit:100});
    $('q').value=''; $('n1').value=n; $('n2').value='';
    await buildSelects(); render(); window.scrollTo({top:0});
  });
}

/* ---------- Arranque ---------- */
(async function(){
  META = await api('/api/meta');
  $('k-n').textContent = fmt(META.total);
  await buildSelects();
  await initSim();
  render();
})();
