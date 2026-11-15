# Projeto 5 - Construção e Deploy de Routing com Multi-Agentes de IA

# ============================================================================
# BLOCO NOVO (nao existia no original): como rodar no ambiente moderno
# ============================================================================
# Este arquivo foi modernizado para rodar com o uv (o "pip + conda" moderno). Toda
# parte alterada mostra o CODIGO ORIGINAL comentado logo acima da versao nova,
# para voce comparar as duas. Blocos sem original estao marcados como BLOCO NOVO.
#
# Como rodar (no terminal, dentro desta pasta):
#   1) Instalar o uv (uma vez so na maquina):
#        Linux / WSL / macOS:  curl -LsSf https://astral.sh/uv/install.sh | sh
#        Windows PowerShell:   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
#   2) Criar o ambiente:       uv sync
#   3) Chave da Groq no .env:  GROQ_API_KEY=gsk_...   (https://console.groq.com/keys)
#   4) Subir o app:            uv run streamlit run dsa_app_p5.py
#
# O que ha de novo nesta versao:
#   - seletor de provedor de LLM na barra lateral: Groq (padrao, como no curso),
#     OpenAI, Anthropic, xAI/Grok e o Ollama local (gratis, sem chave);
#   - limite de tokens explicito: sem ele a Groq cortava as respostas de pesquisa;
#   - mensagens de erro especificas para chave invalida, modelo retirado e cota.
#
# Estudo passo a passo, uma peca de cada vez: Projeto5_Routing_Multi_Agentes.ipynb
# Nomes de modelo validos na sua conta:       uv run python dsa_lista_modelos.py

# Importar módulo para interagir com sistema operacional
import os

# Importar módulo para lidar com arquivos JSON
import json

# Importar módulo Streamlit para criar interface web
import streamlit as st

# Importar módulo para carregar variáveis de ambiente
from dotenv import load_dotenv

# Importar cliente Groq para usar modelos de IA
from groq import Groq

# ============================================================================
# BLOCO NOVO (nao existia no original): modulos extras do ambiente moderno
# ============================================================================
# Modulos da biblioteca padrao
import re                          # le o tempo de espera nas mensagens de cota
import time                        # espera antes de tentar de novo
from pathlib import Path           # monta caminhos a partir da pasta deste arquivo
from types import SimpleNamespace  # cria objetos "de mentira" com atributos (adaptador)

# Clientes dos outros provedores. OpenAI, xAI/Grok e Ollama "falam o dialeto" da
# API da OpenAI, entao a MESMA biblioteca atende os tres: so muda o endereco.
# A Anthropic (Claude) tem API propria e ganha um adaptador mais abaixo.
from openai import OpenAI
import anthropic

# ============================================================================
# CODIGO ORIGINAL (mantido comentado para referencia)
# ============================================================================
# # Configurar página do Streamlit
# st.set_page_config(page_title="Data Science Academy", page_icon=":100:", layout="centered")
#
# ============================================================================
# VERSAO MODERNA (Python 3.12 + uv)
# O que mudou: app publicado na internet sem citar a escola na interface: o
#               titulo da aba do navegador passou a ser neutro.
# ============================================================================
# Configurar página do Streamlit
st.set_page_config(page_title="Routing Multi-Agentes", page_icon=":100:", layout="centered")

# ============================================================================
# BLOCO NOVO (nao existia no original): senha de acesso do app publicado
# ============================================================================
# Publicado no Streamlit Community Cloud, o app fica num endereco publico: sem
# senha, qualquer pessoa com o link gastaria a SUA cota (e o SEU dinheiro) nos
# provedores de LLM. A senha fica em APP_PASSWORD nos "Secrets" do Community
# Cloud (ou em .streamlit/secrets.toml na sua maquina), NUNCA no codigo.
# Sem APP_PASSWORD configurada, o app abre direto, como no original.
import hmac

def dsa_senha_configurada():
    # O Streamlit levanta erro se nao existir nenhum secrets.toml: tratamos como "sem senha"
    try:
        senha = st.secrets.get("APP_PASSWORD")
    except Exception:
        senha = None
    return str(senha or os.getenv("APP_PASSWORD") or "")

