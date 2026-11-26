from typing import Literal
from pydantic import BaseModel, Field, StrictBool, ConfigDict

class RespostaEntrada(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id_pergunta: int = Field(gt=0, strict=True)
    resposta: Literal['sim','nao','naoSei']

class ConfirmacaoEntrada(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id_resultado: int = Field(gt=0, strict=True)
    confirmado: StrictBool
