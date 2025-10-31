import asyncio
from ChatFunctions import *

async def main():
    while True:
        print("\nChatbot de Filmes - TMDB API")
        print("Comandos disponíveis:")
        print("  1 - Buscar filmes populares")
        print("  2 - Buscar por nome de filme")
        print("  3 - Buscar por nome de autor/ator/diretor")
        print("  0 - Encerrar o programa\n")

        opcao = input("> ").strip().lower()

        if opcao == "1":
            while True:
                await buscar_filmes_populares()
                repetir = input("\nDeseja realizar outra pesquisa? (S/N): ").strip().lower()
                if repetir != "s":
                    print("\n Voltando ao menu principal...\n")
                    break

        elif opcao == "2":
            while True:
                nome = input("Digite o nome do filme: ").strip()
                await buscar_filmes_por_nome(nome)
                repetir = input("\nDeseja realizar outra pesquisa? (S/N): ").strip().lower()
                if repetir != "s":
                    print("\nVoltando ao menu principal...\n")
                    break

        elif opcao == "3":
            while True:
                nome = input("Digite o nome do autor/ator/diretor: ").strip()
                await buscar_por_autor(nome)
                repetir = input("\nDeseja realizar outra pesquisa? (S/N): ").strip().lower()
                if repetir != "s":
                    print("\n🔙 Voltando ao menu principal...\n")
                    break

        elif opcao == "0" or opcao == "sair":
            print(" Encerrando o chatbot.")
            break

        else:
            print(" Opção inválida, tente novamente.")

if __name__ == "__main__":
    asyncio.run(main())
