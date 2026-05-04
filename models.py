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

class TransacaoAnomalia(Transacao):
    motivo_suspeita: str
    nivel_risco: str
