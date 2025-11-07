from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import inspect
import json
import random

load_dotenv('./.env')

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv('OPENROUTER_API_KEY'),
)
from db_sqlite import inserir_last_tweet, listar_tweets

now_sp = datetime.now(ZoneInfo("America/Sao_Paulo"))
data_hora_sp = now_sp.strftime("%d/%m/%Y %H:%M:%S")
offset = now_sp.strftime("%z")  # ex: -0300
offset_fmt = f"UTC{offset[:3]}:{offset[3:]}"  # ex: UTC-03:00


# Conjunto de 10 tons possíveis para guiar geração
TONES = [
    {
        "key": "romantico_leve",
        "nome": "Romântico leve",
        "diretriz": "carinhoso e gentil, metáforas simples, emojis moderados, evitar clichês e melosidade"
    },
    {
        "key": "bem_humorado_memes",
        "nome": "Bem-humorado com memes",
        "diretriz": "humor leve, referência sutil a memes sem nomes específicos, linguagem internet, sem hashtags"
    },
    {
        "key": "fofo_carinho",
        "nome": "Fofo e carinhoso",
        "diretriz": "doce e acolhedor, diminutivos moderados, vibe cute sem infantilizar"
    },
    {
        "key": "pimenta_suave",
        "nome": "Pimenta suave",
        "diretriz": "flertar sutil, sugestivo sem vulgaridade, confiante e elegante"
    },
    {
        "key": "poetico_simples",
        "nome": "Poético simples",
        "diretriz": "imagens poéticas em frases curtas, ritmo natural, evitar rimas forçadas"
    },
    {
        "key": "zoeira_respeitosa",
        "nome": "Zoeira respeitosa",
        "diretriz": "brincadeiras provocativas leves, irreverência sem desrespeito, informal e espirituoso"
    },
    {
        "key": "sincero_direto",
        "nome": "Sincero e direto",
        "diretriz": "objetivo e caloroso, poucas palavras, sem floreios, simples e genuíno"
    },
    {
        "key": "brincalhao_energia",
        "nome": "Brincalhão com energia",
        "diretriz": "alto astral, playful, ritmo animado, exclamações moderadas"
    },
    {
        "key": "calmo_acolhedor",
        "nome": "Calmo e acolhedor",
        "diretriz": "tranquilo, reconfortante, sensação de abraço, suavidade nas palavras"
    },
    {
        "key": "confiante_sedutor",
        "nome": "Confiante e sedutor",
        "diretriz": "confiança elegante, elogios sutis, sedução discreta sem exagero"
    },
]

# Janela configurável para evitar repetição de tom (padrão: 5)
TONE_ROTATION_WINDOW = int(os.getenv('TONE_ROTATION_WINDOW', '5'))


