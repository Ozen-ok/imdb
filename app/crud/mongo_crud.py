from pymongo.collection import Collection
from fastapi import HTTPException

def ordenar_resultados(collection: Collection, query: dict, ordenar_por: str, ordem: int):
    """
    Função para ordenar os resultados de uma consulta.
    
    :param collection: A coleção onde a consulta será realizada.
    :param query: O filtro da consulta.
    :param ordenar_por: O campo pelo qual ordenar (default 'nota').
    :param ordem: A ordem da ordenação (-1 para decrescente, 1 para crescente).
    :return: Os resultados ordenados da consulta.
    """
    # Definir a ordenação
    ordenacao = [(ordenar_por, ordem)]  # -1 para decrescente, 1 para crescente
    
    # Retornar os resultados ordenados
    return list(collection.find(query).sort(ordenacao))

# INSERÇÕES -----------------------------------------------

def inserir_filme(collection: Collection, filme: dict):
    resultado = collection.insert_one(filme)
    return str(resultado.inserted_id)


def inserir_ator(collection: Collection, ator: dict):
    resultado = collection.insert_one(ator)
    return str(resultado.inserted_id)

def inserir_elenco(collection: Collection, relacao: dict):
    resultado = collection.insert_one(relacao)
    return str(resultado.inserted_id)

# CONSULTAS -----------------------------------------------

def buscar_filmes_simples(collection: Collection, campo: str, valor: any, ordenar_por: str = 'nota', ordem: int = -1):
    """
    Função para buscar filmes com base em um campo específico (como título, nota, ano de lançamento, etc.).
    :param collection: A coleção de filmes.
    :param campo: O campo a ser filtrado (ex: "titulo", "nota", "ano_lancamento").
    :param valor: O valor que será procurado no campo especificado.
    :param ordenar_por: O campo pelo qual os resultados serão ordenados (default é 'nota').
    :param ordem: A direção da ordenação (1 para crescente, -1 para decrescente).
    :return: Lista de filmes que atendem ao filtro, ordenados pelo campo especificado.
    """
    
    # Criação do filtro baseado no campo e valor passados
    if campo == "titulo":
        filtro = {"titulo": {"$regex": valor, "$options": "i"}}  # Filtro case-insensitive para o título
    elif campo == "nota":
        filtro = {"nota": {"$gte": valor}}  # Busca por filmes com nota maior ou igual ao valor
    elif campo == "ano_lancamento":
        filtro = {"ano_lancamento": {"$gte": valor}}  # Busca por filmes lançados após o ano
    elif campo == "generos":
        filtro = {"generos": {"$all": valor}}  # Busca filmes que tenham todos os gêneros fornecidos
    elif campo == "tipo":
        filtro = {"tipo": valor}  # Busca filmes do tipo especificado
    else:
        raise ValueError(f"Campo '{campo}' não reconhecido. Utilize um campo válido como 'titulo', 'nota', 'ano_lancamento', etc.")

    # Realiza a busca com o filtro fornecido e aplica a ordenação
    return ordenar_resultados(collection, filtro, ordenar_por, ordem)

def buscar_filmes_avancado(collection: Collection, generos: list, ano_min: int, nota_min: float, ordenar_por: str, ordem: int):
    """
    Consulta avançada combinando múltiplos filtros, incluindo o filtro de tipo, e ordena os resultados.
    """
    query = {
        "generos": {"$all": generos},  # Gêneros devem conter todos os valores fornecidos
        "ano_lancamento": {"$gte": ano_min},  # Ano de lançamento maior ou igual ao ano mínimo
        "nota": {"$gte": nota_min},  # Nota maior ou igual à nota mínima
    }
    
    # Aplicando a ordenação
    return ordenar_resultados(collection, query, ordenar_por, ordem)

def buscar_filmes_por_ator(
    filmes_collection: Collection,
    elenco_collection: Collection,
    atores_collection: Collection,
    nome_ator: str,
    ordenar_por: str = 'ano_lancamento',
    ordem: int = -1
):
    """
    Busca filmes com base no nome de um ator, usando junção entre as coleções.
    """
    pipeline = [
        # Filtra o ator pelo nome
        {"$match": {"nome_ator": nome_ator}},
        
        # Junta com a coleção de elenco para pegar os títulos que ele participou
        {"$lookup": {
            "from": elenco_collection.name,
            "localField": "ator_id",
            "foreignField": "ator_id",
            "as": "elenco_info"
        }},
        {"$unwind": "$elenco_info"},

        # Junta com a coleção de filmes para obter os detalhes dos filmes
        {"$lookup": {
            "from": filmes_collection.name,
            "localField": "elenco_info.titulo_id",
            "foreignField": "titulo_id",
            "as": "filme_info"
        }},
        {"$unwind": "$filme_info"},

        # Substitui a estrutura final pelo conteúdo do filme
        {"$replaceRoot": {"newRoot": "$filme_info"}},

        # Ordenação final
        {"$sort": {ordenar_por: ordem}}
    ]

    return list(atores_collection.aggregate(pipeline))

# ATUALIZAÇÃO ---------------------------------------------

