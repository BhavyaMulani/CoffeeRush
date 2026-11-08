'use strict';
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Number(n||0).toLocaleString('en-CA');
const FIELDS=['base','temp','milk','syrup','topping'];
const LABELS={base:'Coffee base',temp:'Temperature',milk:'Milk',syrup:'Syrup',topping:'Topping'};
let state={config:null,member:null,round:null,period:'weekly',authMode:'register',nextAction:null,page:'home',busy:false,
  prefs:loadPrefs()};
let ticking=null;
function loadPrefs(){try{let x=JSON.parse(localStorage.getItem('coffee-rush-design-v2'));return {theme:['plum','mint','amber'].includes(x.theme)?x.theme:'plum',seconds:[25,30,45,60].includes(Number(x.seconds))?Number(x.seconds):45,stories:x.stories&&typeof x.stories==='object'?x.stories:{}};}catch{return{theme:'plum',seconds:45,stories:{}}}}
function savePrefs(){localStorage.setItem('coffee-rush-design-v2',JSON.stringify(state.prefs));}
function toast(message){const el=$('toast');el.textContent=message;el.classList.remove('hidden');clearTimeout(toast.id);toast.id=setTimeout(()=>el.classList.add('hidden'),4500);}
async function api(path,data){const opts={credentials:'same-origin',headers:{'Accept':'application/json'}};
 if(data!==undefined){opts.method='POST';opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(data);}
 let response;try{response=await fetch(path,opts);}catch{throw Error('Cannot connect to the café server. Check that it is running.');}
 const body=await response.json().catch(()=>({error:'Unexpected server response.'}));if(!response.ok)throw Error(body.error||'Request failed.');return body;}
function setMember(member){state.member=member; $('profile-label').textContent=member?member.name:'Join the club';}
function changePage(page){clearTimer();state.page=page;document.querySelectorAll('.page').forEach(el=>el.classList.toggle('shown',el.id==='page-'+page));document.querySelectorAll('[data-nav]').forEach(el=>el.classList.toggle('active',el.dataset.nav===page));window.scrollTo(0,0);
 if(page==='rankings')loadLeaderboard();if(page==='rewards')loadRewards();if(page==='studio')renderStudio();}
function gate(callback){if(state.member){callback();return;}state.nextAction=callback;openAuth();}
function openAuth(){state.authMode=state.member?'login':'register';$('auth-modal').classList.remove('hidden');$('auth-error').textContent='';$('nickname').value=state.member?.name||'';$('password').value='';$('logout').classList.toggle('hidden',!state.member);switchAuth(state.authMode);$('nickname').focus();}
function closeAuth(){$('auth-modal').classList.add('hidden');state.nextAction=null;}
function switchAuth(mode){state.authMode=mode;$('auth-title').textContent=mode==='register'?'Join the member club.':'Welcome back, brewer.';$('auth-submit').textContent=mode==='register'?'Create my account →':'Sign in →';document.querySelectorAll('[data-auth]').forEach(x=>x.classList.toggle('selected',x.dataset.auth===mode));$('auth-error').textContent='';}
async function handleAuth(e){e.preventDefault();const name=$('nickname').value.trim(),password=$('password').value;
 $('auth-error').textContent='';const button=$('auth-submit');button.disabled=true;
 try{const result=await api('/api/auth/'+state.authMode,{name,password});setMember(result.member);const callback=state.nextAction;$('auth-modal').classList.add('hidden');state.nextAction=null;toast('Welcome to The Unwritten Café, '+result.member.name+'!');if(callback)callback();else renderHome();}
 catch(err){$('auth-error').textContent=err.message;}finally{button.disabled=false;}}
async function logout(){try{await api('/api/auth/logout',{});setMember(null);state.round=null;closeAuth();changePage('home');toast('Signed out of this device.');}catch(err){toast(err.message)}}
const PORTRAITS={kaien:'/images/kaien.jpg',rumi:'/images/rumi.jpg',renji:'/images/renji.jpg',sora:'/images/sora.jpg',mika:'/images/mika.jpg',yori:'/images/yori.jpg'};
function portrait(char){return `<img class="portrait-img" src="${PORTRAITS[char.id]||''}" alt="${esc(char.name)}, ${esc(char.alias)}" draggable="false" decoding="async">`;}