def dsa_verifica_senha():
    senha_certa = dsa_senha_configurada()
    if not senha_certa or st.session_state.get("dsa_senha_ok"):
        return True

    def confere():
        # compare_digest compara em tempo constante: nao "vaza" quantos caracteres acertou
        digitada = st.session_state.pop("dsa_senha", "")
        st.session_state["dsa_senha_ok"] = hmac.compare_digest(digitada.encode(), senha_certa.encode())
        if not st.session_state["dsa_senha_ok"]:
            time.sleep(1)   # atrasa tentativas em serie (forca bruta)

    st.title("Assistente Multi-Agentes")
    st.text_input("Senha de acesso", type = "password", on_change = confere, key = "dsa_senha")
    if st.session_state.get("dsa_senha_ok") is False:
        st.error("Senha incorreta.")
    return False

# st.stop() encerra a execucao aqui: nada abaixo (nem a barra lateral) aparece sem a senha
if not dsa_verifica_senha():
    st.stop()

# Configurar título da barra lateral do Streamlit
st.sidebar.title("Instruções")

# Exibir instruções para o usuário na barra lateral
st.sidebar.markdown("""
Digite sua pergunta na caixa ao lado e clique no botão **Enviar**.

A aplicação selecionará automaticamente o melhor Agente para responder com base na complexidade da pergunta.

Tipos de perguntas:
- **Factual**: Perguntas curtas e diretas.
- **Pesquisa**: Perguntas que exigem respostas detalhadas.
- **Geral**: Outras consultas.

IA Generativa comete erros. **SEMPRE** use seu conhecimento para verificar as respostas.
""")

# ============================================================================
# CODIGO ORIGINAL (mantido comentado para referencia)
# ============================================================================
# # Botão de suporte na barra lateral que exibe mensagem ao clicar
# if st.sidebar.button("Suporte"):
#     st.sidebar.write("Dúvidas? Envie um e-mail para: suporte@datascienceacademy.com.br")
#
# ============================================================================
# VERSAO MODERNA (Python 3.12 + uv)
# O que mudou: botao removido. No app publicado ele mandaria os visitantes
#               para o suporte da escola, que nao responde por esta versao.
# ============================================================================

# ============================================================================
# CODIGO ORIGINAL (mantido comentado para referencia)
# ============================================================================
# # Carregar variáveis de ambiente
# load_dotenv()
#
# ============================================================================
# VERSAO MODERNA (Python 3.12 + uv)
# O que mudou: load_dotenv() sem caminho procura o .env a partir da pasta
#               errada quando o app e iniciado de outro lugar. Com o caminho
#               explicito o .env ao lado deste arquivo sempre e encontrado.
# ============================================================================
load_dotenv(Path(__file__).resolve().parent / ".env")

# Carregar configuração dos modelos Groq a partir de arquivo JSON
# ============================================================================
# CODIGO ORIGINAL (mantido comentado para referencia)
# ============================================================================
# with open('groq_modelos_config.json', 'r') as file:
#     modelos_config = json.load(file)
#
# ============================================================================
# VERSAO MODERNA (Python 3.12 + uv)
# O que mudou: o caminho relativo so funcionava se o terminal estivesse nesta
#               pasta; e sem encoding='utf-8' o Windows le errado os acentos do
#               JSON (Forneça, português).
# ============================================================================
DSA_PASTA = Path(__file__).resolve().parent
with open(DSA_PASTA / 'groq_modelos_config.json', 'r', encoding = 'utf-8') as file:
    modelos_config = json.load(file)

# ============================================================================
# BLOCO NOVO (nao existia no original): provedores de LLM e tratamento de erros
# ============================================================================
# Limite de tokens da resposta. Sem ele, a Groq aplica um padrao de 3072 tokens no
# gpt-oss-120b e TODA resposta de pesquisa sai cortada no meio (medido: 3 de 3).
# Com 6000 as respostas terminam (a maior medida usou 5022). Nao exagere: o plano
# gratuito da Groq libera 8000 tokens POR MINUTO, e esse limite entra na conta.
DSA_MAX_TOKENS = 6000

# Uma chave vazia, ausente ou ainda com o texto de exemplo conta como "nao
# configurada": o provedor simplesmente nao aparece no seletor, sem erro.
DSA_PLACEHOLDERS = ("cole-", "seu-", "sua-", "coloque", "your-", "xxx", "<")

# Devolve a chave de API limpa, ou None se ela nao estiver configurada de verdade
def dsa_chave_valida(nome_da_variavel):
    valor = (os.getenv(nome_da_variavel) or "").strip().strip('"').strip("'")
    if not valor or valor.lower().startswith(DSA_PLACEHOLDERS):
        return None
    return valor