def _definir_tom(limit: int = TONE_ROTATION_WINDOW):
    """Analisa os últimos tweets apenas para inferir um tom e retorna um dos 10 tons.

    Saída: dict { "key": str, "nome": str, "diretriz": str }
    """
    try:
        tweets = listar_tweets() or []
        textos = []
        for t in tweets[:limit]:
            txt = (t.get('tweet_text') or '').replace('\n', ' ').strip()
            if txt:
                textos.append(txt)

        # Se não houver tweets, escolhe um tom aleatório
        if not textos:
            return random.choice(TONES)

        tones_brief = [{"key": t["key"], "nome": t["nome"], "diretriz": t["diretriz"]} for t in TONES]

        system_msg = (
            "Você é um classificador de tom. Analise APENAS para perceber o estilo geral, "
            "não copie, não parafraseie e não reutilize nenhum conteúdo. "
            "Escolha exatamente UM dos 10 tons fornecidos e produza APENAS um JSON com o formato:\n"
            "{\"key\": <key>, \"nome\": <nome>, \"diretriz\": <diretriz>}\n"
            "Se os textos estiverem mistos, escolha o tom dominante ou um que permita VARIAÇÃO."
        )

        user_msg = (
            "Tons disponíveis (key, nome, diretriz):\n" + json.dumps(tones_brief, ensure_ascii=False) + "\n\n"
            "Tweets recentes (apenas para ANÁLISE DE TOM, nunca para uso):\n" + "\n".join(textos)
        )

        completion = client.chat.completions.create(
            extra_body={"temperature": 0.2},
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
        )
        resp_text = completion.choices[0].message.content
        # Tenta parsear o JSON
        data = json.loads(resp_text)
        key = data.get("key")
        match = next((t for t in TONES if t["key"] == key), None)
        chosen = None
        if match:
            nome = data.get("nome") or match["nome"]
            diretriz = data.get("diretriz") or match["diretriz"]
            chosen = {"key": key, "nome": nome, "diretriz": diretriz}
        else:
            chosen = random.choice(TONES)

        # Evitar repetição: se o tom escolhido já foi usado recentemente, variar
        recent_keys = set(_recent_tone_keys(limit))
        # Dominante dos últimos pela classificação por tweet
        prev_class = _classificar_tons_por_tweet(limit)
        counts = {}
        for item in prev_class:
            k = item.get('key')
            if k:
                counts[k] = counts.get(k, 0) + 1
        dominant_key = None
        if counts:
            dominant_key = max(counts.items(), key=lambda x: x[1])[0]

        excluded = set(recent_keys)
        if dominant_key:
            excluded.add(dominant_key)

        if chosen and chosen.get('key') in excluded:
            candidates = [t for t in TONES if t['key'] not in excluded]
            if candidates:
                alt = random.choice(candidates)
                print(f"🔄 Variei tom para evitar repetição: {chosen['key']} -> {alt['key']}")
                return {"key": alt['key'], "nome": alt['nome'], "diretriz": alt['diretriz']}
            else:
                # Se todos excluídos, pelo menos evita último usado
                avoid = list(recent_keys)[:1]
                candidates = [t for t in TONES if t['key'] not in avoid]
                if candidates:
                    alt = random.choice(candidates)
                    print(f"🔄 Variei tom (fallback): {chosen['key']} -> {alt['key']}")
                    return {"key": alt['key'], "nome": alt['nome'], "diretriz": alt['diretriz']}
        return chosen
    except Exception:
        return random.choice(TONES)


def _print_tone_info(tone: dict):
    """Imprime informações do tom escolhido antes do tweet principal."""
    try:
        nomes_chaves = ", ".join([t.get("key", "?") for t in TONES])
        print(f"🎛️ Tom escolhido: {tone.get('nome', '?')} ({tone.get('key', '?')})")
        print(f"   Diretriz: {tone.get('diretriz', '')}")
        print(f"   Tons definidos: {nomes_chaves}")
    except Exception as e:
        print(f"⚠️ Erro ao exibir tom: {e}")


def _classificar_tons_por_tweet(limit: int = 5):
    """Classifica o tom de cada um dos últimos N tweets. Retorna lista de dicts.

    Saída: [{"i": int, "key": str, "nome": str, "diretriz": str}]
    """
    try:
        tweets = listar_tweets() or []
        textos = []
        for t in tweets[:limit]:
            txt = (t.get('tweet_text') or '').replace('\n', ' ').strip()
            if txt:
                textos.append(txt)
        if not textos:
            return []

        tones_brief = [{"key": t["key"], "nome": t["nome"], "diretriz": t["diretriz"]} for t in TONES]

        system_msg = (
            "Você é um classificador de tom. Para CADA texto listado, escolha exatamente UM dos 10 tons. "
            "Não copie, não parafraseie conteúdo; produza APENAS um JSON array com itens no formato:\n"
            "[{\"i\": <numero_do_item>, \"key\": <key>, \"nome\": <nome>, \"diretriz\": <diretriz>}, ...]"
        )
        enumerados = [f"{i+1}) {txt}" for i, txt in enumerate(textos)]
        user_msg = (
            "Tons disponíveis (key, nome, diretriz):\n" + json.dumps(tones_brief, ensure_ascii=False) + "\n\n"
            "Tweets numerados (apenas para ANÁLISE DE TOM):\n" + "\n".join(enumerados)
        )

        completion = client.chat.completions.create(
            extra_body={"temperature": 0.2},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            model="openai/gpt-oss-120b",
        )
        resp_text = completion.choices[0].message.content.strip()
        try:
            # Tenta parse direto; se falhar, tenta extrair o bloco JSON entre []
            data = json.loads(resp_text)
        except Exception:
            start = resp_text.find('[')
            end = resp_text.rfind(']')
            if start != -1 and end != -1:
                data = json.loads(resp_text[start:end+1])
            else:
                data = []

        resultados = []
        for item in data:
            key = item.get('key')
            match = next((t for t in TONES if t['key'] == key), None)
            if match:
                resultados.append({
                    'i': item.get('i'),
                    'key': key,
                    'nome': item.get('nome') or match['nome'],
                    'diretriz': item.get('diretriz') or match['diretriz'],
                })
        return resultados
    except Exception:
        return []