function renderHome(){if(!state.config)return;const chars=state.config.characters;$('hero-art').innerHTML=portrait(chars[0]);$('character-grid').innerHTML=chars.map(c=>`<article class="character-card"><div class="character-art">${portrait(c)}</div><div><b>${esc(c.name)}</b><small>${esc(c.alias)}</small><p>${esc(c.drink)}</p></div></article>`).join('');}
async function startRound(mode='ranked'){
 if(state.busy)return;
 gate(async()=>{state.busy=true;try{const r=await api('/api/round/start',{mode,seconds:state.prefs.seconds});state.round={...r,index:0,score:0,perfect:0,phase:'story',line:0,picks:{},feedback:null};changePage('game');renderGame();}
 catch(err){toast(err.message);}finally{state.busy=false;}});
}
function currentGuest(){return state.round?.guests[state.round.index];}
function renderGame(){const r=state.round;if(!r)return;$('game-mode').textContent=r.ranked?'✦ RANKED · THE MIDNIGHT SHIFT':'✦ PRACTICE · DESIGN MODE';$('order-counter').textContent=(r.index+1)+' / 5';$('score-counter').textContent=fmt(r.score);$('progress').innerHTML=r.guests.map((_,i)=>`<i class="${i<r.index?'past':i===r.index?'now':''}"></i>`).join('');
 if(r.phase==='story')renderStory();if(r.phase==='brew')renderBrew();if(r.phase==='feedback')renderFeedback();}
function renderStory(){const r=state.round,c=currentGuest();const line=r.line===0?(state.prefs.stories[c.id]||c.story[0]):c.story[1];
 $('game-stage').innerHTML=`<div class="story-layout"><div class="story-visual">${portrait(c)}<span class="character-tag">✦ ${esc(c.alias)}</span></div><div class="story-copy"><span class="eyebrow">CHAPTER ${String(r.index+1).padStart(2,'0')} / AN UNWRITTEN ENCOUNTER</span><h3>${esc(c.name)} arrives.</h3><span class="alias">${esc(c.alias)}</span><div class="speech">“${esc(line)}”</div><button class="btn main" id="next-dialogue">${r.line===0?'Continue the story →':'Start brewing ☕'}</button><p class="tiny">Story time is untimed. Your coffee countdown begins when you select Start brewing.</p></div></div>`;}
async function nextDialogue(){const r=state.round;if(!r||r.phase!=='story'||state.busy)return;
 if(r.line===0){r.line=1;renderStory();return;}
 state.busy=true;try{const ready=await api('/api/round/ready',{roundId:r.roundId});r.phase='brew';r.duration=ready.duration;r.remaining=ready.duration;r.endTime=Date.now()+ready.duration*1000;r.picks={};renderGame();beginTimer();}
 catch(err){toast(err.message);}finally{state.busy=false;}}
function beginTimer(){clearTimer();ticking=setInterval(()=>{const r=state.round;if(!r||r.phase!=='brew'){clearTimer();return;}r.remaining=Math.max(0,(r.endTime-Date.now())/1000);const text=$('time-left'),fill=$('time-bar-fill'),header=$('timer-header');if(text)text.textContent=Math.ceil(r.remaining)+'s';if(fill){fill.style.width=(r.remaining/r.duration*100)+'%';fill.classList.toggle('urgent',r.remaining<=7);}if(header)header.classList.toggle('urgent',r.remaining<=7);if(r.remaining<=0){clearTimer();serve(true);}},100);}
function clearTimer(){if(ticking!==null){clearInterval(ticking);ticking=null;}}
function renderBrew(){const r=state.round,c=currentGuest(),picks=r.picks;const ingredients=state.config.ingredients;
 const ticket=FIELDS.map(f=>`<div class="ticket-line"><span>${esc(LABELS[f])}</span><b>${esc(c.recipe[f])}</b></div>`).join('');
 const groups=FIELDS.map((f,i)=>`<div class="ingredient-group"><strong>${String(i+1).padStart(2,'0')} / ${esc(LABELS[f])}</strong><div class="options">${ingredients[f].map(o=>`<button class="option ${picks[f]===o?'chosen':''}" data-field="${f}" data-choice="${esc(o)}" aria-pressed="${picks[f]===o}">${esc(o)}</button>`).join('')}</div></div>`).join('');
 const selected=FIELDS.filter(f=>picks[f]).length;
 $('game-stage').innerHTML=`<div class="brew-layout"><aside class="order-visual"><div class="ticket"><div class="ticket-kicker">THE UNWRITTEN CAFÉ<br>OFFICIAL ORDER TICKET · #${r.index+1}</div><h3>${esc(c.drink)}</h3><small>For ${esc(c.name)} · ${esc(c.alias)}</small><div style="margin-top:14px">${ticket}</div><div class="ticket-foot">✦ WHERE THE STORIES BREW ✦</div></div><div class="small-guest">${portrait(c)}<p>${esc(c.name)} is waiting for their perfect drink!</p></div></aside><div class="brew-content"><div class="timer-header" id="timer-header"><span>⏱ BREW BEFORE TIME RUNS OUT</span><b id="time-left">${Math.ceil(r.remaining)}s</b></div><div class="timer-bar"><div class="timer-fill" id="time-bar-fill" style="width:${r.remaining/r.duration*100}%"></div></div><h3>Build the perfect cup.</h3><p class="brew-sub">Match all five parts of the customer’s order.</p>${groups}<div class="brew-bottom"><p>${selected}/5 selected · ${selected===5?'Ready to serve!':'Choose all ingredients'}</p><div class="actions" style="margin:0"><button id="reset-cup" class="btn outline small">Reset cup</button><button id="serve-cup" class="btn main small" ${selected<5?'disabled':''}>Serve drink →</button></div></div></div></div>`;}
