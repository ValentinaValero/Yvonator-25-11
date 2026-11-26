from backend.algorithms.compatibilidade import classificar, escolher_pergunta


def base():
    qs = [dict(id=i, enunciado=t, categoria=g, prioridade=1.) for i,t,g in [
        (1,'Seu personagem é professor(a)?','função'),
        (2,'Seu personagem atua na pedagogia?','função'),
        (19,'Seu personagem atua em Matemática?','disciplina'),
        (20,'Seu personagem atua em Português?','disciplina'),
        (45,'Seu personagem usa óculos?','aparência')]]
    ps=[{'id':i} for i in range(1,7)]
    linhas=[('sim','nao','sim','nao','sim'),('sim','nao','sim','nao','nao'),('sim','nao','nao','sim','sim'),('sim','nao','nao','sim','nao'),('nao','sim','nao','nao','sim'),('nao','nao','nao','nao','nao')]
    mat={(i,q['id']):a for i,linha in enumerate(linhas,1) for q,a in zip(qs,linha)}
    return ps,qs,mat


def proxima(ps,qs,mat,r,ex=None):
    rank=classificar(ps,mat,r,{q['id']:1 for q in qs},ex or set(),qs)
    return escolher_pergunta(rank,qs,mat,set(r),r),rank


def test_primeira_sem_genero_prioriza_aparencia():
    ps,qs,mat=base()
    q,_=proxima(ps,qs,mat,{})
    assert q['id']==45


def test_resposta_antiga_sobre_funcao_ainda_funciona():
    ps,qs,mat=base()
    q,_=proxima(ps,qs,mat,{1:'nao'})
    assert q['id']==2


def test_matematica_nao_pergunta_portugues_sem_sobreposicao():
    ps,qs,mat=base()
    q,rank=proxima(ps,qs,mat,{1:'sim',19:'sim'})
    assert q['id']==45
    assert len(rank)==len(ps)  # ainda tolera uma resposta incorreta
    assert escolher_pergunta(rank,[q for q in qs if q['id']!=45],mat,{1,19,2},{1:'sim',19:'sim',2:'nao'}) is None


def test_duas_disciplinas_podem_coexistir():
    ps,qs,mat=base();mat[(1,20)]='sim'
    q,_=proxima(ps,qs,mat,{1:'sim',19:'sim',45:'naoSei',2:'nao'})
    assert q['id']==20


def test_rejeicao_permite_reabrir_ramo():
    ps,qs,mat=base()
    q,rank=proxima(ps,qs,mat,{1:'sim',19:'sim'},{1,2})
    assert q is not None and q['id'] in (20,45)
    assert {i['personagem']['id'] for i in rank}=={3,4,5,6}


def test_nao_sei_nao_filtra():
    ps,qs,mat=base()
    _,rank=proxima(ps,qs,mat,{1:'naoSei'})
    assert len(rank)==6 and all(abs(i['peso']-1/6)<1e-9 for i in rank)
