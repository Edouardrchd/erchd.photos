(function(){
'use strict';

/* Pour un envoi direct du formulaire : créez un formulaire sur formspree.io
   et collez son adresse ici, par exemple 'https://formspree.io/f/xxxxxxx'. */
var ENDPOINT = '';

var root = document.documentElement;
var rm = matchMedia('(prefers-reduced-motion: reduce)').matches;
var $  = function(s,c){return (c||document).querySelector(s)};
var $$ = function(s,c){return [].slice.call((c||document).querySelectorAll(s))};

/* ======================= 0. MODE PROPRIETAIRE ======================= */
/* Le panneau « Réglages » n'est pas destine aux visiteurs : ils ne voient que
   le bouton clair/sombre. Pour l'afficher sur VOTRE navigateur, ouvrez une
   fois le site avec ?reglages a la fin de l'adresse :

       https://edouardvisuals.com/?reglages     ouvre l'acces
       https://edouardvisuals.com/?reglages=0   le referme

   Le choix est memorise dans ce navigateur, l'adresse est aussitot nettoyee.
   A savoir : cela masque le bouton, cela ne protege pas un secret. Quelqu'un
   qui lit le code source de la page peut retrouver ce parametre. C'est sans
   consequence, les reglages ne modifient que l'affichage local du visiteur. */
var ADMIN_KEY = 'er-portfolio-admin';
(function(){
  var m = /[?&]reglages(?:=([01]))?(?:&|$)/.exec(location.search);
  if(m){
    try{
      if(m[1] === '0') localStorage.removeItem(ADMIN_KEY);
      else localStorage.setItem(ADMIN_KEY,'1');
    }catch(e){}
    history.replaceState(null,'',location.pathname + location.hash);
  }
  var on = false;
  try{ on = localStorage.getItem(ADMIN_KEY) === '1' }catch(e){}
  root.classList.toggle('admin', on);
})();
function isAdmin(){ return root.classList.contains('admin') }

/* ======================= 1. RÉGLAGES ======================= */
var FONTS = {
  d:{
    instrument:{css:"'Instrument Serif',Georgia,serif", q:'Instrument+Serif:ital@0;1', adj:1},
    bodoni:    {css:"'Bodoni Moda',Georgia,serif",      q:'Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;1,6..96,400', adj:.94},
    fraunces:  {css:"'Fraunces',Georgia,serif",         q:'Fraunces:ital,opsz,wght@0,9..144,200;0,9..144,300;1,9..144,300', adj:.94},
    cormorant: {css:"'Cormorant Garamond',Georgia,serif",q:'Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400', adj:1.12},
    archivo:   {css:"'Archivo',Helvetica,sans-serif",   q:'Archivo:wght@300;400;500;600', adj:.82}
  },
  s:{
    archivo:{css:"'Archivo',Helvetica,Arial,sans-serif", q:'Archivo:wght@300;400;500;600'},
    jost:   {css:"'Jost',Helvetica,Arial,sans-serif",    q:'Jost:wght@200;300;400;500'},
    inter:  {css:"'Inter',Helvetica,Arial,sans-serif",   q:'Inter:wght@300;400;500'},
    dm:     {css:"'DM Sans',Helvetica,Arial,sans-serif", q:'DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500'}
  },
  m:{
    plex:     {css:"'IBM Plex Mono',ui-monospace,monospace", q:'IBM+Plex+Mono:wght@400;500'},
    space:    {css:"'Space Mono',ui-monospace,monospace",    q:'Space+Mono:wght@400;700'},
    jetbrains:{css:"'JetBrains Mono',ui-monospace,monospace",q:'JetBrains+Mono:wght@300;400;500'}
  }
};
var IMGMODE = {
  couleur:{sat:1,   sath:1},
  nbrepos:{sat:0,   sath:1},
  nb:     {sat:0,   sath:0}
};
/* réglages par défaut du site (le bouton « Réinitialiser » y revient) */
var DEF = {theme:'nuit',acc:'#C4472C',fd:'instrument',fs:'jost',fm:'plex',
  rad:28,gap:14,u:100,w:1440,cols:4,fsz:105,hsz:100,img:'couleur',
  grain:true,vig:true,cur:true,anim:true};
var S = {}, KEY = 'er-portfolio-reglages';

function loaded(q){ return !!document.querySelector('link[data-q="'+q+'"]') }
function loadFont(q){
  if(!q || loaded(q)) return;
  var l=document.createElement('link');
  l.rel='stylesheet'; l.dataset.q=q;
  l.href='https://fonts.googleapis.com/css2?family='+q+'&display=swap';
  document.head.appendChild(l);
}
function lum(hex){
  var c=hex.replace('#',''); if(c.length===3) c=c[0]+c[0]+c[1]+c[1]+c[2]+c[2];
  var n=parseInt(c,16);
  return (0.2126*((n>>16)&255) + 0.7152*((n>>8)&255) + 0.0722*(n&255))/255;
}
function apply(){
  var st=root.style;
  root.setAttribute('data-theme',S.theme);

  if(S.acc){ st.setProperty('--acc',S.acc); st.setProperty('--acc-ink', lum(S.acc)>.6?'#0A0B0C':'#F4F2EC'); }
  else{ st.removeProperty('--acc'); st.removeProperty('--acc-ink'); }

  var fd=FONTS.d[S.fd]||FONTS.d.instrument, fs=FONTS.s[S.fs]||FONTS.s.archivo, fm=FONTS.m[S.fm]||FONTS.m.plex;
  loadFont(fd.q); loadFont(fs.q); loadFont(fm.q);
  st.setProperty('--ff-d',fd.css); st.setProperty('--ff-s',fs.css); st.setProperty('--ff-m',fm.css);
  st.setProperty('--hs-adj',fd.adj);

  st.setProperty('--rad',S.rad+'px');
  st.setProperty('--gap',S.gap+'px');
  st.setProperty('--u',(S.u/100).toFixed(2));
  st.setProperty('--maxw',S.w+'px');
  st.setProperty('--cols',S.cols);
  st.setProperty('--fs',(S.fsz/100).toFixed(2));
  st.setProperty('--hs',(S.hsz/100).toFixed(2));

  var im=IMGMODE[S.img]||IMGMODE.couleur;
  st.setProperty('--sat',im.sat); st.setProperty('--sat-h',im.sath);

  st.setProperty('--grain',S.grain?'.4':'0');
  st.setProperty('--vig',S.vig?'1':'0');
  root.classList.toggle('cur-on', !!S.cur && !rm);
  root.classList.toggle('noanim', !S.anim);

  var mt=document.querySelector('meta[name=theme-color]');
  if(mt) mt.setAttribute('content', S.theme==='tirage'?'#EFECE4':(S.theme==='encre'?'#000000':'#0A0B0C'));

  var mb=document.getElementById('modebtn');
  if(mb){
    var clair = S.theme==='tirage';
    mb.setAttribute('title', clair?'Passer en affichage sombre':'Passer en affichage clair');
    mb.setAttribute('aria-label', mb.getAttribute('title'));
  }

  sync(); layout();
  try{ localStorage.setItem(KEY, JSON.stringify(S)) }catch(e){}
}
function sync(){
  $$('.seg').forEach(function(g){
    var k=g.dataset.set, v=String(S[k==='cols'?'cols':k]);
    $$('button',g).forEach(function(b){ b.classList.toggle('on', b.dataset.v===v) });
  });
  $$('#swatches .sw').forEach(function(b){
    if(b.dataset.v!==undefined) b.classList.toggle('on', b.dataset.v===S.acc);
  });
  $('#swcustom').classList.toggle('on', !!S.acc && !$$('#swatches button.sw.on').length);
  var set=function(id,out,val,suf){ var el=$(id); if(el){el.value=val;} var o=$(out); if(o){o.textContent=val+suf;} };
  set('#r-rad','#o-rad',S.rad,' px');
  set('#r-gap','#o-gap',S.gap,' px');
  set('#r-u','#o-u',S.u,' %');
  set('#r-w','#o-w',S.w,' px');
  set('#r-fs','#o-fs',S.fsz,' %');
  set('#r-hs','#o-hs',S.hsz,' %');
  [['#t-grain','grain'],['#t-vig','vig'],['#t-cur','cur'],['#t-anim','anim']].forEach(function(p){
    var el=$(p[0]); el.classList.toggle('on',!!S[p[1]]); el.setAttribute('aria-checked',!!S[p[1]]);
  });
}
function load(){
  S={}; for(var k in DEF) S[k]=DEF[k];
  try{
    var j=JSON.parse(localStorage.getItem(KEY)||'{}');
    for(var p in j) if(p in S) S[p]=j[p];
  }catch(e){}
}
load(); apply();

/* — panneau — */
var tw=$('#tw'), scrim=$('#scrim'), twbtn=$('#twbtn');

/* Bascule clair / sombre, seule commande d'affichage offerte aux visiteurs.
   Elle reutilise le reglage « Ambiance » du panneau : les deux restent donc
   toujours d'accord, et le choix du visiteur est memorise dans son navigateur. */
$('#modebtn').addEventListener('click',function(){
  S.theme = (S.theme==='tirage') ? 'nuit' : 'tirage';
  apply();
});

function panel(o){
  if(o && !isAdmin()) return;
  tw.classList.toggle('on',o); scrim.classList.toggle('on',o);
  tw.setAttribute('aria-hidden',!o); twbtn.setAttribute('aria-expanded',o);
  if(o) setTimeout(function(){ $('#twclose').focus() },160);
}
twbtn.addEventListener('click',function(){ panel(!tw.classList.contains('on')) });
$('#twclose').addEventListener('click',function(){ panel(false) });
scrim.addEventListener('click',function(){ panel(false) });
addEventListener('keydown',function(e){
  if(e.key==='Escape' && tw.classList.contains('on')){ panel(false); twbtn.focus(); return; }
  if((e.key==='r'||e.key==='R') && isAdmin()
     && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)
     && !document.getElementById('lb').classList.contains('on')){
    panel(!tw.classList.contains('on'));
  }
});
$$('.seg').forEach(function(g){
  g.addEventListener('click',function(e){
    var b=e.target.closest('button'); if(!b) return;
    var k=g.dataset.set;
    S[k]= k==='cols' ? +b.dataset.v : b.dataset.v;
    apply();
  });
});
$$('#swatches .sw[data-v]').forEach(function(b){
  b.addEventListener('click',function(){ S.acc=b.dataset.v; apply() });
});
$('#acccustom').addEventListener('input',function(e){ S.acc=e.target.value; apply() });
[['#r-rad','rad'],['#r-gap','gap'],['#r-u','u'],['#r-w','w'],['#r-fs','fsz'],['#r-hs','hsz']]
.forEach(function(p){
  $(p[0]).addEventListener('input',function(e){ S[p[1]]=+e.target.value; apply() });
});
[['#t-grain','grain'],['#t-vig','vig'],['#t-cur','cur'],['#t-anim','anim']].forEach(function(p){
  $(p[0]).addEventListener('click',function(){ S[p[1]]=!S[p[1]]; apply() });
});
$('#twreset').addEventListener('click',function(){
  try{ localStorage.removeItem(KEY) }catch(e){}
  load(); apply();
});
$('#twcopy').addEventListener('click',function(){
  var fd=FONTS.d[S.fd], fs=FONTS.s[S.fs], fm=FONTS.m[S.fm];
  var css=':root{\n'+
    '  --ff-d:'+fd.css+';\n  --ff-s:'+fs.css+';\n  --ff-m:'+fm.css+';\n'+
    '  --hs-adj:'+fd.adj+';\n  --fs:'+(S.fsz/100).toFixed(2)+';\n  --hs:'+(S.hsz/100).toFixed(2)+';\n'+
    '  --u:'+(S.u/100).toFixed(2)+';\n  --rad:'+S.rad+'px;\n  --gap:'+S.gap+'px;\n'+
    '  --cols:'+S.cols+';\n  --maxw:'+S.w+'px;\n'+
    '  --grain:'+(S.grain?'.4':'0')+';\n  --vig:'+(S.vig?'1':'0')+';\n'+
    '  --sat:'+IMGMODE[S.img].sat+';\n  --sat-h:'+IMGMODE[S.img].sath+';\n'+
    (S.acc?'  --acc:'+S.acc+';\n':'')+
    '}\n/* thème : data-theme="'+S.theme+'" sur la balise <html> */';
  var done=function(ok){
    var b=$('#twcopy'); b.textContent = ok?'CSS copié ✓':'Copie impossible';
    setTimeout(function(){ b.textContent='Copier le CSS' },1800);
  };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(css).then(function(){done(true)},function(){done(false)});
  } else done(false);
});