function choose(field,option){const r=state.round;if(!r||r.phase!=='brew'||!state.config.ingredients[field]?.includes(option))return;r.picks[field]=option;renderBrew();}
async function serve(expired=false){const r=state.round;if(!r||r.phase!=='brew'||state.busy)return;
 if(!expired&&!FIELDS.every(f=>r.picks[f]))return;
 state.busy=true;clearTimer();$('serve-cup')?.setAttribute('disabled','true');
 try{let picks={...r.picks};if(expired){for(const f of FIELDS)if(!picks[f])picks[f]=state.config.ingredients[f][0];}
 const feedback=await api('/api/round/serve',{roundId:r.roundId,picks});r.score=feedback.score;r.perfect=feedback.perfect;r.feedback=feedback;r.phase='feedback';renderGame();}
 catch(err){toast(err.message);if(r.phase==='brew'){r.remaining=Math.max(0,(r.endTime-Date.now())/1000);if(r.remaining>0)beginTimer();else setTimeout(()=>serve(true),800);}}
 finally{state.busy=false;}}
function renderFeedback(){const r=state.round,c=currentGuest(),f=r.feedback;
 const details=FIELDS.map(field=>`<div class="feedback-check"><span>${esc(LABELS[field])}</span><span class="${!f.expired&&r.picks[field]===c.recipe[field]?'correct':'incorrect'}">${!f.expired&&r.picks[field]===c.recipe[field]?'✓':'✕'} ${esc(c.recipe[field])}</span></div>`).join('');
 $('game-stage').innerHTML=`<div class="feedback-layout"><div class="feedback-primary"><div class="feedback-icon">${f.exact?'🌟':f.expired?'⌛':'☕'}</div><h3>${f.exact?'Perfectly brewed!':f.expired?'Time is up!':'Almost there!'}</h3><p>${f.exact?'A perfect order, ready to enjoy.':f.expired?'The customer waited too long. Next order is a new chance.':`You matched ${f.correctCount} out of five ingredients.`}</p><div class="points-gain">+${fmt(f.gain)} pts</div><p>Speed +${f.speed} · Combo +${f.combo} · Total ${fmt(f.score)}</p><div class="farewell">“${esc(c.farewell)}”<br><small>— ${esc(c.name)}</small></div><button id="next-guest" class="btn main">${r.index===4?'See my results →':'Next customer →'}</button></div><div class="feedback-secondary"><h4>Order review · ${esc(c.drink)}</h4>${details}<p class="tiny">Green check = matched ingredient. Red cross = needed ingredient.</p></div></div>`;}
async function advance(){const r=state.round;if(!r||r.phase!=='feedback'||state.busy)return;state.busy=true;
 try{const reply=await api('/api/round/advance',{roundId:r.roundId});if(reply.done){setMember(reply.member);state.round=null;renderResults(reply);changePage('results');}
 else{r.index=reply.index;r.line=0;r.picks={};r.phase='story';r.feedback=null;renderGame();window.scrollTo(0,0);}}
 catch(err){toast(err.message);}finally{state.busy=false;}}
