import {api,getId,consultar,navegar,mostrarFoto,erroComRetry} from './api.js';
const form=document.querySelector('form');
const pagina=location.pathname.endsWith('/personagem.html')?'personagem':'resultado';
const titulo=document.querySelector('.info h1');
const img=form.querySelector('img');
const acertou=document.getElementById('acertou');
const errou=document.getElementById('errou');
const modal=document.getElementById('modalErro');
let estado=null, ocupado=true;
function bloquear(v){ocupado=v; if(pagina==='resultado') [acertou,errou].forEach(el=>{el.setAttribute('aria-disabled',String(v)); el.style.pointerEvents=v?'none':'';});}
function mostrar(data){
  estado=data;
  if(navegar(data,pagina))return;
  if(data.status==='sem_resultado'){
    titulo.textContent='Sem resultado'; const msg=modal.querySelector('.modalConteudo p');
    msg.textContent='Não consegui identificar com segurança. Que tal tentar novamente?';
    modal.style.display='flex'; bloquear(true); return;
  }
  if(!data.resultado) throw new Error('O servidor não enviou o resultado.');
  const nome=document.querySelector('.info strong');
  if(nome) nome.textContent=data.resultado.nome;
  else titulo.textContent=data.resultado.nome;
  mostrarFoto(img,data.resultado); bloquear(false);
}
async function carregar(){
  bloquear(true);
  const id=getId(); if(!id){location.replace('./inicio.html');return;}
  try{mostrar(await consultar(id));}catch(e){erroComRetry(form,e,carregar);}
}
async function avaliar(confirmado){
  if(ocupado||!estado?.resultado)return;
  bloquear(true);
  try{mostrar(await api('/partidas/'+estado.id_partida+'/confirmar-resultado',{id_resultado:estado.resultado.id_resultado,confirmado}));}
  catch(e){erroComRetry(form,e,carregar);}
}
if(pagina==='resultado'){
  acertou.removeAttribute('onclick');
  acertou.addEventListener('click',()=>avaliar(true));
  errou.addEventListener('click',()=>avaliar(false));
  for(const el of [acertou,errou]){
    el.tabIndex=0;el.setAttribute('role','button');
    el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();el.click();}});
  }
}
carregar();