/* ======================= 2. OUVERTURE ======================= */
var boot=$('#boot'), bootc=$('#bootc');
function endBoot(){
  boot.classList.add('done');
  document.body.classList.add('go');
  setTimeout(function(){ boot.remove() },1200);
}
var seen=false; try{ seen=sessionStorage.getItem('er-boot')==='1' }catch(e){}
if(seen || rm){
  boot.style.display='none';
  /* on laisse peindre l'état de départ pour que la révélation joue quand même */
  requestAnimationFrame(function(){ document.body.classList.add('go') });
}
else{
  try{ sessionStorage.setItem('er-boot','1') }catch(e){}
  document.body.classList.add('lock');
  var n=0, t0=performance.now(), dur=1250;
  (function step(now){
    var p=Math.min(1,(now-t0)/dur), eased=1-Math.pow(1-p,2.4);
    n=Math.round(eased*100);
    bootc.textContent=('00'+n).slice(-3);
    boot.style.setProperty('--p',n+'%');
    if(p<1) requestAnimationFrame(step);
    else{ document.body.classList.remove('lock'); endBoot(); }
  })(t0);
}

/* ======================= 3. MOSAÏQUE ======================= */
var grids=$$('.mosaic'), ROW=6;
function layout(){
  if(!grids) return;                         /* apply() peut s'exécuter avant */
  var cs=getComputedStyle(root);
  var gap=parseFloat(cs.getPropertyValue('--gap'))||14;
  var wanted=parseInt(cs.getPropertyValue('--cols'),10)||3;
  grids.forEach(function(g){
    /* une série de 3 photos ne s'étale jamais sur 4 colonnes */
    g.style.setProperty('--cols-fit', Math.max(1, Math.min(wanted, $$('.frame',g).length)));
    var cols=getComputedStyle(g).gridTemplateColumns.split(' ').filter(Boolean).length;
    var colw=(g.clientWidth-gap*(cols-1))/cols;
    if(colw<=0) return;
    $$('.frame',g).forEach(function(f){
      var w=+f.dataset.w, h=+f.dataset.h; if(!w||!h) return;
      f.style.setProperty('--sp', Math.max(4, Math.round((colw*h/w+gap)/(ROW+gap))));
    });
  });
}
layout();
var rz; addEventListener('resize',function(){ clearTimeout(rz); rz=setTimeout(layout,120) });
addEventListener('load',layout);