function renderResults(result){$('results').innerHTML=`<div class="result-card"><div class="result-symbol">🏆</div><span class="eyebrow">THE MIDNIGHT SHIFT IS COMPLETE</span><h2>Your chapter is written.</h2><p>Five customers. Five orders. A story worth sharing.</p><div class="result-stats"><div><b>${fmt(result.score)}</b><small>Total score</small></div><div><b>${result.perfect} / 5</b><small>Perfect orders</small></div><div><b>${result.ranked?(result.rank?'#'+result.rank:'—'):'—'}</b><small>Weekly rank</small></div></div><div class="result-reward"><b>${result.ranked?'✦ +'+result.earned+' café reward points':'✦ Practice round completed'}</b><p>${result.ranked?`Potential ${result.planned} points this round · daily limit 30. Balance: ${fmt(result.member.points)} points.`:'Practice rounds are unranked and do not earn redeemable demo points.'}</p></div><div class="actions" style="justify-content:center"><button id="play-again" class="btn main">▶ Play again</button><button class="btn outline" data-nav="rankings">View leaderboard</button><button class="btn outline" data-nav="rewards">My rewards</button></div></div>`;}
async function loadLeaderboard(){if(state.page!=='rankings')return;
 $('leader-list').innerHTML='<div class="empty">Loading the café community…</div>';
 try{const data=await api('/api/leaderboard?period='+state.period);if(state.page!=='rankings')return;const entries=data.entries;$('ranking-count').textContent=entries.length+' members ranked';
 $('leader-list').innerHTML=entries.length?entries.map((x,i)=>`<div class="leader-row ${state.member?.id===x.id?'you':''}"><span class="rank-icon">${['🥇','🥈','🥉'][i]||'#'+(i+1)}</span><span class="player-title">${esc(x.name)}${x.id===state.member?.id?' (you)':''}<small>${x.plays} ranked ${x.plays===1?'round':'rounds'}</small></span><span class="leader-score">${fmt(x.score)}</span></div>`).join(''):'<div class="empty">No scores yet. Finish the first ranked round to become the café’s first champion!</div>';
 }catch(err){$('leader-list').innerHTML=`<div class="empty">${esc(err.message)}</div>`;}}
async function loadRewards(){if(state.page!=='rewards')return;
 try{if(state.member){const updated=await api('/api/me');setMember(updated.member);}renderRewards();}catch(err){toast(err.message);renderRewards();}}
function renderRewards(){const m=state.member;$('balance').textContent=fmt(m?.points||0);
 $('reward-cards').innerHTML=state.config.rewards.map(r=>`<div class="reward-card"><div class="emoji">${r.icon}</div><h4>${esc(r.name)}</h4><p>${esc(r.description)}</p><strong>✦ ${r.cost} pts</strong><button class="btn ${m&&m.points>=r.cost?'main':'outline'} small" data-reward="${r.id}">${!m?'Join to claim':m.points>=r.cost?'Redeem sample reward':'Need more points'}</button></div>`).join('');
 $('badges').innerHTML=state.config.badges.map(b=>`<span class="badge ${m?.badges.includes(b.id)?'':'locked'}">${b.icon} ${esc(b.name)} ${m?.badges.includes(b.id)?'✓':'· locked'}</span>`).join('');
 $('vouchers').innerHTML=m?.vouchers.length?m.vouchers.map(v=>`<div class="voucher"><div><b>${esc(v.reward_name)}</b><br><code>${esc(v.id)}</code></div><span class="${v.used?'muted':'correct'}">${v.used?'Used (demo)':'Unused (demo)'}</span></div>`).join(''):'<p class="muted">No vouchers yet. Play a ranked round to earn points.</p>';}
async function redeem(rewardId){gate(async()=>{const r=state.config.rewards.find(x=>x.id===rewardId);if(!r)return;if(state.member.points<r.cost){toast(`You need ${r.cost-state.member.points} more points for ${r.name}.`);return;}if(!confirm(`Redeem ${r.cost} demonstration points for ${r.name}? Sample vouchers are not real discounts.`))return;
 try{const result=await api('/api/rewards/redeem',{rewardId});setMember(result.member);renderRewards();toast('Demo voucher created: '+result.voucherCode);}catch(err){toast(err.message);}});}