# Descobre onde o Ollama esta rodando. Ordem: OLLAMA_HOST do .env -> localhost ->
# IP do Windows (no WSL2 o Ollama pode estar instalado no Windows, e o IP dele e o
# "nameserver" do /etc/resolv.conf). Devolve a primeira URL que responder, ou None.
def dsa_detecta_ollama_host():
    import urllib.request
    candidatos = []
    if os.getenv("OLLAMA_HOST"):
        candidatos.append(os.getenv("OLLAMA_HOST").strip().rstrip("/"))
    candidatos.append("http://localhost:11434")
    # So no WSL vale a pena tentar o IP do Windows. Em outros lugares (como o
    # servidor do Streamlit Community Cloud) isso so gastaria 2 s de espera.
    import platform
    if "microsoft" in platform.release().lower():
        try:
            for linha in Path("/etc/resolv.conf").read_text().splitlines():
                if linha.startswith("nameserver"):
                    candidatos.append(f"http://{linha.split()[1]}:11434")
        except OSError:
            pass
    for host in candidatos:
        try:
            with urllib.request.urlopen(f"{host}/api/tags", timeout = 2):
                return host
        except Exception:
            continue
    return None

# Tabela dos provedores. Na Groq, "modelo" e None porque cada rota usa o modelo do
# groq_modelos_config.json (como no curso). Nos outros, um modelo unico do .env
# atende as tres rotas.
DSA_PROVEDORES = {
    "groq":      {"rotulo": "Groq (nuvem)",                    "chave": "GROQ_API_KEY",
                  "modelo": None, "base_url": None},
    "openai":    {"rotulo": "OpenAI (nuvem)",                  "chave": "OPENAI_API_KEY",
                  "modelo": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "base_url": None},
    "anthropic": {"rotulo": "Anthropic / Claude (nuvem)",      "chave": "ANTHROPIC_API_KEY",
                  "modelo": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"), "base_url": None},
    "xai":       {"rotulo": "xAI / Grok (nuvem)",              "chave": "XAI_API_KEY",
                  "modelo": os.getenv("XAI_MODEL", "grok-4"), "base_url": "https://api.x.ai/v1"},
    "ollama":    {"rotulo": "Ollama (local, grátis)",          "chave": None,
                  "modelo": os.getenv("OLLAMA_MODEL", "llama3.2"), "base_url": None},
}

# O Ollama so entra no seletor se estiver respondendo. Na sua maquina ele aparece;
# no Community Cloud (onde nao existe Ollama) ele some, em vez de dar erro.
# O cache guarda a resposta por 60 s para nao testar a conexao a cada clique.
@st.cache_data(ttl = 60, show_spinner = False)
def dsa_ollama_disponivel():
    return dsa_detecta_ollama_host() is not None

# Lista os provedores que podem ser usados agora: os de nuvem entram se a chave
# estiver preenchida (.env ou Secrets); o Ollama, se estiver no ar
def dsa_provedores_configurados():
    return [nome for nome, cfg in DSA_PROVEDORES.items()
            if (dsa_chave_valida(cfg["chave"]) if cfg["chave"] else dsa_ollama_disponivel())]

# Adaptador da Anthropic. Os agentes chamam client.chat.completions.create(...) e
# leem resposta.choices[0].message.content -- o formato da Groq/OpenAI. A API do
# Claude e diferente (messages.create, "system" em parametro proprio, max_tokens
# obrigatorio). Esta classe "veste" o Claude com a roupa da Groq: por fora, o
# mesmo formato; por dentro, a traducao. Analogia: um adaptador de tomada.
class DSAAdaptadorAnthropic:

    def __init__(self, api_key):
        self._cliente = anthropic.Anthropic(api_key = api_key)
        # Cria o "caminho" client.chat.completions.create que os agentes esperam
        self.chat = SimpleNamespace(completions = SimpleNamespace(create = self._create))

    def _create(self, messages, model, max_completion_tokens = DSA_MAX_TOKENS, **_ignorados):
        # Na Anthropic a mensagem de sistema vai no parametro system=, fora da lista
        sistema = "\n".join(m["content"] for m in messages if m["role"] == "system")
        conversa = [m for m in messages if m["role"] != "system"]
        argumentos = {"model": model, "max_tokens": max_completion_tokens, "messages": conversa}
        if sistema:
            argumentos["system"] = sistema
        r = self._cliente.messages.create(**argumentos)
        if r.stop_reason == "refusal":
            texto = "(O modelo recusou responder a esta pergunta.)"
        else:
            texto = "".join(bloco.text for bloco in r.content if bloco.type == "text")
        # Traduz o motivo de parada para o vocabulario da OpenAI ("length" = cortada)
        fim = "length" if r.stop_reason == "max_tokens" else "stop"
        return SimpleNamespace(choices = [SimpleNamespace(message = SimpleNamespace(content = texto),
                                                          finish_reason = fim)])

# Cria o cliente do provedor escolhido. Todos devolvem um objeto com o mesmo
# client.chat.completions.create(...): e por isso que os agentes nao mudam.
# O @st.cache_resource evita recriar o cliente a cada clique (o Streamlit roda o
# script inteiro de novo a cada interacao).
@st.cache_resource
def dsa_cria_cliente(provedor):
    cfg = DSA_PROVEDORES[provedor]
    if provedor == "groq":
        return Groq(api_key = dsa_chave_valida(cfg["chave"]))
    if provedor == "anthropic":
        return DSAAdaptadorAnthropic(dsa_chave_valida(cfg["chave"]))
    if provedor == "ollama":
        # Se o Ollama nao responder, usamos localhost mesmo: o erro de conexao
        # aparece na hora da pergunta, com uma mensagem explicando o que fazer.
        host = dsa_detecta_ollama_host() or "http://localhost:11434"
        return OpenAI(base_url = f"{host}/v1", api_key = "ollama")  # o Ollama nao valida chave
    # openai e xai: mesma biblioteca, so muda o endereco (base_url) e a chave
    return OpenAI(api_key = dsa_chave_valida(cfg["chave"]), base_url = cfg["base_url"])

# Extrai o tempo de espera de uma mensagem de cota. Os provedores escrevem de tres
# jeitos: "try again in 7.2s", "in 1m30s" e "in 4h30m36.288s". Um regex que so
# lesse segundos faria o app esperar 15 s quando deveria esperar horas.
def dsa_segundos_de_espera(mensagem):
    m = re.search(r"try again in\s+(?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", mensagem)
    if not m or not any(m.groups()):
        return None
    h, mi, s = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + float(s or 0)

# Traduz a excecao do provedor em (tipo, mensagem para o aluno). Cada erro tem causa
# e solucao diferentes; uma mensagem generica ensinaria errado.
# Tipos: conexao | auth | modelo | cota_minuto | cota_diaria | outro
def dsa_classifica_erro(erro):
    msg = str(erro)
    codigo = getattr(erro, "status_code", None)
    if isinstance(erro, ConnectionError) or "Connection" in type(erro).__name__:
        return "conexao", ("O servidor do LLM não respondeu. Se for o Ollama, confira com "
                           "'ollama list' e 'curl localhost:11434'. Detalhe: " + msg[:300])
    if codigo == 401 or "invalid_api_key" in msg or "authentication" in msg.lower():
        return "auth", "Chave de API inválida ou ausente. Confira o .env ou os Secrets (sem aspas, sem espaços em volta)."
    # Atencao: a Groq responde 400 (e nao 404) para modelo retirado ("decommissioned")
    if (codigo == 404 or "model_not_found" in msg or "decommissioned" in msg
            or "does not exist" in msg or "not found" in msg.lower()):
        # (Para o administrador: os nomes validos saem de 'uv run python dsa_lista_modelos.py')
        return "modelo", ("Modelo não encontrado ou retirado do ar neste provedor. Confira o nome do "
                          "modelo no groq_modelos_config.json (Groq) ou no .env (demais provedores). "
                          "No Ollama: 'ollama list' e 'ollama pull NOME'.")
    if codigo == 429 or "rate_limit" in msg or "rate limit" in msg.lower():
        espera = dsa_segundos_de_espera(msg)
        if espera is not None and espera > 300:
            return "cota_diaria", (f"Cota DIÁRIA do provedor esgotada (libera em ~{espera / 3600:.1f} h). "
                                   "Esperar não adianta: troque o provedor na barra lateral.")
        return "cota_minuto", (f"Limite POR MINUTO do provedor atingido (libera em ~{espera or 30:.0f} s). "
                               "Aguarde alguns segundos e clique em Enviar de novo.")
    return "outro", f"{type(erro).__name__}: {msg[:400]}"

# Executa funcao() de novo quando o erro e passageiro (cota por minuto); qualquer
# outro erro sobe na hora para a interface explicar.
def dsa_executa_com_retry(funcao, tentativas = 3):
    for tentativa in range(1, tentativas + 1):
        try:
            return funcao()
        except Exception as erro:
            tipo, _ = dsa_classifica_erro(erro)
            if tipo != "cota_minuto" or tentativa == tentativas:
                raise
            time.sleep(min(dsa_segundos_de_espera(str(erro)) or 5, 60))

# ============================================================================
# CODIGO ORIGINAL (mantido comentado para referencia)
# ============================================================================
# # Inicializar o cliente Groq com a chave de API carregada das variáveis de ambiente
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))
#
# ============================================================================
# VERSAO MODERNA (Python 3.12 + uv)
# O que mudou: o original so falava com a Groq. Agora o cliente vem do
#               provedor escolhido na barra lateral (Groq e o padrao). O nome
#               'client' foi mantido: as classes dos agentes abaixo nao mudam
#               uma linha.
# ============================================================================
# Seletor do provedor na barra lateral. So aparecem os provedores com chave no
# .env ou nos Secrets (o Ollama, se estiver no ar). LLM_PROVEDOR do .env define qual vem
# selecionado ao abrir o app; o padrao deste capitulo e a Groq.
dsa_opcoes = dsa_provedores_configurados()
if not dsa_opcoes:
    st.error("Nenhum provedor de LLM configurado. Defina GROQ_API_KEY no .env "
             "(ou nos Secrets do Streamlit Community Cloud).")
    st.stop()
