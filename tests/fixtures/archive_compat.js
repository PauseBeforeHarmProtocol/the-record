const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = process.argv[2];
const archive = fs.readFileSync(path.join(root, 'the-record.html'), 'utf8');
const slice = (start, end) => archive.slice(archive.indexOf(start), archive.indexOf(end, archive.indexOf(start)));
if (process.argv[3] === 'permalinks') { testPermalinks(); process.exit(0); }
const context = vm.createContext({ console, assert });
vm.runInContext(`
  const escapeHTML=(s)=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const escapeAttr=escapeHTML;
  const window=globalThis;
  const document={head:{appendChild(){}},createElement(){return {textContent:''}}};
  const E=[
    {current_id:'NAT-2026-09-15-003',era:'term2',year:'2026',sort:'2026-09-15',date:'September 15–October 30, 2026',text:'Election enforcement',sig:'Significance',goal:'Response',mt:'Maybe. Therefore.',tags:['Elections'],src:[{t:'Original order',url:'https://court.example/order'}],gp:1,hi:0,_idx:0,review_status:'current-standard-reviewed',dprec:'day'},
    {legacy_id:'LEG-000123',era:'term1',year:'2017',sort:'2017-01-20',date:'January 20, 2017',text:'Historical event',sig:'Historical significance',goal:'Administration response',tags:['Government'],src:['https://legacy.example/direct-source'],gp:1,hi:1,_idx:0,dprec:'day'},
    {legacy_id:'LEG-000124',era:'formation',year:'1927',sort:'1927-01-01',date:'1927',text:'Context',sig:'',goal:'',tags:[],src:[],gp:0,hi:0,_idx:0,dprec:'year'},
  ];
  let activeEra='all',activeYear='all',activeTag='all',sigOnly=false,gpOnly=false,srch='',topicRegex=null,timelineOrder='desc',pastWeekOnly=false;
  function getWeekCutoff(){return '2026-09-01'}
  ${slice('function filtered(){', 'function toggleTimelineOrder(){')}
  ${slice('function buildEntry(e){', '/* ── VIEW SWITCHING ── */')}
  assert.equal((srch='nat-2026-09-15-003',filtered().length),0,'regression fixture must reproduce the missing-ID haystack');
  assert.ok(buildEntry(E[0]).includes('15–October'),'regression fixture must expose malformed whitespace-token date badge');
  const untouchedRecords=JSON.stringify(E);
`, context);

