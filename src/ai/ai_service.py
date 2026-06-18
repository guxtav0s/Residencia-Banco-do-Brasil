import httpx
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash"
URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/" + MODEL + ":generateContent"
)

_CAMPOS_IA_VAZIOS = {
    "explicacao_ia":          "",
    "acao_sugerida":          "",
    "score_fraude":           0,
    "nivel_criticidade":      "",
    "possivel_tipo_fraude":   "",
    "indicadores_detectados": [],
}

SYSTEM_ANTIFRAUDE = (
    "Você é um analista sênior de antifraude do Banco do Brasil, "
    "especialista em fraudes bancárias no mercado brasileiro. "
    "Responda sempre em português, de forma clara, didática e objetiva. "
    "Jamais invente dados — baseie-se somente nas informações fornecidas."
)


def _calcular_desvio(transacao: dict) -> float:
    valor = transacao.get("valor", 0)
    media = transacao.get("media_conta", 0)
    return round(valor / media, 1) if media and media > 0 else 0.0


def _chamar_gemini(contents: list, timeout: float = 30.0, retries: int = 0) -> str:
    """
    Função interna que faz a chamada HTTP ao Gemini e retorna o texto limpo.
    FALHA IMEDIATA (retries=0) em caso de 429 para evitar timeout do dashboard.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY não configurada.")

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_ANTIFRAUDE}]},
        "contents": contents,
    }

    ultimo_erro = None

    for tentativa in range(retries + 1):
        try:
            r = httpx.post(
                URL,
                params={"key": api_key},
                json=payload,
                timeout=timeout,
            )

            # --- Tratamento específico do 429 (Rate Limit) ---
            if r.status_code == 429:
                if tentativa < retries:
                    espera = 15 * (2 ** tentativa)  # 15s, 30s, 60s, 120s
                    print(
                        f"[ai_service] 429 Too Many Requests. "
                        f"Aguardando {espera}s antes da tentativa {tentativa + 2}/{retries + 1}..."
                    )
                    time.sleep(espera)
                    ultimo_erro = httpx.HTTPStatusError(
                        f"429 após {tentativa + 1} tentativa(s)",
                        request=r.request,
                        response=r,
                    )
                    continue  # tenta novamente
                else:
                    # Sem mais tentativas
                    raise httpx.HTTPStatusError("429 Rate Limit", request=r.request, response=r)

            # Outros erros HTTP levantam exceção imediatamente
            r.raise_for_status()

            texto = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

            # Remove blocos markdown ```json ... ``` se presentes
            if texto.startswith("```"):
                partes = texto.split("```")
                texto = partes[1] if len(partes) > 1 else texto
                if texto.startswith("json"):
                    texto = texto[4:]
            return texto.strip()

        except httpx.TimeoutException:
            raise  # timeout não adianta tentar novamente
        except httpx.HTTPStatusError:
            raise  # outros erros HTTP sobem direto

    # Esgotou todas as tentativas por 429
    raise ultimo_erro

def _gerar_explicacao_local(transacao: dict) -> dict:
    """
    Gera uma análise técnica baseada em regras (Local AI/Heuristics) 
    para quando o Gemini estiver indisponível.
    """
    valor = transacao.get("valor", 0)
    media = transacao.get("media_conta", 0)
    desvio = _calcular_desvio(transacao)
    motivo = transacao.get("motivo_suspeita", "").lower()

    indicadores = []
    explicacoes = []

    if desvio > 3:
        indicadores.append("Valor muito acima da média")
        explicacoes.append(f"O valor de R$ {valor:,.2f} é {desvio}x superior ao padrão da conta.")

    if "madrugada" in motivo:
        indicadores.append("Horário de alto risco")
        explicacoes.append("Transação realizada em período de baixa vigilância (madrugada).")

    if transacao.get("pais") != "Brasil":
        indicadores.append("Localização internacional")
        explicacoes.append(f"Operação originada fora do país ({transacao.get('pais')}).")

    if transacao.get("tentativas", 1) >= 3:
        indicadores.append("Múltiplas tentativas")
        explicacoes.append("Detectada insistência incomum no processamento da transação.")

    score = 20
    if desvio > 2: score += 30
    if desvio > 5: score += 30
    if "madrugada" in motivo: score += 15
    score = min(score, 95)

    criticidade = "Baixo"
    if score > 50: criticidade = "Moderado"
    if score > 75: criticidade = "Alto"
    if score > 90: criticidade = "Crítico"

    return {
        "explicacao_ia": " ".join(explicacoes) or "Padrão de consumo divergente detectado pelo motor de risco local.",
        "acao_sugerida": "Bloqueio preventivo e confirmação com o titular via canais oficiais." if score > 70 else "Monitoramento intensivo da conta.",
        "score_fraude": score,
        "nivel_criticidade": criticidade,
        "possivel_tipo_fraude": "Suspeita de Invasão ou Clonagem" if score > 70 else "Anomalia Comportamental",
        "indicadores_detectados": indicadores or ["Desvio estatístico"]
    }


def explicar_anomalia(transacao: dict) -> dict:
    """
    Análise inicial completa da anomalia: explicação, ação sugerida,
    score, criticidade, tipo de fraude e indicadores detectados.
    """
    desvio = _calcular_desvio(transacao)

    prompt = f"""Analise detalhadamente a transação financeira suspeita abaixo.