dsa_padrao = os.getenv("LLM_PROVEDOR", "groq").strip().lower()
dsa_indice_padrao = dsa_opcoes.index(dsa_padrao) if dsa_padrao in dsa_opcoes else 0
provedor_escolhido = st.sidebar.selectbox("Provedor de LLM",
                                          dsa_opcoes,
                                          index = dsa_indice_padrao,
                                          format_func = lambda p: DSA_PROVEDORES[p]["rotulo"])

# Mostra na interface com quem o app esta falando. Sem isso, quando a resposta vem
# estranha, voce nao sabe qual modelo a produziu.
if provedor_escolhido == "groq":
    st.sidebar.info("Provedor: **Groq**  \nUm modelo por rota:  \n" +
                    "  \n".join(f"- {rota}: `{cfg['modelo']}`" for rota, cfg in modelos_config.items()))
else:
    st.sidebar.info(f"Provedor: **{DSA_PROVEDORES[provedor_escolhido]['rotulo']}**  \n"
                    f"Modelo (nas 3 rotas): `{DSA_PROVEDORES[provedor_escolhido]['modelo']}`  \n"
                    "O roteamento por tamanho de modelo existe só na Groq.")

# O nome 'client' e o mesmo do original: os agentes abaixo continuam iguais
client = dsa_cria_cliente(provedor_escolhido)