def _print_prev_tones(classificacoes: list):
    if not classificacoes:
        print("🧭 Toms dos últimos tweets: nenhum disponível")
        return
    print("🧭 Toms dos últimos tweets (inferidos):")
    for item in classificacoes:
        print(f"   {item.get('i')}) {item.get('nome')} ({item.get('key')})")

def bom_dia():
    prev = _classificar_tons_por_tweet()
    _print_prev_tones(prev)
    tone = _definir_tom()
    user_content = (
        f"Data e hora atual (São Paulo/BR): {data_hora_sp} ({offset_fmt}). "
        "Gere uma única mensagem jovem de bom dia para Laura, pronta para postagem, sem hashtags. "
        f"Tom alvo: {tone['nome']}. Diretriz de tom: {tone['diretriz']}. "
        "Varie o estilo; não repita fórmulas; não use conteúdo de tweets anteriores."
    )
    completion = client.chat.completions.create(
      extra_body={},
      model="openai/gpt-oss-120b",
      messages=[
                  {
                    "role": "system",
                    "content": (
                        "Você é um robô e suas respostas vão direto para uma conta no X (Twitter). "
                        "Não faça perguntas, não peça confirmação e não inclua metacommentários. "
                        "Escreva como alguém jovem (nascido em 2003+), com tom natural e leve, usando gírias brasileiras quando fizer sentido, sem soar forçado. "
                        "Não use hashtags em nenhuma hipótese. "
                        "Responda apenas com uma única mensagem pronta para postagem, sem prefixos. "
                        "Você foi criado para escrever mensagens de bom dia carinhosas e divertidas para a Laura. "
                        "Use o dia e a hora que eu te enviar para criar uma saudação única: "
                        "pode ser super romântica, bem-humorada, descontraída, educada ou até com um toque de malícia leve — "
                        "sempre de forma surpreendente e aleatória. "
                        "Varie o estilo a cada mensagem, mas sempre com carinho. "
                        "Siga o 'Tom alvo' e a 'Diretriz de tom' enviados pelo usuário; use exatamente um dos 10 tons definidos. "
                        "Não copie, não parafraseie e não use nenhum conteúdo dos tweets anteriores. Gere mensagem ORIGINAL."
                    )
                  },
                  {
                    "role": "user",
                    "content": user_content
                  }
                ]
    )
    resp_text = completion.choices[0].message.content
    _print_tone_info(tone)
    print(resp_text)
    try:
        type_name = inspect.currentframe().f_code.co_name
        inserir_last_tweet(resp_text, f"{type_name}:{tone['key']}")
    except Exception as e:
        print(f"❌ Erro ao gravar no SQLite: {e}")

