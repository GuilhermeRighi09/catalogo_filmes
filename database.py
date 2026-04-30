import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        db_url = "postgresql://neondb_owner:npg_GhIr7BMvV4Yb@ep-floral-glade-ambf853r-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"Erro crítico ao conectar ao banco Neon: {e}")
        return None


def criar_tabelas():
    sql = """
    CREATE TABLE IF NOT EXISTS filmes (
        id SERIAL PRIMARY KEY,
        titulo VARCHAR(255) NOT NULL,
        genero VARCHAR(100),
        ano DATE,
        url_capa TEXT
    );
    """
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tabela 'filmes' verificada/criada no Neon!")


if __name__ == "__main__":
    criar_tabelas()