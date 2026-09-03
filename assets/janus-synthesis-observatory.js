(() => {
'use strict';

const SYNTH_URL='https://raw.githubusercontent.com/Hawkar-usls/iNaiHR/main/janus-synth/state/JANUS_SYNTH_LATEST.json';
const EXPECTED_SCHEMA='janus.inaihr.semantic_evolution.v2';
const REFRESH_MS=60000;
let lastStateSha=null;
let lastSynthState=null;

function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function short(v,n=12){const s=String(v||'—');return s.length>n?s.slice(0,n)+'…':s;}
function addStyle(){
 if(document.getElementById('janus-synthesis-style'))return;
 const s=document.createElement('style');s.id='janus-synthesis-style';s.textContent=`
 .synth-flow{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:14px 0 20px}.synth-flow span{padding:8px 10px;border:1px solid rgba(0,255,163,.22);border-radius:8px;background:rgba(0,255,163,.035);font:600 .72rem 'IBM Plex Mono',monospace;color:#9bcbbb}.synth-flow i{color:#54edbb;font-style:normal}
 .synth-list{display:grid;gap:12px}.synth-card{border:1px solid rgba(0,255,163,.18);border-radius:14px;background:rgba(4,12,14,.72);padding:16px}.synth-card h3{margin:.25rem 0 .6rem;font-size:.92rem;color:#c9eee2}.synth-card .synth-meta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}.synth-card .synth-meta span{font:600 .67rem 'IBM Plex Mono',monospace;color:#72cbae;border:1px solid rgba(114,203,174,.18);border-radius:999px;padding:4px 7px}.synth-card p{margin:.35rem 0;color:#94aca5;line-height:1.48;font-size:.83rem}.synth-card b{color:#c6ddd6}.synth-sources{display:grid;gap:5px;margin-top:9px}.synth-source{font:500 .67rem 'IBM Plex Mono',monospace;color:#6f8e85;overflow-wrap:anywhere;padding-left:8px;border-left:2px solid rgba(200,169,107,.3)}
 .synth-law{margin-top:16px;padding:12px;border:1px solid rgba(255,193,7,.2);border-radius:10px;color:#bea96d;font:600 .72rem 'IBM Plex Mono',monospace}.synth-state-pulse{color:#66f1c1}.synth-state-wait{color:#ffc75b}`;document.head.appendChild(s);
}

function installNeuralLink(){
 if(document.querySelector('script[data-neural-link-v2-runtime]'))return;
 const s=document.createElement('script');
 s.src='./assets/neural-link-v2-runtime.js';
 s.dataset.neuralLinkV2Runtime='1';
 document.head.appendChild(s);
}

function installView(){
 addStyle();
 if(document.getElementById('view-synthesis'))return;
 const sideFoot=document.querySelector('.sidebar .side-foot');
 const nav=document.createElement('button');nav.className='nav-btn';nav.dataset.view='synthesis';nav.type='button';nav.innerHTML='<span class="nav-icon">⟁</span><span>SYNTHESIS</span>';
 if(sideFoot)sideFoot.before(nav);else document.querySelector('.sidebar')?.appendChild(nav);

 const section=document.createElement('section');section.id='view-synthesis';section.className='view cards-view observatory-view';section.innerHTML=`
 <div class="observatory-head"><div><div class="kicker">Durable autonomous semantic evolution</div><h2>JANUS Synthesis</h2><p>Candidate meanings reconstructed from existing HRaiN/iNaiHR links. This view reads the same persisted synthesis state produced autonomously by JANUS.</p></div><div class="live-badge"><span class="dot"></span><span id="synth-live-status">RESOLVING</span></div></div>
 <div class="metrics-grid compact">
   <article class="metric-card"><label>semantic candidates</label><strong id="synth-count">—</strong><small>durable candidate-only meanings</small></article>
   <article class="metric-card"><label>created last cycle</label><strong id="synth-created">—</strong><small>no forced fill</small></article>
   <article class="metric-card"><label>current focus</label><strong id="synth-focus">—</strong><small id="synth-focus-age">migrating attention</small></article>
   <article class="metric-card"><label>semantic depth</label><strong id="synth-depth">≤ 4</strong><small>max one depth advance / cycle</small></article>
 </div>
 <div class="synth-flow"><span>EXISTING LINKS</span><i>→</i><span>MIGRATING FOCUS</span><i>→</i><span>COMPOSE</span><i>→</i><span>CANDIDATE</span><i>→</i><span>CORROBORATE / VERIFY</span><i>→</i><span>DEVELOP</span></div>
 <div class="card wide"><div class="card-title-row"><h3>LATEST CANDIDATE MEANINGS</h3><button id="synth-refresh" class="btn" type="button">REFRESH SYNTH</button></div><div id="synth-list" class="synth-list"><div class="empty-state">Resolving iNaiHR semantic evolution state…</div></div></div>
 <div class="synth-law">SYNTHESIS != TRUTH · ATTENTION_WEIGHT != EVIDENCE_WEIGHT · CANDIDATE_EDGE != CAUSAL_EDGE · NO VERIFY => NO VERIFIED FIX</div>`;
 document.querySelector('.workspace')?.appendChild(section);

 nav.addEventListener('click',()=>{
   document.querySelectorAll('.nav-btn').forEach(x=>x.classList.remove('active'));
   document.querySelectorAll('.view').forEach(x=>x.classList.remove('active'));
   nav.classList.add('active');section.classList.add('active');
   const cv=document.getElementById('current-view');if(cv)cv.textContent='SYNTHESIS';
   loadSynth();
 });
 section.querySelector('#synth-refresh')?.addEventListener('click',loadSynth);
}

function validate(x){
 if(!x||x.schema!==EXPECTED_SCHEMA||!Array.isArray(x.candidates)||!Array.isArray(x.created_this_run))throw new Error('SYNTH_SCHEMA_REJECTED');
 if(!Number.isInteger(Number(x.candidate_count))||Number(x.candidate_count)!==x.candidates.length)throw new Error('SYNTH_COUNT_MISMATCH');
 if(x.attention?.attention_weight_is_evidence_weight!==false)throw new Error('ATTENTION_AUTHORITY_REJECTED');
 for(const c of x.candidates){
   if(c.kind!=='SEMANTIC_CANDIDATE'||c.status!=='CANDIDATE_AWAITING_CORROBORATION')throw new Error('NON_CANDIDATE_OBJECT_REJECTED');
   const a=c.authority||{};
   if(a.truth!==false||a.proof!==false||a.causal!==false||a.mutation!==false||a.automatic_promotion!==false)throw new Error('SYNTH_AUTHORITY_REJECTED');
   if(!(Number(c.depth)>=1&&Number(c.depth)<=4))throw new Error('SYNTH_DEPTH_REJECTED');
   const boundaries=Array.isArray(c.meaning?.boundaries)?c.meaning.boundaries:[];
   for(const law of ['SYNTHESIS != TRUTH','ATTENTION_WEIGHT != EVIDENCE_WEIGHT','CANDIDATE_EDGE != CAUSAL_EDGE']){
     if(!boundaries.includes(law))throw new Error(`SYNTH_BOUNDARY_MISSING:${law}`);
   }
 }
 return x;
}

function candidateHtml(c){
 const e=c.meaning?.evidence||{}, src=Array.isArray(e.source_records)?e.source_records:[];
 return `<article class="synth-card"><div class="synth-meta"><span>${esc(c.id)}</span><span>DEPTH ${esc(c.depth)}</span><span>${esc(c.focus_key||'focus:unknown')}</span><span>${esc(c.status)}</span></div><h3>${esc(c.label)}</h3><p><b>Purpose:</b> ${esc(c.meaning?.purpose||'—')}</p><p><b>Mechanism:</b> ${esc(c.meaning?.mechanism||'—')}</p><p><b>Next:</b> ${esc((c.meaning?.next_steps||[])[0]||'Await corroboration.')}</p><div class="synth-sources">${src.map(s=>`<div class="synth-source">${esc(s.path||s.id)} · ${esc(s.status||'UNCLASSIFIED')} · sha ${esc(short(s.sha256,16))}</div>`).join('')}</div></article>`;
}

function publishLogEvent(x=lastSynthState){
 const log=document.getElementById('janus-event-log');if(!log||!x||log.querySelector('[data-terminal-synth-event]'))return;
 const latest=(x.candidates||[]).slice(-1)[0];if(!latest)return;
 const row=document.createElement('div');row.className='log-row';row.dataset.terminalSynthEvent='1';row.innerHTML=`<span class="log-seq">#SYN</span><span class="log-type">COMPOSE</span><span class="log-body">${esc(latest.label)} · durable semantic candidate</span><span class="log-verdict warn">CANDIDATE</span>`;log.prepend(row);
}

async function loadSynth(){
 const status=document.getElementById('synth-live-status');if(status)status.textContent='RESOLVING';
 try{
   const r=await fetch(SYNTH_URL,{cache:'no-store',headers:{Accept:'application/json'}});if(!r.ok)throw new Error('HTTP_'+r.status);
   const x=validate(await r.json());lastSynthState=x;
   document.getElementById('synth-count').textContent=x.candidate_count;
   document.getElementById('synth-created').textContent=x.created_this_run.length;
   document.getElementById('synth-focus').textContent=short(x.attention?.focus_key||'NO ACTIVE FOCUS',28);
   document.getElementById('synth-focus-age').textContent=`focus age ${x.attention?.focus_age??0} · replay fatigue active`;
   document.getElementById('synth-depth').textContent=`${Math.max(0,...x.candidates.map(c=>Number(c.depth)||0))} / ${x.limits?.max_depth??4}`;
   const list=document.getElementById('synth-list'), recent=x.candidates.slice(-12).reverse();list.innerHTML=recent.length?recent.map(candidateHtml).join(''):'<div class="empty-state">No candidate meanings yet. Silence is not negative evidence.</div>';
   if(status){status.textContent='PERSISTED · CANDIDATE ONLY';status.className='synth-state-pulse';}
   if(lastStateSha&&lastStateSha!==x.state_sha256)publishLogEvent(x);lastStateSha=x.state_sha256||null;
   publishLogEvent(x);
 }catch(e){console.warn('JANUS synthesis observatory',e);if(status){status.textContent='DEGRADED · NO CLAIM';status.className='synth-state-wait';}const list=document.getElementById('synth-list');if(list)list.innerHTML='<div class="empty-state">SYNTH state unavailable. This is not negative evidence.</div>';}
}

function boot(){installNeuralLink();installView();document.addEventListener('janus:logs-rendered',()=>publishLogEvent());loadSynth();setInterval(loadSynth,REFRESH_MS);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();