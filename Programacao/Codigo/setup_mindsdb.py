from mindsdb_client import connect_mindsdb, create_nlp_model, interpret_user_query

def main():
    print("   Configurando MindsDB para o Movie Bot...\n")
    
    print("   Passo 1: Testando conexão com MindsDB...")
    conn = connect_mindsdb()
    if not conn:
        print("X  Não foi possível conectar ao MindsDB")
        print("   Verifique suas credenciais no arquivo .env:")
        print("   - MINDSDB_HOST")
        print("   - MINDSDB_PORT")
        print("   - MINDSDB_USER")
        print("   - MINDSDB_PASSWORD")
        return
    
    print("  Conexão OK!\n")
    conn.close()
    
    print("   Passo 2: Criando/verificando modelo de interpretação NLP...")
    print("   (Isso pode levar alguns segundos...)")
    
    create_nlp_model(force_recreate=False)
    
    print("\n")
    
    print("   Passo 3: Testando interpretação de queries...")
    print("   (Aguarde, primeira query pode ser lenta...)\n")
    
    mensagens_teste = [
        "quero ver filmes populares",
        "Matrix"
    ]
    
    for msg in mensagens_teste:
        try:
            print(f"   Testando: '{msg}'...", end=" ")
            resultado = interpret_user_query(msg)
            print(f"✓")
            print(f"      Intent: {resultado['intent']}")
            if resultado['params'].get('movie_name'):
                print(f"      Movie: {resultado['params']['movie_name']}")
            if resultado['params'].get('actor_name'):
                print(f"      Actor: {resultado['params']['actor_name']}")
            print()
        except KeyboardInterrupt:
            print("\n\n! Teste interrompido pelo usuário")
            break
        except Exception as e:
            print(f"X")
            print(f"      Erro: {e}")
            print()
    
    print("   Configuração completa!")
    print("\n Agora você pode executar o bot:")
    print("   python telegram_bot.py")

if __name__ == "__main__":
    main()
