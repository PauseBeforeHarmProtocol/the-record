(function(){
  'use strict';

  const LIVE_URL='https://ix.cnn.io/data/truth-social/truth_archive.json';
  const FALLBACK_URL='data/truth_social_seed.json';
  const FALLBACK_META_URL='data/truth_social_feed_meta.json';
  const PAGE_SIZE=50;
  const state={posts:[],query:'',year:'all',shown:PAGE_SIZE,opened:false,loading:false,mode:'Not loaded',checked:'Loading…'};

  const byId=(id)=>document.getElementById(id);
  const safePostUrl=(value)=>{
    try{
      const url=new URL(String(value||''),window.location.href);
      return url.origin==='https://truthsocial.com'&&/^\/@realDonaldTrump\/\d+\/?$/.test(url.pathname)?url.href:'';
    }catch(_error){return '';}
  };
  const safeMediaUrl=(value)=>{
    try{
      const url=new URL(String(value||''),window.location.href);
      return url.origin==='https://static-assets-1.truthsocial.com'?url.href:'';
    }catch(_error){return '';}
  };
  const stripMarkup=(value)=>{
    const template=document.createElement('template');
    template.innerHTML=String(value||'');
    return (template.content.textContent||'').replace(/\u00a0/g,' ').replace(/[ \t]+\n/g,'\n').trim();
  };
  const countValue=(value)=>{
    if(value===null||value===undefined||value==='')return null;
    const number=Number(value);
    return Number.isFinite(number)?number:null;
  };
  const easternParts=(iso)=>{
    const date=new Date(iso);
    if(Number.isNaN(date.getTime()))return {label:String(iso||''),year:''};
    const formatter=new Intl.DateTimeFormat('en-US',{
      timeZone:'America/New_York',month:'short',day:'numeric',year:'numeric',
      hour:'numeric',minute:'2-digit',timeZoneName:'short'
    });
    return {label:formatter.format(date),year:new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric'}).format(date)};
  };
  const normalize=(rows)=>{
    if(!Array.isArray(rows))throw new Error('feed response is not an array');
    const seen=new Set();
    const posts=[];
    rows.forEach((row)=>{
      if(!row||typeof row!=='object')return;
      const id=String(row.id||'').trim();
      const createdAt=String(row.created_at||'').trim();
      const timestamp=Date.parse(createdAt);
      const url=safePostUrl(row.url);
      if(!id||seen.has(id)||!Number.isFinite(timestamp)||!url)return;
      seen.add(id);
      const time=easternParts(createdAt);
      posts.push({
        id,createdAt,timestamp,url,year:time.year,dateLabel:time.label,
        text:stripMarkup(row.content),media:Array.isArray(row.media)?row.media.map(safeMediaUrl).filter(Boolean):[],
        replies:countValue(row.replies_count),
        reblogs:countValue(row.reblogs_count),
        favourites:countValue(row.favourites_count)
      });
    });
    posts.sort((a,b)=>b.timestamp-a.timestamp);
    if(!posts.length)throw new Error('feed contains no valid posts');
    return posts;
  };
  const mergePosts=(...groups)=>{
    const seen=new Set();
    const merged=[];
    groups.forEach((posts)=>posts.forEach((post)=>{
      if(seen.has(post.id))return;
      seen.add(post.id);merged.push(post);
    }));
    return merged.sort((a,b)=>b.timestamp-a.timestamp);
  };
  const fetchJson=async(url,timeoutMs)=>{
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),timeoutMs);
    try{
      const response=await fetch(url,{mode:'cors',cache:'no-store',signal:controller.signal});
      if(!response.ok)throw new Error('HTTP '+response.status);
      return await response.json();
    }finally{clearTimeout(timer);}
  };
  const setStatus=(message,isError)=>{
    const node=byId('tsStatus');
    if(!node)return;
    node.textContent=message;
    node.classList.toggle('truth-feed-error',Boolean(isError));
  };
  const setLoading=(loading)=>{
    state.loading=loading;
    const button=byId('tsRefresh');
    if(button){button.disabled=loading;button.textContent=loading?'Refreshing…':'Refresh live feed';}
  };
  const updateSummary=()=>{
    const latest=state.posts[0];
    const mode=byId('tsMode');
    const newest=byId('tsNewest');
    const checked=byId('tsChecked');
    const original=byId('tsNewestLink');
    if(mode)mode.textContent=state.mode;
    if(newest)newest.textContent=latest?latest.dateLabel:'Unavailable';
    if(checked)checked.textContent=state.checked;
    if(original){
      original.hidden=!latest;
      if(latest)original.href=latest.url;
    }
  };
  const filtered=()=>{
    const terms=state.query.toLowerCase().split(/\s+/).filter(Boolean);
    return state.posts.filter((post)=>{
      if(state.year!=='all'&&post.year!==state.year)return false;
      if(!terms.length)return true;
      const haystack=post.text.toLowerCase();
      return terms.every((term)=>haystack.includes(term));
    });
  };
  const renderYears=()=>{
    const box=byId('tsYears');
    if(!box)return;
    box.replaceChildren();
    const years=[...new Set(state.posts.map((post)=>post.year).filter(Boolean))].sort((a,b)=>b.localeCompare(a));
    ['all',...years].forEach((year)=>{
      const button=document.createElement('button');
      button.type='button';
      button.className='truth-feed-year'+(state.year===year?' on':'');
      button.textContent=year==='all'?'All years':year;
      button.setAttribute('aria-pressed',String(state.year===year));
      button.addEventListener('click',()=>{state.year=year;state.shown=PAGE_SIZE;renderYears();renderPosts();});
      box.appendChild(button);
    });
  };
  const addMedia=(container,post)=>{
    if(!post.media.length)return;
    const wrap=document.createElement('div');
    wrap.className='truth-post__media';
    post.media.forEach((url)=>{
      const extension=(new URL(url).pathname.split('.').pop()||'').toLowerCase();
      if(['jpg','jpeg','png','gif','webp','bmp'].includes(extension)){
        const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener';
        const image=document.createElement('img');image.src=url;image.loading='lazy';image.alt='Media attached to this Truth Social post';image.referrerPolicy='no-referrer';
        image.addEventListener('error',()=>{link.textContent='Open image';});
        link.appendChild(image);wrap.appendChild(link);return;
      }
      if(['mp4','webm','m4v'].includes(extension)){
        const video=document.createElement('video');video.src=url;video.controls=true;video.preload='metadata';video.referrerPolicy='no-referrer';wrap.appendChild(video);return;
      }
      const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener';link.textContent='Open attached media';wrap.appendChild(link);
    });
    container.appendChild(wrap);
  };
  const postCard=(post)=>{
    const card=document.createElement('article');card.className='truth-post';card.id='truth-'+post.id;
    const head=document.createElement('div');head.className='truth-post__head';
    const date=document.createElement('div');date.className='truth-post__date';date.textContent=post.dateLabel;
    const kind=document.createElement('span');kind.className='truth-post__kind';kind.textContent=/^RT(?::|\s|@)/i.test(post.text)?'Retruth':'Post';
    head.append(date,kind);card.appendChild(head);
    const text=document.createElement('div');text.className='truth-post__text'+(post.text?'':' is-media-only');text.textContent=post.text||'[Media-only post]';card.appendChild(text);
    addMedia(card,post);
    const meta=document.createElement('div');meta.className='truth-post__meta';
    if(post.favourites!==null){const engagement=document.createElement('span');engagement.textContent='♥ '+post.favourites.toLocaleString()+' · ↻ '+(post.reblogs||0).toLocaleString()+' · Replies '+(post.replies||0).toLocaleString();meta.appendChild(engagement);}
    const link=document.createElement('a');link.href=post.url;link.target='_blank';link.rel='noopener';link.textContent='View original ↗';meta.appendChild(link);card.appendChild(meta);
    return card;
  };
  const renderPosts=()=>{
    const box=byId('tsList');
    const count=byId('tsCountLine');
    if(!box)return;
    const matches=filtered();
    if(count)count.innerHTML='<strong>'+matches.length.toLocaleString()+'</strong> post'+(matches.length===1?'':'s')+((state.query||state.year!=='all')?' match':'')+' · newest first';
    box.replaceChildren();
    if(!matches.length){const empty=document.createElement('p');empty.className='truth-feed-empty';empty.textContent='No posts match the current search and year filter.';box.appendChild(empty);return;}
    let currentYear='';
    matches.slice(0,state.shown).forEach((post)=>{
      if(post.year!==currentYear){currentYear=post.year;const heading=document.createElement('h3');heading.className='truth-feed-year-heading';heading.textContent=currentYear;box.appendChild(heading);}
      box.appendChild(postCard(post));
    });
    if(matches.length>state.shown){
      const more=document.createElement('button');more.type='button';more.className='truth-feed-more';more.textContent='Load more ('+(matches.length-state.shown).toLocaleString()+' remaining)';
      more.addEventListener('click',()=>{state.shown+=PAGE_SIZE;renderPosts();});box.appendChild(more);
    }
  };
  const applyPosts=(posts,mode,status,checked)=>{
    state.posts=posts;state.mode=mode;state.shown=PAGE_SIZE;
    if(checked)state.checked=checked;
    renderYears();renderPosts();updateSummary();setStatus(status,false);
  };
  const loadFallback=async()=>{
    const [rows,metadata]=await Promise.all([
      fetchJson(FALLBACK_URL,12000),
      fetchJson(FALLBACK_META_URL,12000).catch(()=>null)
    ]);
    const posts=normalize(rows);
    const checked=metadata&&typeof metadata.checked_at_eastern==='string'?metadata.checked_at_eastern:'Check time unavailable';
    applyPosts(posts,'Local fallback','Showing '+posts.length.toLocaleString()+' recent posts while the full live archive loads. Snapshot checked '+checked+'.',checked);
    return posts;
  };
  const loadLive=async()=>{
    const rows=await fetchJson(LIVE_URL,45000);
    const livePosts=normalize(rows);
    const posts=mergePosts(livePosts,state.posts);
    const preservedNewer=posts[0].timestamp>livePosts[0].timestamp;
    const mode=preservedNewer?'Live mirror + newer fallback':'Live public mirror';
    const note=preservedNewer?' A newer locally verified post was preserved.':'';
    const checked=easternParts(new Date().toISOString()).label;
    applyPosts(posts,mode,'Loaded '+posts.length.toLocaleString()+' archived posts. The newest available post is '+posts[0].dateLabel+'.'+note,checked);
    return posts;
  };
  const refresh=async()=>{
    if(state.loading)return;
    setLoading(true);setStatus('Refreshing the full public archive…',false);
    try{await loadLive();}
    catch(error){
      if(!state.posts.length){
        try{await loadFallback();setStatus('Live mirror unavailable. Showing the verified local fallback through '+state.posts[0].dateLabel+'.',false);}
        catch(_fallbackError){setStatus('The live mirror and local fallback could not be loaded.',true);}
      }else{setStatus('Live refresh failed. Keeping the '+state.mode.toLowerCase()+' through '+state.posts[0].dateLabel+'.',true);}
    }finally{setLoading(false);}
  };
  const open=()=>{
    if(state.opened)return;
    state.opened=true;
    const input=byId('tsSearch');
    if(input)input.addEventListener('input',(event)=>{state.query=event.target.value||'';state.shown=PAGE_SIZE;renderPosts();});
    const button=byId('tsRefresh');if(button)button.addEventListener('click',refresh);
    setLoading(true);setStatus('Loading the verified fallback and the full live archive…',false);
    loadFallback().catch(()=>null).finally(()=>{
      loadLive().catch(()=>{
        if(state.posts.length)setStatus('Live mirror unavailable. Showing the verified local fallback through '+state.posts[0].dateLabel+'.',false);
        else setStatus('The live mirror and local fallback could not be loaded.',true);
      }).finally(()=>setLoading(false));
    });
  };

  window.TruthFeed={open,refresh};
})();