## DADOS DA TRANSAÇÃO
- ID               : {transacao.get('id')}
- Valor            : R$ {transacao.get('valor', 0):.2f}
- Média histórica  : R$ {transacao.get('media_conta', 0):.2f}
- Desvio da média  : {desvio}x
- Horário          : {transacao.get('hora')}
- País             : {transacao.get('pais')}
- Cidade           : {transacao.get('cidade')}
- Tipo             : {transacao.get('tipo_transacao')}
- Tentativas       : {transacao.get('tentativas')}
- Motivo suspeita  : {transacao.get('motivo_suspeita')}
- Risco inicial    : {transacao.get('nivel_risco')}

## FATORES A AVALIAR
- Desvio do valor em relação à média histórica
- Compatibilidade do país/cidade com o perfil do cliente
- Horário atípico (madrugada, fins de semana)
- Tentativas consecutivas (possível automação ou força bruta)
- Padrões de golpe do falso funcionário, phishing ou engenharia social
- Indícios de conta laranja ou mula financeira
- Invasão de conta (credential stuffing, SIM swap)

## ESCALA DE SCORE E CRITICIDADE (devem ser consistentes)
- 0–20   → "Baixo"
- 21–50  → "Moderado"
- 51–80  → "Alto"
- 81–100 → "Crítico"

## INSTRUÇÃO PARA explicacao_ia
Escreva de 4 a 6 frases seguindo esta ordem:
1. O que foi detectado e por que é suspeito.
2. Quais combinações de fatores elevam o risco.
3. Padrão de fraude mais provável e como funciona no Brasil.
4. Justificativa do score com base nos dados concretos.
5. (Se aplicável) O que diferencia este caso de um falso positivo.

Responda SOMENTE com JSON válido, sem markdown, sem texto fora do JSON.
Retorne entre 3 e 6 indicadores detectados.

{{
  "explicacao_ia": "<análise detalhada>",
  "acao_sugerida": "<ação imediata e justificada>",
  "score_fraude": <inteiro 0-100>,
  "nivel_criticidade": "<Baixo|Moderado|Alto|Crítico>",
  "possivel_tipo_fraude": "<tipo de fraude>",
  "indicadores_detectados": ["<ind1>", "<ind2>", "<ind3>"]
}}"""

    try:
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        texto = _chamar_gemini(contents)
        
        # Tenta carregar o JSON
        try:
            resultado = json.loads(texto)
        except json.JSONDecodeError:
            # Tenta extrair JSON de dentro de blocos se o split básico falhou
            import re
            match = re.search(r'\{.*\}', texto, re.DOTALL)
            if match:
                resultado = json.loads(match.group())
            else:
                raise

        return {
            "explicacao_ia": resultado.get("explicacao_ia", resultado.get("explicacao", "")),
            "acao_sugerida":          resultado.get("acao_sugerida", ""),
            "score_fraude":           int(resultado.get("score_fraude", 50)),
            "nivel_criticidade":      resultado.get("nivel_criticidade", ""),
            "possivel_tipo_fraude":   resultado.get("possivel_tipo_fraude", ""),
            "indicadores_detectados": resultado.get("indicadores_detectados", []),
        }
    except Exception as e:
        print(f"[ai_service] Gemini indisponível ({e}). Usando IA Local.")
        return _gerar_explicacao_local(transacao)


def chat_anomalia(transacao: dict, historico: list, pergunta: str) -> str:
    """
    Responde perguntas do analista sobre uma anomalia específica,
    mantendo o contexto completo da conversa anterior (historico).

    historico: lista de dicts {"role": "user"|"model", "text": "..."}
    Retorna: string com a resposta do Gemini.
    """
    desvio = _calcular_desvio(transacao)

    contexto_transacao = f"""## TRANSAÇÃO EM ANÁLISE
