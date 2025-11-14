import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ChatFunctions import buscar_filmes_por_nome, buscar_por_autor, buscar_filmes_populares, buscar_filmes_por_franquia
from mindsdb_client import interpret_user_query

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bem-vindo ao Movie Bot com IA!\n\n"
        "Você pode me perguntar em linguagem natural:\n\n"
        "Exemplos:\n"
        "• 'Quero ver filmes populares'\n"
        "• 'Buscar filmes do Christopher Nolan'\n"
        "• 'Me mostre filmes da Scarlett Johansson'\n"
        "• 'Matrix'\n\n"
        "Eu uso MindsDB para entender sua pergunta!"
    )


async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    try:
        await update.message.reply_text("Analisando sua pergunta com IA...")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        # Continua mesmo se falhar ao enviar a mensagem inicial
    interpretation = interpret_user_query(user_message)
    
    intent = interpretation.get('intent', 'unknown')
    params = interpretation.get('params', {})
    
    if intent == 'popular':
        filmes = await buscar_filmes_populares()
        
        if not filmes:
            await update.message.reply_text("Nenhum filme encontrado.")
            return
        
        resposta = f"Filmes Populares:\n\n"
        for filme in filmes:
            resposta += f"• {filme['title']} ({filme['release_date']})\n"
        
        await update.message.reply_text(resposta)
    
    elif intent == 'search_actor':
        actor_name = params.get('actor_name')
        # Verifica se é None, string vazia ou apenas espaços
        if not actor_name or not actor_name.strip():
            actor_name = user_message
        
        resultado = await buscar_por_autor(actor_name)
        
        if not resultado['pessoa']:
            await update.message.reply_text("Nenhum ator/diretor encontrado.")
            return
        
        if not resultado['filmes']:
            await update.message.reply_text(f"Nenhum filme encontrado para {resultado['pessoa']}.")
            return
        
        resposta = f"Filmes de {resultado['pessoa']}:\n\n"
        for filme in resultado['filmes']:
            resposta += f"• {filme['title']} ({filme['release_date']}) - {filme['job']}\n"
        
        await update.message.reply_text(resposta)
    
    elif intent == 'search_movie':
        movie_name = params.get('movie_name')
        # Verifica se é None, string vazia ou apenas espaços
        if not movie_name or not movie_name.strip():
            movie_name = user_message
        
        filmes = await buscar_filmes_por_nome(movie_name)
        
        if not filmes:
            await update.message.reply_text("Nenhum filme encontrado.")
            return
        
        resposta = f"Resultados para '{movie_name}':\n\n"
        for filme in filmes[:10]:
            resposta += f"• {filme['title']} ({filme['release_date']})\n"
        
        await update.message.reply_text(resposta)

    elif intent == 'search_franchise':
        franchise_name = params.get('franchise_name')
        # Verifica se é None, string vazia ou apenas espaços
        if not franchise_name or not franchise_name.strip():
            franchise_name = user_message
        
        filmes = await buscar_filmes_por_franquia(franchise_name)
        
        if not filmes:
            await update.message.reply_text("Nenhum filme encontrado para essa franquia.")
            return
        
        resposta = f"Filmes da franquia '{franchise_name}':\n\n"
        for filme in filmes:
            resposta += f"• {filme['title']} ({filme['release_date']})\n"
        
        await update.message.reply_text(resposta)
    
    else:
        await update.message.reply_text(
            "Desculpe, não entendi sua pergunta.\n\n"
            "Tente perguntar:\n"
            "• 'Filmes populares'\n"
            "• 'Filmes do [nome do ator]'\n"
            "• '[nome do filme]'"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trata erros do bot"""
    print(f"Erro capturado: {context.error}")
    try:
        if update and update.message:
            await update.message.reply_text("Desculpe, ocorreu um erro. Tente novamente.")
    except:
        pass  # Se não conseguir enviar mensagem de erro, apenas ignora

def main():
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN não encontrado no .env")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natural_language))
    app.add_error_handler(error_handler)  # Adiciona handler de erros
    
    print(" Bot iniciado com IA do MindsDB!")
    print("   Aguardando mensagens... Pressione Ctrl+C para parar.")
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n Interrompido pelo usuário. Encerrando o bot...")

if __name__ == "__main__":
    main()
