import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

MINDSDB_HOST = os.getenv("MINDSDB_HOST", "127.0.0.1")
MINDSDB_PORT = int(os.getenv("MINDSDB_PORT", "47335"))
MINDSDB_USER = os.getenv("MINDSDB_USER", "mindsdb")
MINDSDB_PASSWORD = os.getenv("MINDSDB_PASSWORD", "")
MINDSDB_DATABASE = os.getenv("MINDSDB_DATABASE", "mindsdb")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")


def connect_mindsdb():
    try:
        connection = mysql.connector.connect(
            host=MINDSDB_HOST,
            port=MINDSDB_PORT,
            user=MINDSDB_USER,
            password=MINDSDB_PASSWORD,
            database=MINDSDB_DATABASE
        )
        print("Conectado ao MindsDB!")
        return connection
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MindsDB: {err}")
        return None


def query_predictor(predictor_name, input_data):
    connection = connect_mindsdb()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        where_clauses = [f"{key}='{value}'" for key, value in input_data.items()]
        where_str = " AND ".join(where_clauses)
        
        query = f"SELECT * FROM {predictor_name} WHERE {where_str}"
        print(f"Executando: {query}")
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    
    except mysql.connector.Error as err:
        print(f"Erro na query: {err}")
        return None


def interpret_user_query(user_message):
    connection = connect_mindsdb()
    if not connection:
        return simple_interpret(user_message)
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT text, completion
        FROM mindsdb.movie_intent_model
        WHERE text = '{user_message.replace("'", "''")}'
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if result and result.get('completion'):
            import json
            try:
                completion_text = result['completion']
            
                parsed = json.loads(completion_text)
                
                intent = parsed.get('intent', 'unknown')
                params = {
                    'movie_name': parsed.get('movie_name'),
                    'actor_name': parsed.get('actor_name'),
                    'franchise_name': parsed.get('franchise_name')
                }
                return {'intent': intent, 'params': params}
            except json.JSONDecodeError:
                print(f"Resposta do modelo não é JSON válido: {completion_text}")
                return simple_interpret(user_message)
        else:
            return simple_interpret(user_message)
    
    except mysql.connector.Error as err:
        print(f"Erro ao interpretar com MindsDB: {err}")
        return simple_interpret(user_message)


def simple_interpret(user_message):
    msg_lower = user_message.lower()
    
    if any(word in msg_lower for word in ['popular', 'populares', 'em alta', 'trending']):
        return {'intent': 'popular', 'params': {}}
    
    elif any(word in msg_lower for word in ['ator', 'atriz', 'diretor', 'filmes de', 'filmes do']):
     
        for keyword in ['ator', 'atriz', 'diretor', 'filmes de', 'filmes do', 'filmes da']:
            if keyword in msg_lower:
                parts = msg_lower.split(keyword)
                if len(parts) > 1:
                    actor_name = parts[1].strip()
                    return {'intent': 'search_actor', 'params': {'actor_name': actor_name}}
    
    return {'intent': 'search_movie', 'params': {'movie_name': user_message}}


def create_predictor_example():
    connection = connect_mindsdb()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        query = """
        CREATE PREDICTOR movie_recommender
        FROM files
        (SELECT * FROM movie_data)
        PREDICT rating
        """
        
        cursor.execute(query)
        print("Predictor criado com sucesso!")
        
        cursor.close()
        connection.close()
    
    except mysql.connector.Error as err:
        print(f"Erro ao criar predictor: {err}")


