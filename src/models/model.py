from pydantic import BaseModel

class Transacao(BaseModel):
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
    media_conta: float = 0.0

class TransacaoAnomalia(BaseModel):
    # Usando composição ou repetindo campos se necessário para simplificar
    id: int
    valor: float
    data: str
    hora: str
    categoria: str
    conta: str
    cidade: str
    pais: str
    tipo_transacao: str
    tentativas: int
    media_conta: float
    motivo_suspeita: str
    nivel_risco: str
