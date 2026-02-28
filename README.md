# Gerenciador de Compromissos — Bot Telegram

Bot para gerenciamento de compromissos com lembretes automáticos via Telegram. Desenvolvido em Python com banco de dados PostgreSQL e containerizado com Docker.

---

## Funcionalidades

- Cadastro de compromissos via conversa guiada
- Lembretes automáticos com **5 dias**, **1 dia** e **1 hora** de antecedência
- Listagem de compromissos futuros
- Remoção de compromissos
- Exclusão automática de compromissos expirados

---

## Tecnologias

- [Python 3.12](https://www.python.org/)
- [python-telegram-bot](https://python-telegram-bot.org/)
- [PostgreSQL 16](https://www.postgresql.org/)
- [Docker](https://www.docker.com/) + [Docker Compose](https://docs.docker.com/compose/)

---

## 🚀 Como Executar

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado
- [Docker Compose](https://docs.docker.com/compose/install/) instalado
- Token do bot obtido via [@BotFather](https://t.me/BotFather)

### 1. Clone o repositório

```bash
git clone https://github.com/CarlosNiz/bot-telegram-compromissos.git
cd bot-telegram-compromissos
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com seus valores:

```env
TELEGRAM_TOKEN=seu_token_aqui

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=usuario
POSTGRES_PASSWORD=senha_segura
POSTGRES_DB=bot_compromissos
```

### 3. Suba os containers

```bash
docker-compose up -d --build
```

---

## 💬 Comandos do Bot

| Comando | Descrição |
|---|---|
| `/start` | Apresenta o bot e lista os comandos |
| `/agendar` | Inicia o cadastro de um novo compromisso |
| `/listar` | Exibe os compromissos futuros |
| `/deletar <ID>` | Remove um compromisso pelo ID |
| `/cancelar` | Cancela a ação em andamento |

---

## Lembretes

Os lembretes são enviados automaticamente nas seguintes antecedências:

| Lembrete | Quando dispara |
|---|---|
| 📅 5 dias | Quando faltarem 5 dias ou menos |
| ⏰ 1 dia | Quando faltarem 24 horas ou menos |
| 🔔 1 hora | Quando faltarem 60 minutos ou menos |

Cada lembrete é enviado **apenas uma vez** por compromisso.

---

## Banco de Dados

O projeto utiliza PostgreSQL com a seguinte tabela:

```sql
CREATE TABLE compromissos (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    descricao TEXT NOT NULL,
    data_hora TIMESTAMP NOT NULL,
    lembrete_5d BOOLEAN DEFAULT FALSE,
    lembrete_1d BOOLEAN DEFAULT FALSE,
    lembrete_1h BOOLEAN DEFAULT FALSE,
    criado_em TIMESTAMP DEFAULT NOW()
);
```

Compromissos expirados são **removidos automaticamente** a cada hora.

---

## Timezone

O projeto está configurado para o fuso horário `America/Sao_Paulo`. Para alterar, edite o `docker-compose.yml`:

```yaml
environment:
  - TZ=America/Sao_Paulo
```

---

## 📦 Atualizar o Bot

```bash
git pull
docker-compose up -d --build
```