def boa_tarde():
    prev = _classificar_tons_por_tweet()
    _print_prev_tones(prev)
    tone = _definir_tom()
    user_content = (
        f"Data e hora atual (São Paulo/BR): {data_hora_sp} ({offset_fmt}). "
        "Gere uma única mensagem jovem de boa tarde para Laura, pronta para postagem, sem hashtags. "
        f"Tom alvo: {tone['nome']}. Diretriz de tom: {tone['diretriz']}. "
        "Varie o estilo; não repita fórmulas; não use conteúdo de tweets anteriores."
    )
    completion = client.chat.completions.create(
      extra_body={},
      model="openai/gpt-oss-120b",
      messages=[
                  {
                    "role": "system",
                    "content": (
                        "Você é um robô e suas respostas vão direto para uma conta no X (Twitter). "
                        "Não faça perguntas, não peça confirmação e não inclua metacommentários. "
                        "Escreva como alguém jovem (nascido em 2003+), com tom natural e leve, usando gírias brasileiras quando fizer sentido, sem soar forçado. "
                        "Não use hashtags em nenhuma hipótese. "
                        "Responda apenas com uma única mensagem pronta para postagem, sem prefixos. "
                        "Você foi criado para escrever mensagens carinhosas e divertidas para a Laura. "
                        "Use o dia e a hora que eu te enviar para criar uma saudação única: "
                        "pode ser super romântica, bem-humorada, descontraída, educada ou até com um toque de malícia leve — "
                        "sempre de forma surpreendente e aleatória. "
                        "Varie o estilo a cada mensagem, mas sempre com carinho. "
                        "Siga o 'Tom alvo' e a 'Diretriz de tom' enviados pelo usuário; use exatamente um dos 10 tons definidos. "
                        "Não copie, não parafraseie e não use nenhum conteúdo dos tweets anteriores. Gere mensagem ORIGINAL."
                    )
                  },
                  {
                    "role": "user",
                    "content": user_content
                  }
                ]
    )
    resp_text = completion.choices[0].message.content
    _print_tone_info(tone)
    print(resp_text)
    try:
        type_name = inspect.currentframe().f_code.co_name
        inserir_last_tweet(resp_text, f"{type_name}:{tone['key']}")
    except Exception as e:
        print(f"❌ Erro ao gravar no SQLite: {e}")


def boa_noite():
    prev = _classificar_tons_por_tweet()
    _print_prev_tones(prev)
    tone = _definir_tom()
    user_content = (
        f"Data e hora atual (São Paulo/BR): {data_hora_sp} ({offset_fmt}). "
        "Gere uma única mensagem jovem de boa noite para Laura, pronta para postagem, sem hashtags. "
        f"Tom alvo: {tone['nome']}. Diretriz de tom: {tone['diretriz']}. "
        "Varie o estilo; não repita fórmulas; não use conteúdo de tweets anteriores."
    )
    completion = client.chat.completions.create(
      extra_body={},
      model="openai/gpt-oss-120b",
      messages=[
                  {
                    "role": "system",
                    "content": (
                        "Você é um robô e suas respostas vão direto para uma conta no X (Twitter). "
                        "Não faça perguntas, não peça confirmação e não inclua metacommentários. "
                        "Escreva como alguém jovem (nascido em 2003+), com tom natural e leve, usando gírias brasileiras quando fizer sentido, sem soar forçado. "
                        "Não use hashtags em nenhuma hipótese. "
                        "Responda apenas com uma única mensagem pronta para postagem, sem prefixos. "
                        "Você foi criado para escrever mensagens carinhosas e divertidas para a Laura. "
                        "Use o dia e a hora que eu te enviar para criar uma saudação única: "
                        "pode ser super romântica, bem-humorada, descontraída, educada ou até com um toque de malícia leve — "
                        "sempre de forma surpreendente e aleatória. "
                        "Varie o estilo a cada mensagem, mas sempre com carinho. "
                        "Siga o 'Tom alvo' e a 'Diretriz de tom' enviados pelo usuário; use exatamente um dos 10 tons definidos. "
                        "Não copie, não parafraseie e não use nenhum conteúdo dos tweets anteriores. Gere mensagem ORIGINAL."
                    )
                  },
                  {
                    "role": "user",
                    "content": user_content
                  }
                ]
    )
    resp_text = completion.choices[0].message.content
    _print_tone_info(tone)
    print(resp_text)
    try:
        type_name = inspect.currentframe().f_code.co_name
        inserir_last_tweet(resp_text, f"{type_name}:{tone['key']}")
    except Exception as e:
        print(f"❌ Erro ao gravar no SQLite: {e}")


