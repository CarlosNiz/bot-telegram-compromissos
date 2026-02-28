import psycopg2
import psycopg2.extras
import os
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )

async def criar_tabelas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS compromissos (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL,
            descricao TEXT NOT NULL,
            data_hora TIMESTAMP NOT NULL,
            lembrete_5d BOOLEAN DEFAULT FALSE,
            lembrete_1d BOOLEAN DEFAULT FALSE,
            lembrete_1h BOOLEAN DEFAULT FALSE,
            criado_em TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

async def salvar_compromisso(chat_id: int, descricao: str, data_hora: datetime):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO compromissos (chat_id, descricao, data_hora)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (chat_id, descricao, data_hora)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row[0]

async def listar_compromissos(chat_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT id, descricao, data_hora
        FROM compromissos
        WHERE chat_id = %s AND data_hora > NOW()
        ORDER BY data_hora ASC
        """,
        (chat_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

async def deletar_compromisso(compromisso_id: int, chat_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM compromissos WHERE id = %s AND chat_id = %s",
        (compromisso_id, chat_id)
    )
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted == 1

async def buscar_lembretes_pendentes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT id, chat_id, descricao, data_hora,
               lembrete_5d, lembrete_1d, lembrete_1h
        FROM compromissos
        WHERE data_hora > NOW()
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

async def marcar_lembrete(compromisso_id: int, tipo: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE compromissos SET {tipo} = TRUE WHERE id = %s",
        (compromisso_id,)
    )
    conn.commit()
    cur.close()
    conn.close()