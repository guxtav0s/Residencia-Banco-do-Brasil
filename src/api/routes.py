from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..models.transaction_model import Transacao, TransacaoAnomalia
from ..services.anomaly_detection import (
    analisar_anomalias,
    analisar_anomalias_ia,
    criar_nova_transacao,
    calcular_probabilidade_fraude,
)
from ..repositories.data_repository import TransacaoRepository
from ..ai.ai_service import enriquecer_anomalias, chat_anomalia


class ChatInput(BaseModel):
    transacao: dict
    historico: list
    pergunta: str


# Entrada do teste de validacao por porcentagem (campos minimos necessarios)
class ValidacaoFraudeInput(BaseModel):
    valor: float
    hora: str = "12:00"
    tentativas: int = 1
    pais: str = "Brasil"
    conta: Optional[str] = None
    media_conta: Optional[float] = None

router = APIRouter()


@router.get("/transactions")
def listar_transacoes(
    categoria: str = None,
    cidade: str = None,
    valor_min: float = None,
    valor_max: float = None,
):
    filtros = {
        "categoria": categoria,
        "cidade": cidade,
        "valor_min": valor_min,
        "valor_max": valor_max,
    }
    return TransacaoRepository.buscar_todas(filtros)


@router.get("/anomalies", response_model=list[TransacaoAnomalia])
def detectar_anomalias():
    return analisar_anomalias()


@router.get("/anomalies/ai", response_model=list[TransacaoAnomalia])
def detectar_anomalias_ia():
    return analisar_anomalias_ia()


@router.get("/anomalies/ai-explained")
def detectar_com_explicacao(apenas_alto_risco: bool = True):
   
    anomalias = analisar_anomalias_ia()
    if not anomalias:
        return []
    
    # Ordena para garantir que os de risco Alto venham primeiro
    anomalias.sort(key=lambda x: 1 if x.get("nivel_risco") == "Alto" else 0, reverse=True)
    
    # Limita a 20 anomalias no total para evitar timeout do dashboard
    return enriquecer_anomalias(anomalias[:20], apenas_alto_risco=apenas_alto_risco)


@router.post("/anomalies/chat")
def chat_com_anomalia(body: ChatInput):
    """Responde perguntas do analista sobre uma anomalia específica via Gemini."""
    resposta = chat_anomalia(body.transacao, body.historico, body.pergunta)
    return {"resposta": resposta}


@router.post("/validacao/fraude")
def validar_probabilidade_fraude(dados: ValidacaoFraudeInput):
    """Teste de validacao: estima a probabilidade (%) de uma transacao ser fraude.
    NAO grava nada no banco — apenas analisa o que foi enviado."""
    return calcular_probabilidade_fraude(dados.model_dump())


@router.post("/transactions")
def criar_transacao(t: Transacao):
    try:
        criar_nova_transacao(t)
        return {"mensagem": "Salvo com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/motives")
def listar_motivos():
    return TransacaoRepository.buscar_motivos()


@router.post("/motives")
def salvar_motivo(body: dict):
    TransacaoRepository.salvar_motivo(
        body["transacao_id"], 
        body["explicacao"], 
        body["score"], 
        body["indicadores"]
    )
    return {"mensagem": "Motivo salvo com sucesso!"}


@router.delete("/transactions/{id}")
def deletar(id: int):
    TransacaoRepository.deletar(id)
    return {"mensagem": "Deletado!"}
