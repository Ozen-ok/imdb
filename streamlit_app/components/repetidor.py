import streamlit as st
import pandas as pd
import os
from PIL import Image

def criar_botao_home():
    if st.button("Home"):
        st.switch_page("pages/Home.py")

MONGO_API_URL = "http://localhost:8000/mongo"
REDIS_API_URL = "http://localhost:8000/redis"
CASSANDRA_API_URL = "http://localhost:8000/cassandra"
NEO4J_API_URL = "http://localhost:8000/neo4j"

def preparar_dados_filmes(filmes):
    if not filmes:
        return []

    df = pd.DataFrame(filmes)

    df["poster_url"] = df["titulo_id"].apply(lambda tid: f"assets/imagens/posters/{tid}.jpg")
    return df.to_dict(orient="records")

def exibir_cartao_filme(row):
    col1, col2 = st.columns([1, 4])
    with col1:
        poster_path = row.get("poster_url", "")
        if os.path.exists(poster_path):
            imagem = Image.open(poster_path)
            st.image(imagem)
        else:
            st.warning(f"Imagem não encontrada para {row['titulo']}")

    with col2:
        st.subheader(f"{row['titulo']} ({int(row['ano_lancamento'])})")

        if row.get("nota", 0) == 0:
            st.markdown("⭐ Ainda não lançado | 🗳️ Votos indisponíveis")
        else:
            # Arredonda a nota para 2 casas decimais
            nota_arredondada = round(row['nota'], 2)
            st.markdown(f"⭐ {nota_arredondada} | 🗳️ {row['numero_votos']} votos")

        tipo = row.get("tipo", "Desconhecido")
        st.markdown(f"🎬 Tipo: {tipo}")

        generos_raw = row.get("generos", "")
        if isinstance(generos_raw, str) and generos_raw.startswith("["):
            generos_lista = eval(generos_raw)
        elif isinstance(generos_raw, list):
            generos_lista = generos_raw
        else:
            generos_lista = [generos_raw]

        generos_formatado = ', '.join(str(g).strip("'\"") for g in generos_lista)
        st.markdown(f"🎞️ {generos_formatado}")

        duracao = row.get("duracao", "N/A")
        try:
            duracao = f"{int(duracao)} minutos"
        except:
            duracao = "N/A"
        if tipo.lower() != "jogo":
            st.markdown(f"⏱️ {duracao}")

        sinopse = row.get("sinopse", "")
        if isinstance(sinopse, str) and len(sinopse) > 200:
            sinopse_curta = sinopse[:200].rsplit(' ', 1)[0] + "..."
        else:
            sinopse_curta = sinopse if isinstance(sinopse, str) else "Sinopse indisponível."
        st.markdown(f"🧾 {sinopse_curta}")

def verificar_titulos_sem_imagem(filmes):
    if not filmes:
        return []

    df = pd.DataFrame(filmes)

    # Caminho base onde as imagens deveriam estar
    base_path = "assets/imagens/posters"

    # Função auxiliar que verifica se o arquivo de imagem existe
    def imagem_existe(titulo_id):
        caminho_imagem = os.path.join(base_path, f"{titulo_id}.jpg")
        return os.path.isfile(caminho_imagem)

    # Filtra os títulos que **não** têm imagem
    df_sem_imagem = df[~df["titulo_id"].apply(imagem_existe)]
    return df_sem_imagem["titulo_id"].tolist()