def sextou_bom_dia():
    prev = _classificar_tons_por_tweet()
    _print_prev_tones(prev)
    tone = _definir_tom()
    user_content = (
        f"Data e hora atual (São Paulo/BR): {data_hora_sp} ({offset_fmt}). "
        "Gere uma única mensagem jovem de bom dia de sexta-feira (sextou) para Laura, pronta para postagem, sem hashtags. "
        f"Tom alvo: {tone['nome']}. Diretriz de tom: {tone['diretriz']}. "
        "Varie o estilo; não repita fórmulas; não use conteúdo de tweets anteriores."
    )
    completion = client.chat.completions.create(
      extra_body={},
      model="openai/gpt-oss-120b",
      messages=[
                  {
                    "role": "system",
                    "content": (
                        "Você é um robô e suas respostas vão direto para uma conta no X (Twitter). "
                        "Não faça perguntas, não peça confirmação e não inclua metacommentários. "
                        "Escreva como alguém jovem (nascido em 2003+), com tom natural e leve, usando gírias brasileiras quando fizer sentido, sem soar forçado. "
                        "Não use hashtags em nenhuma hipótese. "
                        "Responda apenas com uma única mensagem pronta para postagem, sem prefixos. "
                        "Você foi criado para escrever mensagens carinhosas e divertidas para a Laura. "
                        "Use o dia e a hora que eu te enviar para criar uma saudação única: "
                        "pode ser super romântica, bem-humorada, descontraída, educada ou até com um toque de malícia leve — "
                        "sempre de forma surpreendente e aleatória. "
                        "Varie o estilo a cada mensagem, mas sempre com carinho. "
                        "Siga o 'Tom alvo' e a 'Diretriz de tom' enviados pelo usuário; use exatamente um dos 10 tons definidos. "
                        "Não copie, não parafraseie e não use nenhum conteúdo dos tweets anteriores. Gere mensagem ORIGINAL."
                    )
                  },
                  {
                    "role": "user",
                    "content": user_content
                  }
                ]
    )
    resp_text = completion.choices[0].message.content
    _print_tone_info(tone)
    print(resp_text)
    try:
        type_name = inspect.currentframe().f_code.co_name
        inserir_last_tweet(resp_text, f"{type_name}:{tone['key']}")
    except Exception as e:
        print(f"❌ Erro ao gravar no SQLite: {e}")


def sextou_boa_tarde():
    prev = _classificar_tons_por_tweet()
    _print_prev_tones(prev)
    tone = _definir_tom()
    user_content = (
        f"Data e hora atual (São Paulo/BR): {data_hora_sp} ({offset_fmt}). "
        "Gere uma única mensagem jovem de boa tarde de sexta-feira (quem fez fez) para Laura, pronta para postagem, sem hashtags. "
        f"Tom alvo: {tone['nome']}. Diretriz de tom: {tone['diretriz']}. "
        "Varie o estilo; não repita fórmulas; não use conteúdo de tweets anteriores."
    )
    completion = client.chat.completions.create(
      extra_body={},
      model="openai/gpt-oss-120b",
      messages=[
                  {
                    "role": "system",
                    "content": (
                        "Você é um robô. Suas respostas irão direto para uma conta no X (Twitter). "
                        "Não faça perguntas, não peça confirmação e não inclua metacommentários. "
                        "Responda apenas com uma única mensagem pronta para postagem. "
                        "Você foi criado para escrever mensagens carinhosas e divertidas para a Laura. "
                        "Use o dia e a hora que eu te enviar para criar uma saudação única: "
                        "pode ser super romântica, bem-humorada, descontraída, educada ou até com um toque de malícia leve — "
                        "sempre de forma surpreendente e aleatória. "
                        "Varie o estilo a cada mensagem, mas sempre com carinho. "
                        "Siga o 'Tom alvo' e a 'Diretriz de tom' enviados pelo usuário; use exatamente um dos 10 tons definidos. "
                        "Não copie, não parafraseie e não use nenhum conteúdo dos tweets anteriores. Gere mensagem ORIGINAL."
                    )
                  },
                  {
                    "role": "user",
                    "content": user_content
                  }
                ]
    )
    resp_text = completion.choices[0].message.content
    _print_tone_info(tone)
    print(resp_text)
    try:
        type_name = inspect.currentframe().f_code.co_name
        inserir_last_tweet(resp_text, f"{type_name}:{tone['key']}")
    except Exception as e:
        print(f"❌ Erro ao gravar no SQLite: {e}")


if __name__ == '__main__':
    sextou_boa_tarde()
def _recent_tone_keys(limit: int = TONE_ROTATION_WINDOW):
    """Extrai as keys de tom registradas em 'type' dos últimos N tweets (formato func:ton_key)."""
    try:
        tweets = listar_tweets() or []
        keys = []
        for t in tweets[:limit]:
            typ = (t.get('type') or '')
            if ':' in typ:
                parts = typ.split(':', 1)
                if len(parts) == 2 and parts[1]:
                    keys.append(parts[1].strip())
        return keys
    except Exception:
        return []
