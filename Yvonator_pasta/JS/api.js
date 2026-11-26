const KEY = 'yvonator.partida';
export const getId = () => sessionStorage.getItem(KEY);
export const setId = id => sessionStorage.setItem(KEY,id);
export async function api(path, body) {
  const options = body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
  const response = await fetch('/api'+path, {...options,cache:'no-store'});
  let data;
  try { data = await response.json(); } catch { throw new Error('Resposta inesperada do servidor.'); }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Não foi possível concluir a operação.');
  return data;
}
export const consultar = id => api('/partidas/'+encodeURIComponent(id));
export function navegar(estado, pagina) {
  const destino = estado.status === 'em_andamento' ? 'perguntas' : estado.status === 'confirmada' ? 'personagem' : 'resultado';
  if (pagina !== destino) { location.replace('./'+destino+'.html'); return true; }
  return false;
}
export function mostrarFoto(img, resultado) {
  const padrao = '../IMG/professor_padrao.svg';
  const id = resultado.id_personagem;
  img.alt = resultado.nome || 'Professor';
  // Também protege contra fotos existentes, mas corrompidas ou incompatíveis.
  img.onerror = () => { img.onerror = null; img.src = padrao; };
  img.src = resultado.foto || (Number.isInteger(id) && id > 0
    ? '/api/personagens/' + id + '/foto'
    : padrao);
}
export function erroComRetry(container, erro, tentar) {
  container.querySelector('[data-api-erro]')?.remove();
  const block=document.createElement('div'); block.dataset.apiErro='1'; block.setAttribute('role','alert');
  const text=document.createElement('span'); text.textContent=erro.message || 'Falha de conexão.';
  const button=document.createElement('button'); button.type='button'; button.textContent='Tentar novamente';
  button.addEventListener('click',()=>{block.remove(); tentar();},{once:true});
  block.append(text,' ',button); container.append(block);
}
