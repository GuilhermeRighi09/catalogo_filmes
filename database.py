import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    db_url = os.environ.get("DATABASE_URL")


    if not db_url:
        db_url = "postgresql://neondb_owner:npg_GhIr7BMvV4Yb@ep-floral-glade-ambf853r-pooler.c-5.us-east-1.aws.neon.tech/neondb"


    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"Erro crítico ao conectar ao banco Neon: {e}")
        return None

def criar_tabelas():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filmes (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                genero VARCHAR(100),
                ano DATE,
                url_capa TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                senha TEXT NOT NULL
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tabelas 'filmes' e 'usuario' verificadas no Neon!")

if __name__ == "__main__":
    criar_tabelas()