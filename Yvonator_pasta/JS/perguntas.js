import { api, getId, setId, consultar, navegar, erroComRetry } from './api.js';
const form=document.querySelector('.opcoes form');
const texto=form.querySelector('p');
const radios=[...form.querySelectorAll('input[name="escolha"]')];
const TEMPO_RESPOSTA=700, TEMPO_NOVA_PERGUNTA=300;
const esperar=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let estado=null, ocupado=false;
function bloquear(valor){
  ocupado=valor;
  radios.forEach(r=>r.disabled=valor);
  form.setAttribute('aria-busy',String(valor));
}
function mostrar(data, manterBloqueio=false){
  estado=data;
  if(navegar(data,'perguntas')) return false;
  if(!data.pergunta) throw new Error('O servidor não enviou uma pergunta.');
  texto.textContent=data.pergunta.enunciado;


radios.forEach(r => {
    r.checked = false;
    r.closest('.fundoResposta').classList.remove('selecionada');
});

  
  if(!manterBloqueio) bloquear(false);
  return true;
}
async function iniciar(){
  bloquear(true); texto.textContent='Carregando...';
  try {
    let id=getId();
    if(!id || new URLSearchParams(location.search).has('nova')){
      const data=await api('/partidas',{}); setId(data.id_partida);
      history.replaceState(null,'',location.pathname); mostrar(data);
    } else { mostrar(await consultar(id)); }
  } catch(e){texto.textContent='Não foi possível carregar a partida.';erroComRetry(form,e,iniciar);}
}
async function responder(valor){
  if(ocupado || !estado?.pergunta) return;
  const q=estado.pergunta.id, id=estado.id_partida;


  radios.forEach(r => {
    r.closest('.fundoResposta').classList.toggle('selecionada', r.value === valor);
});

bloquear(true);
form.classList.add('aguardando-resposta');


  try {
    // API e intervalo em paralelo: a resposta selecionada permanece visível.
    const [data]=await Promise.all([
      api('/partidas/'+id+'/responder',{id_pergunta:q,resposta:valor}),
      esperar(TEMPO_RESPOSTA)
    ]);
    form.classList.remove('aguardando-resposta');
    if(!mostrar(data,true)) return;
    texto.classList.add('nova-pergunta');
    await esperar(TEMPO_NOVA_PERGUNTA);
    texto.classList.remove('nova-pergunta');
    bloquear(false);
  } catch(e){
    form.classList.remove('aguardando-resposta');
    texto.classList.remove('nova-pergunta');
    texto.textContent='Não foi possível enviar a resposta.';
    erroComRetry(form,e,async()=>{try{mostrar(await consultar(id));}catch{iniciar();}});
  }
}
form.addEventListener('submit',e=>e.preventDefault());
radios.forEach(r=>r.addEventListener('change',()=>responder(r.value)));
iniciar();
