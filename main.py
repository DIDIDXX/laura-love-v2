import os
import time  # Importe 'time' se quiser adicionar um atraso, mas 'apscheduler' já cuida disso
from dotenv import load_dotenv

# Importa as defs de novo.py
from novo import bom_dia, boa_tarde, boa_noite, sextou_bom_dia, sextou_boa_tarde

# Para recuperar o último texto gerado e postar
from db_sqlite import listar_tweets

# Importações do Scheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from zoneinfo import ZoneInfo

load_dotenv('./.env')


def tweetar(texto: str, dry_run: bool) -> bool:
    """Envia um tweet com Tweepy se credenciais estiverem disponíveis; em dry-run, apenas imprime."""
    if dry_run:
        print("🧪 DRY_RUN ativo: não enviando para o Twitter. Conteúdo:")
        print(texto)
        return False
    try:
        from tweepy import Client
        consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
        consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_KEY')
        access_token_secret = os.getenv('TWITTER_ACCESS_SECRET')

        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            print("⚠️ Credenciais do Twitter não encontradas em .env; não foi enviado. Conteúdo:")
            print(texto)
            return False

        client = Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        client.create_tweet(text=texto)
        print("✅ Tweet enviado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Falha ao enviar tweet: {e}")
        print("Conteúdo:")
        print(texto)
        return False


def run_action(acao: str, dry_run: bool):
    """Executa a função de geração de conteúdo e depois tenta tweetar o resultado."""
    mapping = {
        'bom_dia': bom_dia,
        'boa_tarde': boa_tarde,
        'boa_noite': boa_noite,
        'sextou_bom_dia': sextou_bom_dia,
        'sextou_boa_tarde': sextou_boa_tarde,
    }
    fn = mapping.get(acao)
    if not fn:
        print(f"❌ Ação desconhecida: {acao}")
        return
    
    print(f"Executando ação: {acao}")
    fn()  # Roda a função de 'novo.py' (que deve salvar no DB)
    
    # Busca o resultado do banco de dados para postar
    tweets = listar_tweets() or []
    if tweets:
        texto = tweets[0].get('tweet_text') or ''
        if texto:
            tweetar(texto, dry_run)
        else:
            print("⚠️ Texto do tweet está vazio, não enviado.")
    else:
        print("⚠️ Nenhum tweet encontrado no DB para enviar após a ação.")


def start_scheduler(dry_run: bool):
    """Inicia o agendador de tarefas."""
    scheduler = BlockingScheduler(timezone=ZoneInfo("America/Sao_Paulo"))
    
    print("Configurando agendamentos...")
    
    # Replicando horários do bot.py
    scheduler.add_job(lambda: run_action('bom_dia', dry_run), 'cron', hour=7, day_of_week='tue,thu')
    scheduler.add_job(lambda: run_action('bom_dia', dry_run), 'cron', hour=7, day_of_week='mon')
    scheduler.add_job(lambda: run_action('bom_dia', dry_run), 'cron', hour=7, day_of_week='wed')
    # Sexta de manhã usa sextou_bom_dia
    scheduler.add_job(lambda: run_action('sextou_bom_dia', dry_run), 'cron', hour=7, day_of_week='fri')
    # Fim de semana bom dia às 9
    scheduler.add_job(lambda: run_action('bom_dia', dry_run), 'cron', hour=9, day_of_week='sat,sun')
    # Boa noite diário 22:00
    scheduler.add_job(lambda: run_action('boa_noite', dry_run), 'cron', hour=22, day_of_week='mon,tue,wed,thu,fri,sat,sun')
    
    print("⏱️ Scheduler iniciado. Pressione Ctrl+C para parar.")
    scheduler.start()


def main():
    """Função principal que inicia o bot."""
    
    # A lógica de 'dry_run' agora vem apenas do arquivo .env
    # Se DRY_RUN não estiver no .env, o padrão é 'false' (ou seja, vai postar)
    env_dry = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    if env_dry:
        print("🧪 DRY_RUN ativo (definido no .env). Nenhum tweet será enviado.")
    else:
        print("🚀 Bot iniciando em MODO DE PRODUÇÃO. Tweets serão enviados.")
    
    # Envio imediato simples antes de iniciar o scheduler
    msg = "Estou iniciando... tweets para Laura em breve"
    print(f"💬 Envio imediato: {msg}")
    tweetar(msg, env_dry)
    
    # Inicia o scheduler
    start_scheduler(dry_run=env_dry)


if __name__ == '__main__':
    main()