# Classe para avaliar a intenção da consulta do usuário
class AgenteIntencao:
    @staticmethod
    def avaliar_intencao(consulta):

        # Avalia se a consulta é factual
        if len(consulta.split()) <= 10 and 'Informe' in consulta:
            return 'factual'

        # Avalia se a consulta é do tipo pesquisa
        elif '?' in consulta:
            return 'pesquisa'

        # Caso contrário, considera como consulta geral
        else:
            return 'geral'

# Classe para buscar informação usando o modelo adequado
class AgenteInformacao:
    @staticmethod
    def buscar_informacao(consulta, intencao):

        # Retorna a config de acordo com a intenção do usuário
        config = modelos_config[intencao]

        # ====================================================================
        # CODIGO ORIGINAL (mantido comentado para referencia)
        # ====================================================================
        # # Extrai o modelo
        # modelo = config["modelo"]
        #
        # ====================================================================
        # VERSAO MODERNA (Python 3.12 + uv)
        # O que mudou: na Groq cada rota usa o seu modelo (como no curso); nos
        #               outros provedores, o modelo unico do .env atende as
        #               tres rotas.
        # ====================================================================
        # Extrai o modelo: na Groq, o da rota; nos outros provedores, o modelo unico do .env
        modelo = config["modelo"] if provedor_escolhido == "groq" else DSA_PROVEDORES[provedor_escolhido]["modelo"]

        # Formata o prompt
        prompt_customizado = config["prompt"].format(consulta=consulta)

        # ====================================================================
        # CODIGO ORIGINAL (mantido comentado para referencia)
        # ====================================================================
        # # Gera a resposta do LLM
        # resposta = client.chat.completions.create(
        #     messages = [{"role": "user", "content": prompt_customizado}],
        #     model = modelo,
        # )
        #
        # return resposta.choices[0].message.content, modelo
        #
        # ====================================================================
        # VERSAO MODERNA (Python 3.12 + uv)
        # O que mudou: limite de tokens explicito (sem ele a Groq corta toda
        #               resposta de pesquisa em 3072 tokens), retry automatico
        #               para cota por minuto e aviso quando a resposta vier
        #               cortada.
        # ====================================================================
        # Gera a resposta do LLM (com retry se a cota por minuto estourar)
        resposta = dsa_executa_com_retry(lambda: client.chat.completions.create(
            messages = [{"role": "user", "content": prompt_customizado}],
            model = modelo,
            max_completion_tokens = DSA_MAX_TOKENS,
        ))

        # finish_reason == "length" significa: o modelo parou porque bateu no limite de
        # tokens, e nao porque terminou. Avisamos em vez de entregar um texto cortado calado.
        texto = resposta.choices[0].message.content or ""
        if resposta.choices[0].finish_reason == "length":
            texto += "\n\n*(Resposta cortada: o modelo atingiu o limite de tokens.)*"

        return texto, modelo

