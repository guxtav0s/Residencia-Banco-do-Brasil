from fastapi import APIRouter, HTTPException
from ..models.model import Transacao, TransacaoAnomalia
from ..services.anomaly_detection import analisar_anomalias, analisar_anomalias_ia, criar_nova_transacao
from ..repositories.data_repository import TransacaoRepository

router = APIRouter()

@router.get("/transactions")
def listar_transacoes(
    categoria: str = None, 
    cidade: str = None, 
    valor_min: float = None, 
    valor_max: float = None
    ):

    filtros = {
        "categoria": categoria, 
        "cidade": cidade, 
        "valor_min": valor_min, 
        "valor_max": valor_max
        }
    
    return TransacaoRepository.buscar_todas(filtros)

@router.get("/anomalies", response_model=list[TransacaoAnomalia])
def detectar_anomalias():
    return analisar_anomalias()

@router.get("/anomalies/ai", response_model=list[TransacaoAnomalia])
def detectar_anomalias_ia():
    return analisar_anomalias_ia()

@router.post("/transactions")
def criar_transacao(t: Transacao):
    try:
        criar_nova_transacao(t)
        return {"mensagem": "Salvo com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/transactions/{id}")
def deletar(id: int):
    TransacaoRepository.deletar(id)
    return {"mensagem": "Deletado!"}