/* ======================= 4. RÉVÉLATIONS ======================= */
var frames=$$('.frame');
if(rm || !('IntersectionObserver' in window)){ frames.forEach(function(f){ f.classList.add('in') }) }
else{
  var io=new IntersectionObserver(function(en){
    en.forEach(function(x){
      if(!x.isIntersecting) return;
      var sibs=$$('.frame',x.target.parentNode), d=sibs.indexOf(x.target)%3;
      x.target.style.transitionDelay=(d*0.08)+'s';
      x.target.classList.add('in'); io.unobserve(x.target);
    });
  },{threshold:.05,rootMargin:'0px 0px -4% 0px'});
  frames.forEach(function(f){ io.observe(f) });
}

/* ======================= 5. PLANCHE CONTACT ======================= */
var strip=$('#strip');
frames.forEach(function(f,k){
  var fig=document.createElement('figure');
  var im=document.createElement('img');
  im.decoding='async'; im.dataset.src=f.querySelector('img').src;
  im.alt=f.dataset.cap+' — '+f.dataset.cat;
  var cp=document.createElement('figcaption');
  cp.textContent=('0'+(k+1)).slice(-2);
  fig.appendChild(im); fig.appendChild(cp);
  fig.tabIndex=0; fig.setAttribute('role','button');
  fig.setAttribute('aria-label','Ouvrir : '+f.dataset.cap);
  fig.addEventListener('click',function(){ if(!moved) open(k) });
  fig.addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.key===' '){ e.preventDefault(); open(k) }
  });
  strip.appendChild(fig);
});
/* les vignettes ne sont décodées qu'à l'approche de la planche */
function fillStrip(){
  $$('img[data-src]',strip).forEach(function(im){ im.src=im.dataset.src; delete im.dataset.src });
}
if('IntersectionObserver' in window){
  var sio=new IntersectionObserver(function(en){
    if(en[0].isIntersecting){ fillStrip(); sio.disconnect() }
  },{rootMargin:'600px 0px'});
  sio.observe(strip);
} else fillStrip();

