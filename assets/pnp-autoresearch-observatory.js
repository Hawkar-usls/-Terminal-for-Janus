(() => {
'use strict';
const U={
 h:'https://raw.githubusercontent.com/Hawkar-usls/Hrain/janus/fundamentum-structural-memory/data/fundamentum-mirror/LATEST.json',
 i:'https://raw.githubusercontent.com/Hawkar-usls/iNaiHR/janus/fundamentum-associative-memory/data/fundamentum-associative/LATEST.json',
 t:'https://raw.githubusercontent.com/Hawkar-usls/TOPA/janus/pnp-autoresearch-state/data/pnp-autoresearch/LATEST.json',
 c:'https://raw.githubusercontent.com/Hawkar-usls/TOPA/janus/pnp-autoresearch-state/data/pnp-autoresearch/CORPUS.json',
 w:'https://raw.githubusercontent.com/Hawkar-usls/TOPA/janus/pnp-autoresearch-state/data/pnp-autoresearch/CORPUS_WEIGHT_LEDGER.json',
 r:'https://raw.githubusercontent.com/Hawkar-usls/TOPA/janus/pnp-autoresearch-state/data/pnp-autoresearch/DEDUPE_RECEIPT.json',
 g:'https://raw.githubusercontent.com/Hawkar-usls/TOPA/janus/pnp-autoresearch-state/data/pnp-autoresearch/DRIVE_INDEX_RECEIPT.json',
 d:'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/state/JANUS_PNP_AUTORESEARCH_CONTEXT.json',
 f:'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/policy/JANUS_RESEARCH_ORGAN_FABRIC.json'
};
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const short=(v,n=16)=>{const s=String(v||'—');return s.length>n?s.slice(0,n)+'…':s};
async function get(url,optional=false){try{const r=await fetch(url+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP_'+r.status);return await r.json()}catch(e){if(optional)return {status:'UNAVAILABLE',error:String(e)};throw e}}

function corpusBundleSafe(c,w,r){
 return c?.schema==='janus.topa.pnp_corpus.v1'
   && c?.P_VS_NP==='OPEN'
   && c?.D1==='EMPTY'
   && c?.successor_algorithm==='LOCKED'
   && w?.schema==='janus.topa.pnp_corpus_weight_ledger.v1'
   && r?.schema==='janus.topa.pnp_corpus_dedupe_receipt.v1'
   && r?.status==='PASS'
   && typeof c?.semantic_sha256==='string'
   && typeof w?.semantic_sha256==='string'
   && w?.corpus_semantic_sha256===c?.semantic_sha256
   && r?.corpus_semantic_sha256===c?.semantic_sha256
   && r?.ledger_semantic_sha256===w?.semantic_sha256;
}

function supervisorSafe(d,f){
 const s=d?.research_supervisor||{};
 const p=f?.promotion_barrier||{};
 return s.schema==='janus.research_supervisor_state.v1'
   && s.status==='ACTIVE_FAIL_CLOSED'
   && s.promotion_barrier==='BLOCKED'
   && s.scientific_claim_promotion===false
   && s.fundamentum_mutation===false
   && s.autonomous_merge===false
   && s.p_vs_np_auto_promotion===false
   && p.p_vs_np_auto_promotion===false
   && p.autonomous_merge===false
   && p.fundamentum_mutation===false;
}

function install(){
 const view=$('view-research'); if(!view)return;
 const cards=view.querySelector('.cards-grid'); if(!cards)return;

 if(!$('pnp-auto-panel')){
   const a=document.createElement('article');a.id='pnp-auto-panel';a.className='card wide';
   a.innerHTML='<div class="card-title-row"><h3>AUTONOMOUS P-vs-NP LOOP</h3><span id="pnp-auto-state" class="pill">RESOLVING</span></div>'+
   '<div class="kv-stack">'+
   '<div class="kv-row"><span>HRAiN structural memory</span><b id="pnp-h">—</b></div>'+
   '<div class="kv-row"><span>iNaiHR associative memory</span><b id="pnp-i">—</b></div>'+
   '<div class="kv-row"><span>TOPA internet spider</span><b id="pnp-t">—</b></div>'+
   '<div class="kv-row"><span>PNP deduplicated corpus</span><b id="pnp-c">—</b></div>'+
   '<div class="kv-row"><span>TOPA attention ledger</span><b id="pnp-w">—</b></div>'+
   '<div class="kv-row"><span>corpus state bundle</span><b id="pnp-bind">—</b></div>'+
   '<div class="kv-row"><span>private Drive corpus sync</span><b id="pnp-g">—</b></div>'+
   '<div class="kv-row"><span>Demiurge own research</span><b id="pnp-d">—</b></div>'+
   '<div class="kv-row"><span>Fundamentum mutation</span><b>FALSE</b></div>'+
   '<div class="kv-row"><span>automatic P=NP promotion</span><b>FALSE</b></div>'+
   '</div><div class="law">HRAiN → iNaiHR → TOPA SPIDER/CORPUS → DEMIURGE → NATIVE WAKE. ATTENTION WEIGHT != EVIDENCE · DRIVE SYNC != SCIENTIFIC RESULT · SOURCE MEMORY AND JANUS OWN RESEARCH REMAIN SEPARATE.</div>';
   cards.prepend(a);
 }

 if(!$('research-organ-panel')){
   const o=document.createElement('article');o.id='research-organ-panel';o.className='card wide';
   o.innerHTML='<div class="card-title-row"><h3>RESEARCH ORGAN FABRIC</h3><span id="organ-fabric-state" class="pill">RESOLVING</span></div>'+
   '<div class="kv-stack">'+
   '<div class="kv-row"><span>reusable verifier / coordinator organs</span><b id="organ-count">—</b></div>'+
   '<div class="kv-row"><span>mandatory route stages</span><b id="organ-stage-count">—</b></div>'+
   '<div class="kv-row"><span>Fundamentum source binding</span><b id="organ-source-binding">—</b></div>'+
   '<div class="kv-row"><span>scientific promotion barrier</span><b id="organ-promotion">BLOCKED</b></div>'+
   '</div>'+
   '<h4>ORGANS</h4><div id="organ-list" class="kv-stack"><div class="empty-state">Resolving cross-repository capabilities…</div></div>'+
   '<h4>CANDIDATE ROUTES</h4><div id="candidate-route-list" class="kv-stack"><div class="empty-state">Resolving supervised candidates…</div></div>'+
   '<div class="law">CAPABILITY != EVIDENCE · REPOSITORY_AVAILABILITY != EXECUTION_RECEIPT · REPLICATION_COUNT != INDEPENDENT_ROOT COUNT · MODEL_OUTPUT != PROOF</div>';
   const first=$('pnp-auto-panel');
   if(first?.nextSibling)cards.insertBefore(o,first.nextSibling);else cards.appendChild(o);
 }
}

function renderOrgans(f){
 const list=$('organ-list'); if(!list)return;
 const organs=Array.isArray(f?.organs)?f.organs:[];
 list.innerHTML=organs.length?organs.map(o=>'<div class="kv-row"><span>'+esc(o.id)+'<small>'+esc(o.repository)+' · '+esc(o.role)+'</small></span><b>'+esc(short(o.capability,42))+'</b></div>').join(''):'<div class="empty-state">Organ policy unavailable. No capability inference is allowed.</div>';
}

function renderRoutes(d){
 const list=$('candidate-route-list'); if(!list)return;
 const routes=Array.isArray(d?.research_supervisor?.candidate_routes)?d.research_supervisor.candidate_routes:[];
 list.innerHTML=routes.length?routes.map(r=>{
   const blocked=r.promotion_barrier==='BLOCKED';
   return '<div class="kv-row"><span>'+esc(r.candidate_id)+'<small>'+esc(r.status||'UNRESOLVED')+'</small></span><b>'+esc(r.next_required_stage||'UNRESOLVED')+(blocked?' · BLOCKED':'')+'</b></div>';
 }).join(''):'<div class="empty-state">No supervised candidate routes published. Silence is not negative evidence.</div>';
}

async function refresh(){
 install(); if(!$('pnp-auto-panel'))return;
 const [h,i,t,corpus,weights,dedupe,drive,d,f]=await Promise.all([get(U.h,true),get(U.i,true),get(U.t,true),get(U.c,true),get(U.w,true),get(U.r,true),get(U.g,true),get(U.d,true),get(U.f,true)]);

 $('pnp-h').textContent=(h.status||'UNRESOLVED')+' · '+short(h.source_commit)+' · '+(h.entry_count??'—')+' files';
 $('pnp-i').textContent=(i.status||'UNRESOLVED')+' · '+(i.topa_query_seed_count??'—')+' query seeds';
 $('pnp-t').textContent=(t.status||'UNRESOLVED')+' · '+(t.record_count??0)+' records · '+(t.edge_count??0)+' edges';
 $('pnp-c').textContent=(corpus.status||'UNRESOLVED')+' · '+(corpus.record_count??0)+' unique · '+(corpus.new_publication_count??0)+' new';
 $('pnp-w').textContent=(weights.status||'UNRESOLVED')+' · '+(weights.weight_count??0)+' weighted · truth=FALSE';
 const bundleSafe=corpusBundleSafe(corpus,weights,dedupe);
 $('pnp-bind').textContent=bundleSafe?'BOUND · PASS':'UNBOUND / MIXED · FAIL-CLOSED';
 $('pnp-g').textContent=(drive.status||'UNRESOLVED')+' · '+(drive.source||'NO LIVE DRIVE RECEIPT');
 $('pnp-d').textContent=(d.status||'UNRESOLVED')+' · '+short(d.context_sha256);
 const ready=[h,i,t,corpus,weights,dedupe].every(x=>!['UNAVAILABLE','UNRESOLVED'].includes(String(x.status||''))) && bundleSafe;
 const pill=$('pnp-auto-state');pill.textContent=ready?'AUTOMATIC · LIVE · BOUND':'PARTIAL / BOOTSTRAP';pill.classList.toggle('live',ready);pill.classList.toggle('warn',!ready);

 const s=d?.research_supervisor||{};
 $('organ-count').textContent=s.organ_count??(Array.isArray(f?.organs)?f.organs.length:'—');
 $('organ-stage-count').textContent=s.route_stage_count??(Array.isArray(f?.route)?f.route.length:'—');
 $('organ-source-binding').textContent=s.source_binding_current===true?'CURRENT':s.source_binding_current===false?'STALE / UNRESOLVED':'—';
 $('organ-promotion').textContent=s.promotion_barrier||'BLOCKED';
 renderOrgans(f);renderRoutes(d);

 const safe=supervisorSafe(d,f);
 const op=$('organ-fabric-state');
 op.textContent=safe?'ACTIVE · FAIL-CLOSED':'DEGRADED · NO PROMOTION';
 op.classList.toggle('live',safe);
 op.classList.toggle('warn',!safe);
}
function boot(){install();refresh();setInterval(refresh,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.JANUS_PNP_AUTORESEARCH={automatic:true,source_mutation:false,automatic_claim_promotion:false,research_supervisor:true,pnp_corpus_fabric:true,corpus_weights_are_evidence:false,corpus_bundle_must_bind:true,urls:U};
})();
