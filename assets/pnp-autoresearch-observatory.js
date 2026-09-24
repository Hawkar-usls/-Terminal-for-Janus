(() => {
'use strict';
const U={
 h:'https://raw.githubusercontent.com/Hawkar-usls/Hrain/janus/fundamentum-structural-memory/data/fundamentum-mirror/LATEST.json',
 i:'https://raw.githubusercontent.com/Hawkar-usls/iNaiHR/janus/fundamentum-associative-memory/data/fundamentum-associative/LATEST.json',
 t:'https://raw.githubusercontent.com/Hawkar-usls/TOPA/janus/pnp-autoresearch-state/data/pnp-autoresearch/LATEST.json',
 d:'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/state/JANUS_PNP_AUTORESEARCH_CONTEXT.json',
 f:'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/policy/JANUS_RESEARCH_ORGAN_FABRIC.json',
 k:'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/state/KEYMASTER_MECHANISM_COMPOSITION_LATEST.json',
 kb:'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/state/KEYMASTER_TRUMP_BRIDGE_LATEST.json'
};
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const short=(v,n=16)=>{const s=String(v||'—');return s.length>n?s.slice(0,n)+'…':s};
async function get(url,optional=false){try{const r=await fetch(url+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP_'+r.status);return await r.json()}catch(e){if(optional)return {status:'UNAVAILABLE',error:String(e)};throw e}}

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

function keymasterSafe(k){
 const fw=k?.firewall||{};
 return k?.schema==='janus.keymaster.mechanism_composition_report.v1'
   && k?.mode==='PROOF_CARRYING_MECHANISM_COMPOSITION'
   && fw.P_VS_NP==='OPEN'
   && fw.D1==='EMPTY'
   && fw.automatic_d1_promotion===false
   && fw.automatic_p_equals_np_claim===false
   && fw.automatic_theorem_promotion===false
   && fw.complete_path_is_proof===false
   && fw.fundamentum_is_scientific_authority===true;
}

function keymasterBridgeSafe(b){
 const fw=b?.firewall||{};
 const sa=b?.self_application||{};
 return b?.schema==='janus.keymaster.trump_runtime_bridge.v1'
   && b?.status==='CANDIDATE_RUNTIME_SELECTED'
   && fw.P_VS_NP==='OPEN'
   && fw.D1==='EMPTY'
   && fw.route_coverage_is_probability===false
   && fw.complete_route_is_proof===false
   && sa.mode==='CANDIDATE_INTERNAL_TASKS_ONLY'
   && sa.proof_authority===false
   && sa.scientific_claim_promotion_authority===false
   && sa.direct_main_writeback===false
   && sa.automatic_merge===false;
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
   '<div class="kv-row"><span>Demiurge own research</span><b id="pnp-d">—</b></div>'+
   '<div class="kv-row"><span>Fundamentum mutation</span><b>FALSE</b></div>'+
   '<div class="kv-row"><span>automatic P=NP promotion</span><b>FALSE</b></div>'+
   '</div><div class="law">HRAiN → iNaiHR → TOPA SPIDER → DEMIURGE → NATIVE WAKE. SOURCE MEMORY AND JANUS OWN RESEARCH REMAIN SEPARATE.</div>';
   cards.prepend(a);
 }

 if(!$('keymaster-panel')){
   const k=document.createElement('article');k.id='keymaster-panel';k.className='card wide';
   k.innerHTML='<div class="card-title-row"><h3>KEYMASTER · MECHANISM COMPOSITION</h3><span id="keymaster-state" class="pill">RESOLVING</span></div>'+
   '<div class="keymaster-progress">'+
   '<div class="keymaster-progress-head"><span>proof-readiness stage</span><b id="keymaster-proof-stage">—</b></div>'+
   '<div class="keymaster-progress-track"><i id="keymaster-progress-fill"></i></div>'+
   '<div class="keymaster-progress-foot"><span id="keymaster-route-coverage">—</span><span>ROUTE COVERAGE · NOT P=NP PROBABILITY</span></div>'+
   '</div>'+
   '<div class="kv-stack">'+
   '<div class="kv-row"><span>latest composition report</span><b id="keymaster-report">—</b></div>'+
   '<div class="kv-row"><span>authority artifacts</span><b id="keymaster-authority-artifacts">—</b></div>'+
   '<div class="kv-row"><span>authoritative / candidate edges</span><b id="keymaster-edges">—</b></div>'+
   '<div class="kv-row"><span>open missing interfaces</span><b id="keymaster-open">—</b></div>'+
   '<div class="kv-row"><span>complete universal lifecycle candidates</span><b id="keymaster-complete">—</b></div>'+
   '<div class="kv-row"><span>best lockpick target</span><b id="keymaster-best">—</b></div>'+
   '<div class="kv-row"><span>best routing score</span><b id="keymaster-score">—</b></div>'+
   '<div class="kv-row"><span>proved context / path if closed</span><b id="keymaster-coverage">—</b></div>'+
   '<div class="kv-row"><span>TRUMP selected runtime</span><b id="keymaster-runtime">—</b></div>'+
   '<div class="kv-row"><span>JANUS self-application</span><b id="keymaster-self-application">—</b></div>'+
   '</div>'+
   '<h4>AUTONOMOUS LOCKPICK FORGE</h4>'+
   '<div class="kv-stack">'+
   '<div class="kv-row"><span>forge status</span><b id="keymaster-forge-status">—</b></div>'+
   '<div class="kv-row"><span>cycles / distinct / duplicate</span><b id="keymaster-forge-counts">—</b></div>'+
   '<div class="kv-row"><span>active forge target</span><b id="keymaster-forge-target">—</b></div>'+
   '<div class="kv-row"><span>latest candidate algorithm</span><b id="keymaster-forge-candidate">—</b></div>'+
   '<div class="kv-row"><span>next candidate gate</span><b id="keymaster-forge-next">—</b></div>'+
   '<div class="kv-row"><span>proof/shadow admission</span><b id="keymaster-forge-admission">FALSE / FALSE</b></div>'+
   '</div>'+
   '<h4>TOP MISSING INTERFACES</h4><div id="keymaster-frontier-list" class="kv-stack"><div class="empty-state">Resolving Keymaster frontier…</div></div>'+
   '<h4>CANDIDATE-ONLY MECHANISMS</h4><div id="keymaster-candidate-list" class="kv-stack"><div class="empty-state">Resolving candidate mechanisms…</div></div>'+
   '<div class="law">LOCKPICK SCORE = ROUTING PRIORITY, NOT PROBABILITY OR P=NP PROGRESS.</div>'+
   '<div class="law">REPORT COMPLETE != UNIVERSAL SOLVER COMPLETE · COMPLETE PATH != PROOF · P_VS_NP=OPEN · D1=EMPTY.</div>';
   const first=$('pnp-auto-panel');
   if(first?.nextSibling)cards.insertBefore(k,first.nextSibling);else cards.appendChild(k);
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

function renderKeymaster(k,b){
 const pill=$('keymaster-state'); if(!pill)return;
 const safe=keymasterSafe(k);
 const bridgeSafe=keymasterBridgeSafe(b);
 const queue=Array.isArray(k?.missing_interface_queue)?k.missing_interface_queue:[];
 const best=queue[0]||{};
 const complete=Array.isArray(k?.complete_universal_lifecycle_candidates)?k.complete_universal_lifecycle_candidates:[];
 const candidates=Array.isArray(k?.candidate_only_mechanisms)?k.candidate_only_mechanisms:[];
 const progress=k?.progress_readout||{};
 const stage=Number.isFinite(Number(progress.stage))?Number(progress.stage):(complete.length?3:(queue.length?2:0));
 const stageMax=Number.isFinite(Number(progress.stage_max))?Number(progress.stage_max):5;
 const fallbackCoverage=best.proved_context_edges!==undefined&&best.complete_path_edges_if_closed
   ?100*Number(best.proved_context_edges)/Number(best.complete_path_edges_if_closed)
   :0;
 const routeCoverage=Number.isFinite(Number(progress.best_route_coverage_percent))
   ?Number(progress.best_route_coverage_percent)
   :fallbackCoverage;
 const boundedCoverage=Math.max(0,Math.min(100,routeCoverage));
 const forge=k?.autonomous_forge||{};
 const forgeTarget=forge?.target||{};
 const forgeCandidate=forge?.candidate||{};
 const forgeAuthority=forge?.authority||{};

 $('keymaster-report').textContent=(k?.status||'UNRESOLVED')+' · '+short(k?.report_sha256,18);
 $('keymaster-authority-artifacts').textContent=k?.authority_artifact_count??'—';
 $('keymaster-edges').textContent=(k?.authoritative_edge_count??'—')+' / '+(k?.candidate_edge_count??'—');
 $('keymaster-open').textContent=queue.length;
 $('keymaster-complete').textContent=complete.length;
 $('keymaster-best').textContent=best.from_type&&best.to_type?short(best.from_type,30)+' → '+short(best.to_type,34):'—';
 $('keymaster-score').textContent=best.lockpick_score!==undefined?best.lockpick_score+' routing pts':'—';
 $('keymaster-coverage').textContent=best.proved_context_edges!==undefined&&best.complete_path_edges_if_closed!==undefined
   ?best.proved_context_edges+' / '+best.complete_path_edges_if_closed+' edges'
   :'—';
 $('keymaster-proof-stage').textContent='STAGE '+stage+' / '+stageMax;
 $('keymaster-route-coverage').textContent=boundedCoverage.toFixed(1)+'% best typed route';
 const fill=$('keymaster-progress-fill'); if(fill)fill.style.width=boundedCoverage+'%';
 $('keymaster-runtime').textContent=bridgeSafe?(b.selected_source_id||'NO_ADMITTED_RUNTIME'):'UNRESOLVED / FALLBACK';
 $('keymaster-self-application').textContent=bridgeSafe
   ?(b?.self_application?.mode||'CANDIDATE_INTERNAL_TASKS_ONLY')+' · AUTO-SWITCH '+String(b?.self_application?.automatic_switch_to_higher_ranked_admitted_runtime===true)
   :'FAIL-CLOSED';
 $('keymaster-forge-status').textContent=forge.status||'NOT_CONNECTED';
 $('keymaster-forge-counts').textContent=(forge.cycle_count??0)+' / '+(forge.distinct_candidate_count??0)+' / '+(forge.duplicate_candidate_count??0);
 $('keymaster-forge-target').textContent=forgeTarget.from_type&&forgeTarget.to_type
   ?short(forgeTarget.from_type,28)+' → '+short(forgeTarget.to_type,34)
   :'—';
 $('keymaster-forge-candidate').textContent=forgeCandidate.candidate_id
   ?short(forgeCandidate.candidate_id,62)+' · '+(forgeCandidate.status||'CANDIDATE')
   :'—';
 $('keymaster-forge-next').textContent=forge.next_action||'—';
 $('keymaster-forge-admission').textContent=String(forgeAuthority.proof===true).toUpperCase()+' / '+String(forge.keymaster_shadow_admission===true).toUpperCase();

 const frontier=$('keymaster-frontier-list');
 if(frontier){
   const top=queue.slice(0,6);
   frontier.innerHTML=top.length?top.map((r,i)=>
     '<div class="kv-row"><span>#'+String(i+1).padStart(2,'0')+' '+esc(short(r.from_type,28))+' → '+esc(short(r.to_type,34))+
     '<small>prefix '+esc(r.proved_prefix_edges??'—')+' · suffix '+esc(r.proved_suffix_edges??'—')+' · context '+esc(r.proved_context_edges??'—')+
     ' · barrier '+esc(r.barrier_penalty??0)+'</small></span><b>SCORE '+esc(r.lockpick_score??'—')+'</b></div>'
   ).join(''):'<div class="empty-state">No missing-interface queue published. Silence is not a proof of closure.</div>';
 }

 const candidateBox=$('keymaster-candidate-list');
 if(candidateBox){
   candidateBox.innerHTML=candidates.length?candidates.map(m=>
     '<div class="kv-row"><span>'+esc(m.id||'UNNAMED')+'<small>'+esc(m.input_type||'—')+' → '+esc(m.output_type||'—')+'</small></span><b>'+esc(m.status||'CANDIDATE')+'</b></div>'
   ).join(''):'<div class="empty-state">No candidate-only mechanisms in the latest report.</div>';
 }

 pill.textContent=safe&&bridgeSafe?'STAGE '+stage+'/'+stageMax+' · '+boundedCoverage.toFixed(1)+'% ROUTE':safe?'REPORT LIVE · BRIDGE DEGRADED':'UNRESOLVED · NO CLAIM';
 pill.classList.toggle('live',safe&&bridgeSafe);
 pill.classList.toggle('warn',!safe||!bridgeSafe);
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
 const [h,i,t,d,f,k,kb]=await Promise.all([get(U.h,true),get(U.i,true),get(U.t,true),get(U.d,true),get(U.f,true),get(U.k,true),get(U.kb,true)]);

 const s=d?.research_supervisor||{};
 const sourceCommits=[h?.source_commit,i?.source_commit,t?.source_commit].filter(Boolean);
 const sourcesAligned=sourceCommits.length===3 && sourceCommits.every(x=>x===sourceCommits[0]);
 const sourcesAvailable=[h,i,t].every(x=>!['UNAVAILABLE','UNRESOLVED'].includes(String(x.status||'')));
 const sourceBindingCurrent=s.source_binding_current===true && sourcesAligned;
 const ready=sourcesAvailable && sourceBindingCurrent;

 $('pnp-h').textContent=(h.status||'UNRESOLVED')+' · '+short(h.source_commit)+' · '+(h.entry_count??'—')+' files';
 $('pnp-i').textContent=(i.status||'UNRESOLVED')+' · '+short(i.source_commit)+' · '+(i.topa_query_seed_count??'—')+' query seeds';
 $('pnp-t').textContent=(t.status||'UNRESOLVED')+' · '+short(t.source_commit)+' · '+(t.record_count??0)+' records · '+(t.edge_count??0)+' edges';
 $('pnp-d').textContent=(d.status||'UNRESOLVED')+' · '+short(d.context_sha256);
 const pill=$('pnp-auto-state');
 pill.textContent=ready?'AUTOMATIC · LIVE':sourcesAvailable?'SOURCE BINDING STALE':'PARTIAL / BOOTSTRAP';
 pill.classList.toggle('live',ready);
 pill.classList.toggle('warn',!ready);

 $('organ-count').textContent=s.organ_count??(Array.isArray(f?.organs)?f.organs.length:'—');
 $('organ-stage-count').textContent=s.route_stage_count??(Array.isArray(f?.route)?f.route.length:'—');
 $('organ-source-binding').textContent=s.source_binding_current===true?'CURRENT':s.source_binding_current===false?'STALE / UNRESOLVED':'—';
 $('organ-promotion').textContent=s.promotion_barrier||'BLOCKED';
 renderKeymaster(k,kb);renderOrgans(f);renderRoutes(d);

 const safe=supervisorSafe(d,f);
 const op=$('organ-fabric-state');
 op.textContent=safe?'ACTIVE · FAIL-CLOSED':'DEGRADED · NO PROMOTION';
 op.classList.toggle('live',safe);
 op.classList.toggle('warn',!safe);
}
function boot(){install();refresh();setInterval(refresh,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.JANUS_PNP_AUTORESEARCH={automatic:true,source_mutation:false,automatic_claim_promotion:false,research_supervisor:true,keymaster_observability:true,keymaster_authority:false,keymaster_route_coverage_is_probability:false,keymaster_self_application:'CANDIDATE_INTERNAL_TASKS_ONLY',keymaster_autonomous_forge_observable:true,keymaster_autonomous_forge_grants_proof:false,urls:U};
})();