def create_nlp_model(force_recreate=False):
    connection = connect_mindsdb()
    if not connection:
        print("Não foi possível conectar ao MindsDB")
        return
    
    try:
        cursor = connection.cursor()
        
        print("Configurando ML Engine para Ollama...")
        
        try:
            engine_query = """
            CREATE ML_ENGINE ollama_engine
            FROM ollama;
            """
            cursor.execute(engine_query)
            print("ML Engine Ollama criado!")
        except mysql.connector.Error as err:
           
            if "already exists" in str(err):
                print("ML Engine 'ollama_engine' já existe (usando o existente)")
            else:
                raise 
        
        print(f"Configurando modelo NLP com Ollama ({OLLAMA_MODEL})...")
        
        if force_recreate:
            print("Modo force_recreate ativado - removendo modelo existente...")
            try:
                cursor.execute("DROP MODEL IF EXISTS mindsdb.movie_intent_model;")
                print("   Modelo antigo removido")
            except mysql.connector.Error as drop_err:
                print(f"   Aviso ao remover modelo: {drop_err}")
    
        try:
            cursor.execute("SHOW MODELS;")
            models = cursor.fetchall()
            model_exists = any('movie_intent_model' in str(model) for model in models)
            
            if model_exists and not force_recreate:
                print("   Modelo 'movie_intent_model' já existe")
                print("   Usando modelo existente...")
                print("   Para recriar: create_nlp_model(force_recreate=True)")
            else:
                model_query = f"""
                CREATE MODEL mindsdb.movie_intent_model
                PREDICT completion
                USING
                    engine = 'ollama_engine',
                    model_name = '{OLLAMA_MODEL}',
                    ollama_serve_url = 'http://{OLLAMA_HOST}',
                    prompt_template = 'Analise esta mensagem do usuário sobre filmes e retorne APENAS um JSON válido.
Mensagem: "{{{{text}}}}"

Identifique:
- intent: "search_movie" (buscar filme pelo nome), "search_actor" (buscar filmes de um ator/diretor), "popular" (filmes populares), ou "search_franchise" (buscar filmes de uma franquia)
- movie_name: nome do filme se mencionado (ou null)
- actor_name: nome do ator/diretor se mencionado (ou null)
- franchise_name: nome da franquia se mencionada como Marvel, DC, Star Wars, Harry Potter etc (ou null)

Exemplos:
- "Matrix" → {{"intent": "search_movie", "movie_name": "Matrix", "actor_name": null, "franchise_name": null}}
- "filmes do Christopher Nolan" → {{"intent": "search_actor", "movie_name": null, "actor_name": "Christopher Nolan", "franchise_name": null}}
- "populares" → {{"intent": "popular", "movie_name": null, "actor_name": null, "franchise_name": null}}
- "filmes da jogos vorazes" → {{"intent": "search_franchise", "movie_name": null, "actor_name": null, "franchise_name": "Marvel"}}
- "filmes do star wars" → {{"intent": "search_franchise", "movie_name": null, "actor_name": null, "franchise_name": "Star Wars"}}

Retorne apenas: {{"intent": "...", "movie_name": "...", "actor_name": "...", "franchise_name": "..."}}'
                """
                
                cursor.execute(model_query)
                print("   Modelo NLP criado com sucesso usando Ollama!")
        except mysql.connector.Error as model_err:
            print(f"  Erro ao criar/verificar modelo: {model_err}")
        
        print(f"   Configuração concluída!")
        print(f"   Modelo: {OLLAMA_MODEL}")
        print(f"   URL: http://{OLLAMA_HOST}")
        print("    Agora o bot pode interpretar linguagem natural!")
        
        cursor.close()
        connection.close()
    
    except mysql.connector.Error as err:
        print(f" Erro ao criar modelo NLP: {err}")
        print("   Dica: Certifique-se de que:")
        print("   1. Ollama está rodando no host (porta 11434)")
        print(f"  2. O modelo '{OLLAMA_MODEL}' está baixado no Ollama")
        print("   3. MindsDB pode acessar http://{OLLAMA_HOST}")
        print("   4. Comando para baixar modelo: ollama pull {OLLAMA_MODEL}")



if __name__ == "__main__":
    conn = connect_mindsdb()
    if conn:
        print(" Conexão com MindsDB OK!")
        conn.close()
    
    print("\n Testando interpretação de queries:")
    
    mensagens_teste = [
        "quero ver filmes populares",
        "buscar filmes do Christopher Nolan",
        "Matrix",
        "me mostre filmes de ação",
        "quais filmes a Scarlett Johansson fez?",
        "filmes do star wars"
    ]
    
    for msg in mensagens_teste:
        resultado = interpret_user_query(msg)
        print(f"   '{msg}' → {resultado}")