# Classe para formular resposta final com base na intenção
class AgenteResposta:
    @staticmethod
    def formular_resposta(informacao, intencao):

        # Formula resposta rápida para consultas factuais
        if intencao == 'factual':
            return f"Resposta rápida: {informacao}"

        # Formula resposta detalhada para consultas de pesquisa
        elif intencao == 'pesquisa':
            return f"Resposta detalhada: {informacao}"

        # Formula resposta geral para outros casos
        else:
            return f"Resposta geral: {informacao}"

# Função principal que obtém resposta com base na consulta
def dsa_obtem_resposta(consulta):

    # Avaliar intenção da consulta
    intencao = AgenteIntencao.avaliar_intencao(consulta)

    # Buscar informação com base na intenção avaliada
    informacao, modelo_usado = AgenteInformacao.buscar_informacao(consulta, intencao)

    # Formular resposta final com base na informação e intenção
    resposta_final = AgenteResposta.formular_resposta(informacao, intencao)

    # Retornar resposta final e modelo usado
    return resposta_final, modelo_usado

# ============================================================================
# CODIGO ORIGINAL (mantido comentado para referencia)
# ============================================================================
# # Interface principal do Streamlit
# st.title("DSA Projeto 5")
#
# ============================================================================
# VERSAO MODERNA (Python 3.12 + uv)
# O que mudou: titulo neutro, sem o nome da escola, para o app publicado.
# ============================================================================
# Interface principal do Streamlit
st.title("Assistente Multi-Agentes")
st.subheader("Construção e Deploy de Routing com Multi-Agentes de IA")

# Campo para entrada de texto da consulta do usuário
consulta = st.text_input("Digite sua pergunta:")

# Botão para enviar consulta
if st.button("Enviar"):

    # Verifica se a consulta não está vazia
    if consulta.strip():

        # ====================================================================
        # CODIGO ORIGINAL (mantido comentado para referencia)
        # ====================================================================
        # # Obter resposta e modelo utilizado
        # resposta, modelo_usado = dsa_obtem_resposta(consulta)
        #
        # # Exibir resposta
        # st.write(resposta)
        #
        # # Exibir modelo utilizado para gerar resposta
        # st.caption(f"Modelo utilizado: {modelo_usado}")
        #
        # ====================================================================
        # VERSAO MODERNA (Python 3.12 + uv)
        # O que mudou: erros (chave invalida, modelo retirado, cota) viram
        #               mensagens especificas na tela em vez de um traceback;
        #               spinner enquanto os agentes trabalham; o rodape mostra
        #               tambem o provedor.
        # ====================================================================
        try:
            # Obter resposta e modelo utilizado
            with st.spinner("Os agentes estão trabalhando..."):
                resposta, modelo_usado = dsa_obtem_resposta(consulta)

        # Se algo der errado, explica a causa provavel em vez de mostrar um traceback
        except Exception as erro:
            tipo, mensagem = dsa_classifica_erro(erro)
            st.error(mensagem)

        else:
            # Exibir resposta
            st.write(resposta)

            # Exibir modelo e provedor utilizados para gerar resposta
            st.caption(f"Modelo utilizado: {modelo_usado}  |  Provedor: {DSA_PROVEDORES[provedor_escolhido]['rotulo']}")

    # Exibe aviso caso a consulta esteja vazia
    else:
        st.warning("Por favor, digite uma pergunta antes de enviar.")


