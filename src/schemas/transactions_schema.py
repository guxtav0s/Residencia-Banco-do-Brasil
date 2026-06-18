from pydantic import BaseModel
from typing import Optional


# 📥 Entrada (POST /transactions)
class TransacaoCreate(BaseModel):
    id: int
    valor: float
    data: str
    hora: str
    dia_semana: str
    categoria: str
    conta: str
    cidade: str
    estado: str
    pais: str
    latitude: float
    longitude: float
    tipo_transacao: str
    dispositivo: str
    estabelecimento: str
    tentativas: int
    ip_origem: str
    is_fraude: int


# 📤 Saída (GET /transactions)
class TransacaoResponse(TransacaoCreate):
    media_conta: Optional[float] = None


# 🚨 Anomalias
class TransacaoAnomaliaSchema(BaseModel):
    id: int
    valor: float
    conta: str
    cidade: str
    categoria: str
    risco: str
    score: Optional[float] = None
    explicacao: Optional[str] = None