function testPermalinks() {
  const legacy = JSON.parse(fs.readFileSync(path.join(root, 'data/legacy_entries.json'), 'utf8'));
  const bridge = vm.createContext({ window: {} });
  vm.runInContext(fs.readFileSync(path.join(root, 'current_layer_bridge.js'), 'utf8'), bridge);
  const rows = [...legacy.filter(entry => entry.review_status !== 'superseded'), ...bridge.window.CURRENT_LAYER_BRIDGE];
  const counts = {};
  for (const entry of rows) { entry.tags = []; entry.year = entry.sort.slice(0, 4); entry._idx = counts[entry.sort] || 0; counts[entry.sort] = entry._idx + 1; }
  const redirects = Object.fromEntries(legacy.filter(entry => entry.review_status === 'superseded').map(entry => [entry.legacy_id, { target: entry.superseded_by, reason: entry.superseded_reason }]));
  const context = vm.createContext({ console, assert });
  vm.runInContext(String.raw`
    const window=globalThis;
    const metrics={renderPageCalls:0,renderedEntries:0,feedOpens:0};
    const nodes=new Map();
    class Element {
      constructor(id=''){this.id=id;this.html='';this.children=[];this.style={};this.dataset={};this.listeners={};this.value='';this.classes=new Set();this.classList={add:(v)=>this.classes.add(v),remove:(v)=>this.classes.delete(v),toggle:(v,on)=>on===false?this.classes.delete(v):this.classes.add(v)};}
      set innerHTML(value){this.html=String(value);this.children=[];if(this.id==='static'){for(const id of [...nodes.keys()])if(id.startsWith('e-')||id==='supersededNotice')nodes.delete(id);}this.indexHTML(String(value));}
      get innerHTML(){return this.html;}
      indexHTML(value){for(const match of value.matchAll(/id="(e-[^"]+)"/g))nodes.set(match[1],new Element(match[1]));metrics.renderedEntries+=(value.match(/class="entry /g)||[]).length;}
      insertAdjacentHTML(position,value){this.html+=value;this.indexHTML(value);}
      appendChild(child){this.children.push(child);child.parent=this;if(child.id)nodes.set(child.id,child);return child;}
      prepend(child){this.children.unshift(child);child.parent=this;if(child.id)nodes.set(child.id,child);}
      before(child){if(child.id)nodes.set(child.id,child);}
      remove(){if(this.parent)this.parent.children=this.parent.children.filter(child=>child!==this);if(this.id)nodes.delete(this.id);}
      querySelector(selector){if(selector==='.loadmore')return this.children.find(child=>child.className==='loadmore')||null;const year=/data-year-header="([^"]+)"/.exec(selector)?.[1];return year&&this.html.includes('data-year-header="'+year+'"')?{}:null;}
      querySelectorAll(){return [];}
      addEventListener(type,fn){this.listeners[type]=fn;}
      setAttribute(){}
      scrollIntoView(){this.scrolled=true;}
    }
    const document={head:new Element(),createElement(){return new Element();},querySelectorAll(){return [];},getElementById(id){if(id.startsWith('e-')||id==='supersededNotice')return nodes.get(id)||null;if(!nodes.has(id))nodes.set(id,new Element(id));return nodes.get(id);}};
    window.location={hash:'#LEG-000199'};
    const history={replaceState(a,b,fragment){window.location.hash=String(fragment);}};
    const timers=[];function setTimeout(fn){timers.push(fn);}
    const escapeHTML=(s)=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    const escapeAttr=escapeHTML;
    const E=${JSON.stringify(rows)};
    const SUPERSEDED_REDIRECTS=${JSON.stringify(redirects)};
    const ERAS=[...new Set(E.map(entry=>entry.era))].map(id=>[id,id]);
    const TOPIC_FOLDERS=[],POLS=[];
    const CURRENT_LAYER_META={};
    let activeEra='all',activeYear='all',activeTag='all',sigOnly=false,gpOnly=false,srch='',topicRegex=null,timelineOrder='desc',pastWeekOnly=false;
    let currentView='home',currentPage=0,currentFiltered=[];
    const PAGE_SIZE=100;
    function getWeekCutoff(){return '2026-01-01'}
    function renderTagBar(){} function renderYrStrip(){} function renderYearTabs(){} function buildTimelinePips(){}
    function renderHome(){} function renderTopicFolders(){} function renderYearFolders(){} function renderPolView(){} function renderAiGrid(){}
    ${slice('function resetFilters(o){', 'const PAGE_SIZE=100;')}
    ${slice('function filtered(){', 'function toggleTimelineOrder(){')}
    ${slice('function buildEntry(e){', '/* ── VIEW SWITCHING ── */')}
    ${slice('function switchView(view){', '/* ── POLITICIANS VIEW ── */')}
    ${slice('function renderStatic(){', '/* ── DATE LOOKUP ── */')}
    ${slice('function jumpToHash(){', '/* ── TIMELINE BAR ── */')}
    const realRenderPage=renderPage;
    window.renderPage=function(){metrics.renderPageCalls++;return realRenderPage();};
    const untouchedRecords=JSON.stringify(E);
    jumpToHash();
    assert.ok(metrics.renderPageCalls>10,'original permalink must reproduce rendering every preceding page');
    assert.ok(metrics.renderedEntries>1000,'original regression should reproduce thousands of cards');
    globalThis.originalRenderedCards=metrics.renderedEntries;
    currentView='home';window.location.hash='#LEG-000199';document.getElementById('static').innerHTML='';
    metrics.renderPageCalls=0;metrics.renderedEntries=0;timers.length=0;
  `, context);
  vm.runInContext(fs.readFileSync(path.join(root, 'assets/archive-compat.js'), 'utf8'), context);
  vm.runInContext(String.raw`
    jumpToHash();
    assert.equal(metrics.renderPageCalls,1,'old permalink renders exactly one bounded page');
    assert.ok(metrics.renderedEntries<=PAGE_SIZE,'no preceding pages are mounted');
    assert.equal(currentFiltered.length,E.length,'full ordered dataset remains available for pagination');
    const old=E.find(entry=>entry.legacy_id==='LEG-000199');
    assert.equal(currentPage,Math.floor(currentFiltered.indexOf(old)/PAGE_SIZE));
    assert.ok(document.getElementById('e-LEG-000199'),'exact target is in the bounded page');
    assert.ok(document.getElementById('e-LEG-000199').classes.has('permalink-hl'));
    assert.equal(window.location.hash,'#LEG-000199','entry hash survives view initialization');
    const output=document.getElementById('static');
    const contextNote=output.children.find(child=>child.className==='integrity-note');
    assert.match(contextNote.innerHTML,/Opened at timeline page/);
    const more=output.querySelector('.loadmore');
    if(more){const page=currentPage;more.listeners.click();assert.equal(currentPage,page+1);assert.equal(metrics.renderPageCalls,2);assert.ok(metrics.renderedEntries<=PAGE_SIZE*2);}
    contextNote.children.find(child=>child.className==='backbtn').listeners.click();
    assert.equal(currentPage,0,'Start of timeline restores ordinary pagination');
    assert.equal(window.location.hash,'#timeline');
    const current=E.find(entry=>entry.current_id);
    window.location.hash='#'+current.current_id;currentView='home';
    activeEra='formation';activeYear='1927';activeTag='absent';sigOnly=true;gpOnly=true;srch='unrelated';topicRegex=/will-not-match/;pastWeekOnly=true;
    metrics.renderPageCalls=0;metrics.renderedEntries=0;
    jumpToHash();assert.equal(metrics.renderPageCalls,1);assert.ok(metrics.renderedEntries<=PAGE_SIZE);
    assert.ok(document.getElementById('e-'+current.current_id),'current stable ID opens despite stale view filters');
    assert.equal(pastWeekOnly,false);assert.equal(topicRegex,null);assert.equal(srch,'');
    const retired=Object.keys(SUPERSEDED_REDIRECTS)[0];
    window.location.hash='#'+retired;metrics.renderPageCalls=0;metrics.renderedEntries=0;jumpToHash();
    const target=SUPERSEDED_REDIRECTS[retired].target;
    assert.equal(metrics.renderPageCalls,1);assert.ok(metrics.renderedEntries<=PAGE_SIZE);
    assert.ok(document.getElementById('e-'+target));assert.equal(window.location.hash,'#'+retired);
    assert.ok(document.getElementById('supersededNotice').innerHTML.includes(escapeHTML(retired)));
    assert.ok(document.getElementById('supersededNotice').innerHTML.includes(escapeAttr(target)));
    window.location.hash='#'+old.sort+'_'+old._idx;timelineOrder='asc';metrics.renderPageCalls=0;jumpToHash();
    assert.equal(metrics.renderPageCalls,1);assert.ok(document.getElementById('e-LEG-000199'),'old date-index alias still resolves');assert.equal(timelineOrder,'asc');
    const priorCalls=metrics.renderPageCalls;
    window.location.hash='#not-a-record';jumpToHash();assert.equal(metrics.renderPageCalls,priorCalls,'unknown hash does not render unrelated cards');
    window.location.hash='#%invalid';jumpToHash();assert.equal(metrics.renderPageCalls,priorCalls);
    const pageRenderer=window.renderPage,staticRenderer=window.renderStatic;
    window.renderStatic=()=>{throw Error('forced view initialization failure');};
    currentView='home';window.location.hash='#LEG-000199';
    assert.throws(()=>jumpToHash(),/forced view initialization failure/);
    assert.equal(window.renderPage,pageRenderer,'temporary page suppression is restored even on exceptions');
    assert.equal(window.location.hash,'#LEG-000199','failed view initialization retains the requested stable fragment');
    window.renderStatic=staticRenderer;
    window.TruthFeed={open(){metrics.feedOpens++;}};
    window.location.hash='#feed';jumpToHash();assert.equal(currentView,'feed');assert.equal(metrics.feedOpens,1,'view-level deep links stay wired');
    assert.equal(JSON.stringify(E),untouchedRecords,'permalink presentation must not mutate source records');
    console.log('PASS: bounded real-archive permalinks; old rendered '+originalRenderedCards+' cards, repaired target <= '+PAGE_SIZE+'; '+E.length+' records preserved');
  `, context);
}
vm.runInContext(fs.readFileSync(path.join(root, 'assets/archive-compat.js'), 'utf8'), context);
vm.runInContext(`
  assert.equal(filtered().length,1);
  assert.equal(filtered()[0].current_id,'NAT-2026-09-15-003');
  assert.equal(srch,'nat-2026-09-15-003','search state must be restored');
  srch='#NAT-2026-09-15-003';assert.equal(filtered().length,1);
  srch='LEG-000123';assert.equal(filtered().length,1);
  srch='legacy.example/direct-source';assert.equal(filtered()[0].legacy_id,'LEG-000123','plain-string source URLs are searchable');
  srch='court.example/order';assert.equal(filtered()[0].current_id,'NAT-2026-09-15-003');
  srch='election response';assert.equal(filtered().length,1,'multi-word search preserved');
  srch='nat-2026-09-15-003';activeEra='term1';assert.equal(filtered().length,0,'ID search must not bypass era filters');
  activeEra='all';activeTag='Government';assert.equal(filtered().length,0,'ID search must not bypass tags');
  activeTag='all';sigOnly=true;assert.equal(filtered().length,0,'ID search must not bypass significance filter');
  sigOnly=false;activeYear='2017';assert.equal(filtered().length,0,'ID search must not bypass year filter');
  activeYear='all';srch='';assert.equal(filtered().length,3,'empty query retains normal archive');
  const rangeHTML=buildEntry(E[0]);
  assert.ok(rangeHTML.includes('<span class="edaterange">'+escapeHTML(E[0].date)+'</span>'),'complete range must remain intact');
  assert.ok(!rangeHTML.includes('<span class="eday">15–October</span>'));
  assert.ok(buildEntry(E[1]).includes('<span class="eday">20</span>January<br>2017'),'single-day badge remains structured');
  assert.ok(buildEntry(E[2]).includes('<span class="edaterange">1927</span>'),'year-only label remains intact');
  const unsafe={...E[0],date:'</div><img src=x onerror=alert(1)>'};
  assert.ok(!buildEntry(unsafe).includes('<img src=x'),'date labels and title attributes are escaped');
  assert.ok(buildEntry(unsafe).includes('&lt;img'));
  assert.ok(buildEntry({...E[0],review_status:'corrected'}).includes('<span class="eqastate reviewed">Corrected · reviewed</span>'));
  assert.ok(buildEntry({...E[1],review_status:'in-review'}).includes('In review · not revalidated'));
  assert.ok(buildEntry({...E[1],review_status:'needs-sourcing'}).includes('Needs sourcing · not revalidated'));
  assert.ok(buildEntry({...E[0],review_status:undefined}).includes('Review state not recorded'),'current ID must not invent a review state');
  const intact=E[0];E[0]=null;srch='nat-2026-09-15-003';
  assert.throws(()=>filtered());assert.equal(srch,'nat-2026-09-15-003','exceptions must also restore query state');
  E[0]=intact;srch='';
  assert.equal(JSON.stringify(E),untouchedRecords,'compatibility must not rewrite stored facts, dates or IDs');
  const once=buildEntry(E[0]);
  globalThis.afterFirstInstall=once;
`, context);
// A duplicate script include must not wrap the repaired renderer a second time.
vm.runInContext(fs.readFileSync(path.join(root, 'assets/archive-compat.js'), 'utf8'), context);
vm.runInContext(`
  assert.equal(buildEntry(E[0]),afterFirstInstall,'repair installation is idempotent');
  console.log('PASS: archive stable-ID search and complete date labels');
`, context);
