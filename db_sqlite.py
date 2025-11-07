import os
import sqlite3
from dotenv import load_dotenv

# Carrega variáveis do .env (opcional)
load_dotenv('./.env')

# Caminho do arquivo de banco
DB_PATH = os.getenv('SQLITE_DB_PATH', os.path.join(os.path.dirname(__file__), 'tweets.db'))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_text TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco SQLite: {e}")
        return False


# Inicializa a tabela ao importar
init_db()


def inserir_last_tweet(tweet_text, type):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tweets (tweet_text, type) VALUES (?, ?)",
            (tweet_text, type),
        )
        conn.commit()
        inserted_id = cur.lastrowid
        cur.close()
        conn.close()
        print(f"✅ Tweet inserido com sucesso: id={inserted_id}")
        return {"id": inserted_id, "tweet_text": tweet_text, "type": type}
    except Exception as e:
        print(f"❌ Erro ao inserir tweet no SQLite: {e}")
        return None


def listar_tweets():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, tweet_text, type, created_at FROM tweets ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        result = [dict(r) for r in rows]
        print(f"📋 Tweets encontrados: {len(result)}")
        for t in result:
            print(f"  - {t['tweet_text']}: {t['type']}")
        return result
    except Exception as e:
        print(f"❌ Erro ao listar tweets no SQLite: {e}")
        return []


def buscar_tweet(tweet_text):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, tweet_text, type, created_at FROM tweets WHERE tweet_text = ?",
            (tweet_text,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"❌ Erro ao buscar tweet no SQLite: {e}")
        return []


if __name__ == '__main__':
    ok = init_db()
    if ok:
        print(f"✅ SQLite pronto em: {DB_PATH}")
    else:
        print("❌ Falha ao preparar SQLite")