var down=false, sx0=0, sl0=0, moved=false;
strip.addEventListener('pointerdown',function(e){
  down=true; moved=false; sx0=e.clientX; sl0=strip.scrollLeft; strip.classList.add('drag');
});
strip.addEventListener('pointermove',function(e){
  if(!down) return;
  var dx=e.clientX-sx0;
  if(Math.abs(dx)>4) moved=true;
  strip.scrollLeft=sl0-dx;
});
['pointerup','pointerleave','pointercancel'].forEach(function(ev){
  strip.addEventListener(ev,function(){ down=false; strip.classList.remove('drag') });
});

/* ======================= 6. DÉFILEMENT ======================= */
var nav=$('#nav'), gauge=$('#gauge'), hm=$('#hm'), tick=false;
var ids=['hockey','basket','football','boxe','atelier','contact'];
var links=$$('[data-s]');
function onScroll(){
  var y=scrollY, d=document.documentElement, mx=d.scrollHeight-d.clientHeight;
  gauge.style.width=(mx>0? y/mx*100 : 0)+'%';
  nav.classList.toggle('stuck', y>60);
  if(hm && !rm && S.anim && y<innerHeight*1.3) hm.style.transform='translate3d(0,'+(y*.22)+'px,0)';
  var mid=y+innerHeight*.35, cur='';
  ids.forEach(function(id){
    var el=document.getElementById(id);
    if(el && el.offsetTop<=mid) cur=id;
  });
  links.forEach(function(a){ a.classList.toggle('act', a.dataset.s===cur) });
  tick=false;
}
addEventListener('scroll',function(){ if(!tick){ requestAnimationFrame(onScroll); tick=true } },{passive:true});
onScroll();