function renderStudio(){document.body.dataset.theme=state.prefs.theme;document.querySelectorAll('[data-theme-choice]').forEach(x=>x.classList.toggle('current',x.dataset.themeChoice===state.prefs.theme));$('studio-timer').value=state.prefs.seconds;$('studio-character').innerHTML=state.config.characters.map(c=>`<option value="${c.id}">${esc(c.name)} · ${esc(c.alias)}</option>`).join('');refreshDialogue();}
function refreshDialogue(){const c=state.config.characters.find(x=>x.id===$('studio-character').value)||state.config.characters[0];$('studio-dialogue').value=state.prefs.stories[c.id]||c.story[0];$('studio-saved').textContent='';}
function saveDialogue(){const id=$('studio-character').value,value=$('studio-dialogue').value.trim();if(!value){toast('Please add some dialogue.');return;}state.prefs.stories[id]=value.slice(0,180);savePrefs();$('studio-saved').textContent='Saved!';toast('Dialogue saved. Try a practice round to hear the new line.');}
async function validateStaff(e){e.preventDefault();const output=$('staff-output');output.textContent='Checking…';try{const r=await api('/api/staff/redeem',{code:$('staff-code').value,pin:$('staff-pin').value});output.textContent='Demo voucher '+r.code+' marked used: '+r.reward+'.';$('staff-pin').value='';await loadRewards();}catch(err){output.textContent=err.message;}}
function clickHandler(event){const nav=event.target.closest('[data-nav]');if(nav){if(state.round&&state.page==='game'&&!confirm('Leave this round? Your unfinished score will not count.'))return;state.round=null;changePage(nav.dataset.nav);return;}
 const choice=event.target.closest('[data-field][data-choice]');if(choice){choose(choice.dataset.field,choice.dataset.choice);return;}
 const period=event.target.closest('[data-period]');if(period){state.period=period.dataset.period;document.querySelectorAll('[data-period]').forEach(x=>x.classList.toggle('selected',x===period));loadLeaderboard();return;}
 const reward=event.target.closest('[data-reward]');if(reward){redeem(reward.dataset.reward);return;}
 const theme=event.target.closest('[data-theme-choice]');if(theme){state.prefs.theme=theme.dataset.themeChoice;savePrefs();document.body.dataset.theme=state.prefs.theme;document.querySelectorAll('[data-theme-choice]').forEach(x=>x.classList.toggle('current',x===theme));toast('Café palette updated!');return;}
 if(event.target.closest('#next-dialogue')){nextDialogue();return;}
 if(event.target.closest('#serve-cup')){serve(false);return;}
 if(event.target.closest('#reset-cup')){if(state.round?.phase==='brew'){state.round.picks={};renderBrew();}return;}
 if(event.target.closest('#next-guest')){advance();return;}
 if(event.target.closest('#play-again')){startRound('ranked');return;}
}
async function bootstrap(){try{state.config=await api('/api/config');const me=await api('/api/me');setMember(me.member);document.body.dataset.theme=state.prefs.theme;renderHome();}
 catch(err){$('page-home').innerHTML=`<div class="empty"><h2>Unable to connect to the game server.</h2><p>${esc(err.message)}</p><p>Open this game through the Python server, not as a local file.</p></div>`;}}

document.addEventListener('click',clickHandler);
$('logo').addEventListener('click',()=>{state.round=null;changePage('home');});
$('profile').addEventListener('click',openAuth);
$('close-modal').addEventListener('click',closeAuth);
$('auth-modal').addEventListener('click',e=>{if(e.target===$('auth-modal'))closeAuth();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('auth-modal').classList.contains('hidden'))closeAuth();});
document.querySelectorAll('[data-auth]').forEach(x=>x.addEventListener('click',()=>switchAuth(x.dataset.auth)));
$('auth-form').addEventListener('submit',handleAuth);
$('logout').addEventListener('click',logout);
$('start-ranked').addEventListener('click',()=>startRound('ranked'));
$('start-practice').addEventListener('click',()=>startRound('practice'));
$('leader-start').addEventListener('click',()=>startRound('ranked'));
$('quit-game').addEventListener('click',()=>{if(confirm('Leave this round? Your unfinished score will not count.')){state.round=null;changePage('home');}});
$('staff-form').addEventListener('submit',validateStaff);
$('studio-character').addEventListener('change',refreshDialogue);
$('studio-timer').addEventListener('change',e=>{state.prefs.seconds=Number(e.target.value);savePrefs();toast('Practice timer updated!');});
$('save-dialogue').addEventListener('click',saveDialogue);
$('reset-dialogue').addEventListener('click',()=>{delete state.prefs.stories[$('studio-character').value];savePrefs();refreshDialogue();toast('Original story restored.');});
$('studio-test').addEventListener('click',()=>startRound('practice'));
bootstrap();
