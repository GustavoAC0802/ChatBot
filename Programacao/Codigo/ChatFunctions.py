import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

async def buscar_filmes_por_nome(nome):
    """Busca filmes pelo nome"""
    url = f"{BASE_URL}/search/movie?api_key={API_KEY}&language=pt-BR&query={nome}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            resultados = data.get("results", [])
            if not resultados:
                print("\nNenhum filme encontrado.")
                return []
            else:
                print(f"\nResultados para '{nome}':")
                filmes_lista = []
                for filme in resultados[:10]:
                    print(f"- {filme['title']} ({filme.get('release_date', 'sem data')})")
                    filmes_lista.append({
                        'title': filme['title'],
                        'release_date': filme.get('release_date', 'sem data'),
                        'id': filme['id']
                    })
                return filmes_lista

async def buscar_por_autor(nome):
    """Busca filmes por nome de pessoa (ator, diretor, roteirista etc.)"""
    search_url = f"{BASE_URL}/search/person?api_key={API_KEY}&language=pt-BR&query={nome}"

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as resp:
            data = await resp.json()
            pessoas = data.get("results", [])

            if not pessoas:
                print("\nNenhum autor/ator/diretor encontrado.")
                return {"pessoa": None, "filmes": []}

            pessoa = pessoas[0]
            pessoa_id = pessoa["id"]
            pessoa_nome = pessoa["name"]

            print(f"\nResultados para '{nome}': {pessoa_nome}")

            # Buscar os créditos de filmes da pessoa (atuações, direção, etc.)
            creditos_url = f"{BASE_URL}/person/{pessoa_id}/movie_credits?api_key={API_KEY}&language=pt-BR"
            async with session.get(creditos_url) as cred_resp:
                creditos_data = await cred_resp.json()
                filmes = creditos_data.get("cast", []) + creditos_data.get("crew", [])

                if not filmes:
                    print("Nenhum filme associado encontrado.")
                    return {"pessoa": pessoa_nome, "filmes": []}

                # Remove duplicatas e ordena por popularidade
                vistos = set()
                filmes_unicos = []
                for f in filmes:
                    if f["id"] not in vistos:
                        vistos.add(f["id"])
                        filmes_unicos.append(f)

                filmes_ordenados = sorted(filmes_unicos, key=lambda x: x.get("popularity", 0), reverse=True)
                filmes_exibicao = filmes_ordenados[:10]

                print("\nFilmes conhecidos:")
                filmes_lista = []
                for filme in filmes_exibicao:
                    titulo = filme.get("title") or filme.get("name", "Sem título")
                    data_lanc = filme.get("release_date", "sem data")
                    cargo = filme.get("job") or "Ator/Atriz"
                    print(f"- {titulo} ({data_lanc}) — {cargo}")
                    filmes_lista.append({
                        'title': titulo,
                        'release_date': data_lanc,
                        'id': filme['id'],
                        'job': cargo
                    })
                
                return {"pessoa": pessoa_nome, "filmes": filmes_lista}

async def buscar_filmes_populares():
    """Lista filmes populares"""
    url = f"{BASE_URL}/movie/popular?api_key={API_KEY}&language=pt-BR"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            filmes = data.get("results", [])
            print(f"\nFilmes populares:")
            filmes_lista = []
            for filme in filmes[:10]:
                print(f"- {filme['title']} ({filme.get('release_date', 'sem data')})")
                filmes_lista.append({
                    'title': filme['title'],
                    'release_date': filme.get('release_date', 'sem data'),
                    'id': filme['id']
                })
            return filmes_lista

# Exemplo rápido de uso:
async def main():
    await buscar_por_autor("Christopher Nolan")
    await buscar_filmes_por_nome("Matrix")
    await buscar_filmes_populares()

if __name__ == "__main__":
    asyncio.run(main())
