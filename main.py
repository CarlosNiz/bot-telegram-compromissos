import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from database import criar_tabelas, salvar_compromisso, listar_compromissos, deletar_compromisso, buscar_lembretes_pendentes, marcar_lembrete, get_connection

load_dotenv()

DESCRICAO, DATA, HORA = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Olá! Eu sou seu bot de compromissos.\n\n"
        "Comandos disponíveis:\n"
        "/agendar — Criar novo compromisso\n"
        "/listar — Ver seus compromissos\n"
        "/deletar — Remover um compromisso\n"
        "/cancelar — Cancelar ação atual"
    )

async def agendar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Qual é a descrição do compromisso?",
        reply_markup=ReplyKeyboardRemove()
    )
    return DESCRICAO

async def receber_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["descricao"] = update.message.text
    await update.message.reply_text(
        "📅 Qual é a data do compromisso?\n"
        "Formato: DD/MM/AAAA\n"
        "Exemplo: 25/03/2025"
    )
    return DATA

async def receber_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        datetime.strptime(texto, "%d/%m/%Y")
        context.user_data["data"] = texto
    except ValueError:
        await update.message.reply_text(
            "❌ Data inválida. Use o formato DD/MM/AAAA\nExemplo: 25/03/2025"
        )
        return DATA

    await update.message.reply_text(
        "🕐 Qual é o horário?\n"
        "Formato: HH:MM\n"
        "Exemplo: 14:30"
    )
    return HORA

async def receber_hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        data_hora = datetime.strptime(
            f"{context.user_data['data']} {texto}",
            "%d/%m/%Y %H:%M"
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Horário inválido. Use o formato HH:MM\nExemplo: 14:30"
        )
        return HORA

    if data_hora < datetime.now():
        await update.message.reply_text(
            "❌ Essa data já passou. Por favor, informe uma data futura."
        )
        return HORA

    chat_id = update.message.chat_id
    descricao = context.user_data["descricao"]
    await salvar_compromisso(chat_id, descricao, data_hora)

    await update.message.reply_text(
        f"✅ *Compromisso agendado!*\n\n"
        f"📌 {descricao}\n"
        f"🕐 {data_hora.strftime('%d/%m/%Y às %H:%M')}\n\n"
        f"Você receberá lembretes com 5 dias, 1 dia e 1 hora de antecedência.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    compromissos = await listar_compromissos(chat_id)

    if not compromissos:
        await update.message.reply_text("📭 Você não tem compromissos agendados.")
        return

    texto = "📋 *Seus compromissos:*\n\n"
    for c in compromissos:
        texto += (
            f"🔹 *ID {c['id']}*\n"
            f"📌 {c['descricao']}\n"
            f"🕐 {c['data_hora'].strftime('%d/%m/%Y às %H:%M')}\n\n"
        )

    await update.message.reply_text(texto, parse_mode="Markdown")

async def deletar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "ℹ️ Use: /deletar <ID>\nExemplo: /deletar 3\n\n"
            "Consulte os IDs com /listar"
        )
        return

    try:
        compromisso_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")
        return

    chat_id = update.message.chat_id
    sucesso = await deletar_compromisso(compromisso_id, chat_id)

    if sucesso:
        await update.message.reply_text(f"🗑️ Compromisso #{compromisso_id} removido.")
    else:
        await update.message.reply_text("❌ Compromisso não encontrado.")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Ação cancelada.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def verificar_lembretes(context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now()
    try:
        compromissos = await buscar_lembretes_pendentes()
        for c in compromissos:
            diferenca = c["data_hora"] - agora

            if not c["lembrete_5d"] and diferenca <= timedelta(days=5):
                await context.bot.send_message(
                    chat_id=c["chat_id"],
                    text=(
                        f"📅 *Lembrete — 5 dias*\n\n"
                        f"Você tem um compromisso em breve:\n"
                        f"📌 {c['descricao']}\n"
                        f"🕐 {c['data_hora'].strftime('%d/%m/%Y às %H:%M')}"
                    ),
                    parse_mode="Markdown"
                )
                await marcar_lembrete(c["id"], "lembrete_5d")

            if not c["lembrete_1d"] and diferenca <= timedelta(days=1):
                await context.bot.send_message(
                    chat_id=c["chat_id"],
                    text=(
                        f"⏰ *Lembrete — 1 dia*\n\n"
                        f"Seu compromisso é *amanhã*:\n"
                        f"📌 {c['descricao']}\n"
                        f"🕐 {c['data_hora'].strftime('%d/%m/%Y às %H:%M')}"
                    ),
                    parse_mode="Markdown"
                )
                await marcar_lembrete(c["id"], "lembrete_1d")

            if not c["lembrete_1h"] and diferenca <= timedelta(hours=1):
                await context.bot.send_message(
                    chat_id=c["chat_id"],
                    text=(
                        f"🔔 *Lembrete — 1 hora*\n\n"
                        f"Seu compromisso começa em *1 hora*:\n"
                        f"📌 {c['descricao']}\n"
                        f"🕐 {c['data_hora'].strftime('%d/%m/%Y às %H:%M')}"
                    ),
                    parse_mode="Markdown"
                )
                await marcar_lembrete(c["id"], "lembrete_1h")

    except Exception as e:
        print(f"[Scheduler] Erro: {e}")

async def limpar_compromissos_passados(context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM compromissos WHERE data_hora < NOW()")
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        if deleted > 0:
            print(f"[Limpeza] {deleted} compromisso(s) expirado(s) removido(s).")
    except Exception as e:
        print(f"[Limpeza] Erro: {e}")

async def post_init(app):
    await criar_tabelas()
    app.job_queue.run_repeating(verificar_lembretes, interval=60, first=10)
    app.job_queue.run_repeating(limpar_compromissos_passados, interval=3600, first=60)

def main():
    app = (
        ApplicationBuilder()
        .token(os.getenv("TELEGRAM_TOKEN"))
        .post_init(post_init)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("agendar", agendar_inicio)],
        states={
            DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao)],
            DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_data)],
            HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_hora)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("listar", listar))
    app.add_handler(CommandHandler("deletar", deletar))

    app.run_polling()

if __name__ == "__main__":
    main()