/* ======================= 7. MENU MOBILE ======================= */
var bg=$('#bg'), sheet=$('#sheet');
function setSheet(o){
  sheet.classList.toggle('on',o); bg.classList.toggle('on',o);
  document.body.classList.toggle('lock',o);
  bg.setAttribute('aria-expanded',o);
  bg.setAttribute('aria-label', o?'Fermer le menu':'Ouvrir le menu');
}
bg.addEventListener('click',function(){ setSheet(!sheet.classList.contains('on')) });
$$('a',sheet).forEach(function(a){ a.addEventListener('click',function(){ setSheet(false) }) });
addEventListener('keydown',function(e){
  if(e.key==='Escape' && sheet.classList.contains('on')) setSheet(false);
});

/* ======================= 8. VISIONNEUSE ======================= */
var lb=$('#lb'), lbi=$('#lbi'), lbc=$('#lbc'), lbd=$('#lbd'),
    lbs=$('#lbs'), lbn=$('#lbn'), lbstrip=$('#lbstrip'), idx=0, prevFocus=null;
frames.forEach(function(f,k){
  var t=document.createElement('img');
  t.src=f.querySelector('img').src; t.alt=''; t.loading='lazy';
  t.addEventListener('click',function(){ show(k) });
  lbstrip.appendChild(t);
  f.tabIndex=0; f.setAttribute('role','button');
  f.setAttribute('aria-label','Agrandir : '+f.dataset.cap);
  f.addEventListener('click',function(){ open(k) });
  f.addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.key===' '){ e.preventDefault(); open(k) }
  });
});
var thumbs=$$('img',lbstrip);
function show(k){
  idx=(k+frames.length)%frames.length;
  var f=frames[idx], im=f.querySelector('img');
  lbi.classList.remove('on');
  setTimeout(function(){
    lbi.src=im.src; lbi.alt=im.alt;
    lbc.textContent=f.dataset.cap;
    lbd.textContent=f.dataset.meta;
    lbs.textContent=f.dataset.cat;
    lbn.textContent=(idx+1)+' / '+frames.length;
    lbi.classList.add('on');
  }, rm?0:110);
  thumbs.forEach(function(t,i){ t.classList.toggle('sel', i===idx) });
  var sel=thumbs[idx];
  if(sel) lbstrip.scrollTo({left:sel.offsetLeft-lbstrip.clientWidth/2+sel.clientWidth/2, behavior:rm?'auto':'smooth'});
}
function open(k){
  prevFocus=document.activeElement;
  lb.classList.add('on');
  var reveal=function(){ lb.classList.add('vis') };
  requestAnimationFrame(reveal); setTimeout(reveal,60);   /* filet de sécurité */
  document.body.classList.add('lock');
  show(k); $('#lbx').focus();
}
function close(){
  lb.classList.remove('vis'); document.body.classList.remove('lock'); lbi.classList.remove('on');
  setTimeout(function(){ lb.classList.remove('on') },300);
  if(prevFocus) prevFocus.focus();
}
$('#lbx').addEventListener('click',close);
$('#lbp').addEventListener('click',function(){ show(idx-1) });
$('#lbnx').addEventListener('click',function(){ show(idx+1) });
$('.lb-m',lb).addEventListener('click',function(e){ if(e.target!==lbi) close() });
addEventListener('keydown',function(e){
  if(!lb.classList.contains('on')) return;
  if(e.key==='Escape') close();
  else if(e.key==='ArrowLeft') show(idx-1);
  else if(e.key==='ArrowRight') show(idx+1);
});
var tx=null;
lb.addEventListener('touchstart',function(e){ tx=e.changedTouches[0].clientX },{passive:true});
lb.addEventListener('touchend',function(e){
  if(tx===null) return;
  var dx=e.changedTouches[0].clientX-tx;
  if(Math.abs(dx)>52) show(dx<0? idx+1 : idx-1);
  tx=null;
},{passive:true});