def atualizar_campo_filme(collection: Collection, titulo_id: str, campo: str, novo_valor: any):
    """
    Atualiza um campo específico de um filme no banco de dados.
    :param collection: A coleção onde o filme está armazenado.
    :param titulo_id: O ID do título do filme.
    :param campo: O campo a ser atualizado (exemplo: 'nota', 'ano_lancamento', 'generos').
    :param novo_valor: O novo valor para o campo especificado.
    """
    # Verificar se o filme existe
    resultado = collection.find_one({"titulo_id": titulo_id})
    
    if not resultado:
        # Se o filme não existe, lançar um erro HTTP
        raise HTTPException(status_code=404, detail=f"Filme com o título ID '{titulo_id}' não encontrado")
    
    # Atualizar o campo do filme especificado pelo usuário
    collection.update_one(
        {"titulo_id": titulo_id},
        {"$set": {campo: novo_valor}}
    )
    
    return {"status": "sucesso", "mensagem": f"{campo} do filme atualizado com sucesso"}

# REMOÇÃO -------------------------------------------------

def remover_filme(collection: Collection, titulo_id: str) -> bool:
    # Verificar se o filme existe antes de tentar removê-lo
    resultado = collection.find_one({"titulo_id": titulo_id})
    
    if not resultado:
        raise HTTPException(status_code=404, detail=f"Filme com o título ID '{titulo_id}' não encontrado")
    
    # Caso o filme exista, realizar a remoção
    resultado = collection.delete_one({"titulo_id": titulo_id})
    return resultado.deleted_count > 0  # Retorna True se a remoção for bem-sucedida

# AGREGAÇÃO / ANÁLISE -------------------------------------

def contar_filmes_por_ano(collection: Collection):
    pipeline = [
        {"$group": {"_id": "$ano_lancamento", "quantidade": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    return list(collection.aggregate(pipeline))

def media_notas_por_genero(collection: Collection):
    pipeline = [
        {"$unwind": "$generos"},
        {"$group": {
            "_id": "$generos",
            "soma_nota": {"$sum": "$nota"},
            "contagem": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "genero": "$_id",
            "media_nota": {"$divide": ["$soma_nota", "$contagem"]}
        }},
        {"$sort": {"media_nota": -1}}
    ]
    return list(collection.aggregate(pipeline))

def buscar_atores_por_filmes(collection_filmes: Collection, collection_elenco: Collection, collection_atores: Collection, titulo_id: str):
    """
    Lista os atores que participaram de um filme, com detalhes como nome, ano de nascimento,
    personagem e outros filmes que participou (com título, ano e ID para imagem).
    """
    # Busca os registros de elenco associados ao título
    elenco = list(collection_elenco.find({"titulo_id": titulo_id}))

    # Coleta os IDs dos atores
    ator_ids = [item["ator_id"] for item in elenco]

    # Busca as informações dos atores na collection de filmes (ou atores, dependendo da sua estrutura)
    atores = list(collection_atores.find({"ator_id": {"$in": ator_ids}}))

    resultado = []
    for ator in atores:
        print("ator encontrado.")
        ator_id = ator.get("ator_id")
        nome = ator.get("nome_ator")
        ano_nascimento = ator.get("ano_nascimento")

        # Pega personagem correspondente a esse ator no filme atual
        personagem = next((item["nome_personagem"] for item in elenco if item["ator_id"] == ator_id), "Desconhecido")

        # Busca todos os títulos que esse ator participou
        participacoes = list(collection_elenco.find({"ator_id": ator_id}))
        titulo_ids = [p["titulo_id"] for p in participacoes]

        # Recupera os títulos e anos para exibir junto com o ID
        titulos = []
        for tid in titulo_ids:
            filme = collection_filmes.find_one({"titulo_id": tid})
            if filme:
                titulos.append({
                    "titulo": filme.get("titulo", "Desconhecido"),
                    "ano": filme.get("ano_lancamento", "N/A"),
                    "titulo_id": filme.get("titulo_id")  # necessário para a imagem
                })

        resultado.append({
            "ator_id": ator_id,
            "nome_ator": nome,
            "ano_nascimento": ano_nascimento,
            "nome_personagem": personagem,
            "titulos": titulos  # cada um com titulo, ano, titulo_id
        })
    return resultado


"""""
from config.db_config import get_mongo_client

# Inserir Filme
def inserir_filme3(filme):
    client = get_mongo_client()
    try:
        db = client['imdb_db']
        colecao_filmes = db['filmes']
        colecao_filmes.insert_one(filme)
    except Exception as e:
        print(f"Erro ao inserir o filme: {e}")

# Inserir Ator
def inserir_ator3(ator):
    client = get_mongo_client()
    try:
        db = client['imdb_db']
        colecao_atores = db['atores']
        colecao_atores.insert_one(ator)
    except Exception as e:
        print(f"Erro ao inserir o ator: {e}")

# Inserir Elenco (Relação Ator - Filme)
def inserir_elenco3(elenco):
    client = get_mongo_client()
    try:
        db = client['imdb_db']
        colecao_elenco = db['elenco']
        colecao_elenco.insert_one(elenco)
    except Exception as e:
        print(f"Erro ao inserir o elenco: {e}")
"""""