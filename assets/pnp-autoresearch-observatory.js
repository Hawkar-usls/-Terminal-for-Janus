(() => {
'use strict';
const U={
 h:'https://raw.githubusercontent.com/Hawkar-usls/Hrain/janus/fundamentum-structural-memory/data/fundamentum-mirror/LATEST.json',
 i:'https://raw.githubusercontent.com/Hawkar-usls/iNaiHR/janus/fundamentum-associative-memory/data/fundamentum-associative/LATEST.json',
 t:'https://raw.githubusercontent.com/Hawkar-usls/TOPA/janus/pnp-autoresearch-state/data/pnp-autoresearch/LATEST.json',
 d:'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/state/JANUS_PNP_AUTORESEARCH_CONTEXT.json'
};
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const short=(v,n=16)=>{const s=String(v||'—');return s.length>n?s.slice(0,n)+'…':s};
async function get(url,optional=false){try{const r=await fetch(url+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP_'+r.status);return await r.json()}catch(e){if(optional)return {status:'UNAVAILABLE',error:String(e)};throw e}}
function install(){
 const view=$('view-research'); if(!view||$('pnp-auto-panel'))return;
 const cards=view.querySelector('.cards-grid'); if(!cards)return;
 const a=document.createElement('article');a.id='pnp-auto-panel';a.className='card wide';
 a.innerHTML='<div class="card-title-row"><h3>AUTONOMOUS P-vs-NP LOOP</h3><span id="pnp-auto-state" class="pill">RESOLVING</span></div>'+
 '<div class="kv-stack">'+
 '<div class="kv-row"><span>HRAiN structural memory</span><b id="pnp-h">—</b></div>'+
 '<div class="kv-row"><span>iNaiHR associative memory</span><b id="pnp-i">—</b></div>'+
 '<div class="kv-row"><span>TOPA internet spider</span><b id="pnp-t">—</b></div>'+
 '<div class="kv-row"><span>Demiurge own research</span><b id="pnp-d">—</b></div>'+
 '<div class="kv-row"><span>Fundamentum mutation</span><b>FALSE</b></div>'+
 '<div class="kv-row"><span>automatic P=NP promotion</span><b>FALSE</b></div>'+
 '</div><div class="law">HRAiN → iNaiHR → TOPA SPIDER → DEMIURGE → NATIVE WAKE. SOURCE MEMORY AND JANUS OWN RESEARCH REMAIN SEPARATE.</div>';
 cards.prepend(a);
}
async function refresh(){
 install(); if(!$('pnp-auto-panel'))return;
 const [h,i,t,d]=await Promise.all([get(U.h,true),get(U.i,true),get(U.t,true),get(U.d,true)]);
 $('pnp-h').textContent=(h.status||'UNRESOLVED')+' · '+short(h.source_commit)+' · '+(h.entry_count??'—')+' files';
 $('pnp-i').textContent=(i.status||'UNRESOLVED')+' · '+(i.topa_query_seed_count??'—')+' query seeds';
 $('pnp-t').textContent=(t.status||'UNRESOLVED')+' · '+(t.record_count??0)+' records · '+(t.edge_count??0)+' edges';
 $('pnp-d').textContent=(d.status||'UNRESOLVED')+' · '+short(d.context_sha256);
 const ready=[h,i,t].every(x=>!['UNAVAILABLE','UNRESOLVED'].includes(String(x.status||'')));
 const pill=$('pnp-auto-state');pill.textContent=ready?'AUTOMATIC · LIVE':'PARTIAL / BOOTSTRAP';pill.classList.toggle('live',ready);pill.classList.toggle('warn',!ready);
}
function boot(){install();refresh();setInterval(refresh,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.JANUS_PNP_AUTORESEARCH={automatic:true,source_mutation:false,automatic_claim_promotion:false,urls:U};
})();