/* ======================= 9. CURSEUR ======================= */
var cd=$('#cd'), cr=$('#cr'), mx=innerWidth/2, my=innerHeight/2, rx=mx, ry=my, raf=null;
function loop(){
  rx+=(mx-rx)*.16; ry+=(my-ry)*.16;
  cd.style.transform='translate3d('+mx+'px,'+my+'px,0)';
  cr.style.transform='translate3d('+rx+'px,'+ry+'px,0)';
  raf=requestAnimationFrame(loop);
}
addEventListener('pointermove',function(e){
  mx=e.clientX; my=e.clientY;
  if(!raf && root.classList.contains('cur-on')){ loop(); root.classList.add('cur-live'); }
  var over=e.target.closest('.frame, .strip figure, .chap, .lb-m');
  root.classList.toggle('cur-view', !!over);
},{passive:true});

/* ======================= 10. FORMULAIRE ======================= */
var fm=$('#fm'), ok=$('#ok');
fm.addEventListener('submit',function(e){
  e.preventDefault();
  if(!fm.checkValidity()){ fm.reportValidity(); return; }
  var d=new FormData(fm), get=function(k){ return (d.get(k)||'').toString().trim() };
  var btn=fm.querySelector('.send');
  if(ENDPOINT){
    btn.textContent='Envoi…';
    fetch(ENDPOINT,{method:'POST',body:d,headers:{Accept:'application/json'}})
      .then(function(r){
        if(!r.ok) throw 0;
        ok.textContent='Demande envoyée. Réponse sous 24 h.'; ok.classList.add('on');
        btn.textContent='Envoyé ✓'; fm.reset();
      })
      .catch(function(){
        ok.textContent="L'envoi a échoué. Écrivez directement à edouard.rchd@gmail.com.";
        ok.classList.add('on'); btn.textContent='Envoyer la demande';
      });
    return;
  }
  var body='Nom : '+get('nom')+'\nEmail : '+get('email')+'\nClub : '+get('structure')+
    '\nDiscipline : '+get('discipline')+'\nDate : '+get('date')+'\n\n'+get('message');
  location.href='mailto:edouard.rchd@gmail.com?subject='+
    encodeURIComponent('Demande de reportage — '+get('discipline'))+'&body='+encodeURIComponent(body);
  ok.textContent='Votre messagerie vient de s\'ouvrir avec la demande pré-remplie.';
  ok.classList.add('on');
});

})();