- ID               : {transacao.get('id')}
- Valor            : R$ {transacao.get('valor', 0):.2f}
- Média histórica  : R$ {transacao.get('media_conta', 0):.2f}
- Desvio da média  : {desvio}x
- Horário          : {transacao.get('hora')}
- País             : {transacao.get('pais')} | Cidade: {transacao.get('cidade')}
- Tipo             : {transacao.get('tipo_transacao')}
- Tentativas       : {transacao.get('tentativas')}
- Risco            : {transacao.get('nivel_risco')}
- Motivo suspeita  : {transacao.get('motivo_suspeita')}
- Score de fraude  : {transacao.get('score_fraude', 'N/A')}
- Tipo de fraude   : {transacao.get('possivel_tipo_fraude', 'N/A')}
- Análise anterior : {transacao.get('explicacao_ia', 'N/A')}
- Ação sugerida    : {transacao.get('acao_sugerida', 'N/A')}"""

    # Monta o histórico no formato multi-turn do Gemini
    contents = []

    # Primeira mensagem sempre carrega o contexto da transação
    primeira_pergunta = (
        f"{contexto_transacao}\n\n"
        f"Você é o analista de antifraude responsável por esta transação. "
        f"Responda as perguntas do investigador de forma clara e didática, "
        f"sempre baseando-se nos dados acima.\n\n"
        f"Pergunta inicial: {historico[0]['text'] if historico else pergunta}"
    )
    contents.append({"role": "user", "parts": [{"text": primeira_pergunta}]})

    # Adiciona troca de mensagens anteriores (a partir da segunda)
    for msg in historico[1:]:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["text"]}]})

    # Adiciona a nova pergunta (se houver histórico)
    if historico:
        contents.append({"role": "user", "parts": [{"text": pergunta}]})

    try:
        return _chamar_gemini(contents, timeout=30.0)
    except httpx.TimeoutException:
        return "⚠️ A IA demorou para responder. Tente novamente."
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response else "?"
        if status == 429:
            return "⚠️ Limite de requisições atingido (429). Aguarde alguns segundos e tente novamente."
        return f"⚠️ Erro ao consultar a IA: HTTP {status}"
    except Exception as e:
        return f"⚠️ Erro ao consultar a IA: {e}"


def enriquecer_anomalias(anomalias: list, apenas_alto_risco: bool = True) -> list:
    """
    Acrescenta os campos da IA em cada anomalia.
    Tenta usar Gemini para as transações mais críticas (limite 8), 
    com fallback automático e INSTANTÂNEO para IA Local em caso de erro.
    """
    resultado = []
    contador_gemini = 0
    MAX_GEMINI = 8 

    for transacao in anomalias:
        item = dict(transacao)
        risco = item.get("nivel_risco")

        try:
            # Só tentamos Gemini se for Risco Alto e estivermos no início da lista
            if (not apenas_alto_risco or risco == "Alto") and contador_gemini < MAX_GEMINI:
                # Pequena pausa entre chamadas Gemini para respeitar 15 RPM
                if contador_gemini > 0:
                    time.sleep(2)
                
                resposta_ia = explicar_anomalia(item)
                # Se a resposta_ia veio do fallback local interno do explicar_anomalia,
                # não incrementamos o sucesso do Gemini, mas o fluxo segue.
                contador_gemini += 1
            else:
                # Demais itens ou se já estourou o limite Gemini, usa IA Local (instantânea)
                resposta_ia = _gerar_explicacao_local(item)

            # PADRONIZA OS CAMPOS (IMPORTANTE)
            item["explicacao_ia"] = resposta_ia.get("explicacao_ia", "")
            item["acao_sugerida"] = resposta_ia.get("acao_sugerida", "")
            item["score_fraude"] = resposta_ia.get("score_fraude", 0)
            item["nivel_criticidade"] = resposta_ia.get("nivel_criticidade", "")
            item["possivel_tipo_fraude"] = resposta_ia.get("possivel_tipo_fraude", "")
            item["indicadores_detectados"] = resposta_ia.get("indicadores_detectados", [])

        except Exception as e:
            item["explicacao_ia"] = f"Erro no processamento: {str(e)}"
            item["score_fraude"] = 0

        resultado.append(item)

    return resultado


def _fallback(msg: str) -> dict:
    print(f"[ai_service] fallback: {msg}")
    return dict(_CAMPOS_IA_VAZIOS)