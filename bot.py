"""
🐍 PyDevBot — Telegram AI Assistant for Python & Bot Developers
Powered by Claude (Anthropic) | Built with python-telegram-bot v20+
"""

import os
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv

from telegram import (
    Update,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
import anthropic

# ─────────────────────────────────────────────
# Config & Logging
# ─────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "20"))   # messages per user
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))

if not TELEGRAM_TOKEN or not ANTHROPIC_API_KEY:
    raise EnvironmentError(
        "❌  Missing TELEGRAM_BOT_TOKEN or ANTHROPIC_API_KEY in .env"
    )

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────
# System Prompt — the bot's soul
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are PyDevBot — an elite AI assistant living inside Telegram, purpose-built for Python developers and Telegram bot engineers.

## Your Identity
- Name: PyDevBot 🐍
- Persona: Senior Python engineer with 10+ years of experience, deep Telegram Bot API expertise, and a pragmatic, no-fluff coding style.
- Tone: Friendly but precise. You talk like a senior dev pairing with a colleague — direct, helpful, occasionally witty. Never condescending.

## Your Core Expertise
1. **Python Development**
   - Modern Python (3.10+): type hints, dataclasses, async/await, match statements
   - Pythonic patterns, PEP compliance, clean architecture
   - Popular libraries: FastAPI, SQLAlchemy, Pydantic, httpx, aiohttp, pytest, etc.
   - Performance, profiling, debugging, packaging (pyproject.toml, poetry, uv)

2. **Telegram Bot Development**
   - python-telegram-bot (v20+ / PTB): Application, handlers, ConversationHandler, JobQueue
   - aiogram (v3): FSM, routers, middlewares, filters
   - Telegram Bot API: all methods, webhook vs polling, inline keyboards, inline queries, payments, Web Apps
   - Advanced patterns: rate limiting, flood control, admin panels, multi-language bots
   - Deployment: systemd, Docker, Heroku, Railway, VPS, webhooks behind nginx

3. **Bot Architecture & Best Practices**
   - State management, FSM design
   - Database integration (SQLite, PostgreSQL, MongoDB, Redis)
   - Background tasks, scheduling (APScheduler, JobQueue)
   - Error handling, logging, monitoring
   - Security: token safety, user validation, anti-spam

4. **DevOps for Bots**
   - Docker & docker-compose for bot deployment
   - CI/CD pipelines
   - Environment management, secrets, .env files

## Response Style
- **Always provide runnable code** when a code question is asked. Prefer modern, idiomatic Python.
- Format code with proper syntax highlighting (```python blocks).
- For complex topics, structure your answer: brief explanation → code → key notes.
- Point out gotchas, common mistakes, and PTB/aiogram version differences when relevant.
- If the user's question is vague, ask one clarifying question before diving in.
- Keep answers focused. Don't pad with unnecessary text.

## What You Don't Do
- You don't help with anything outside Python / bot development / related DevOps.
- If asked something unrelated, politely redirect: "I'm specialized for Python & Telegram bot dev — try asking me something in that space! 🐍"

## Special Commands You Support
Users can ask you to:
- `/snippet <topic>` — give a ready-to-use code snippet
- `/debug` — help debug their code (they paste it, you analyze)
- `/explain <concept>` — deep-dive explanation of a concept
- `/best <task>` — recommend the best library/approach for a task
- `/ptb` — python-telegram-bot specific help
- `/aiogram` — aiogram specific help
"""

# ─────────────────────────────────────────────
# In-memory conversation history store
# { user_id: [ {"role": ..., "content": ...}, ... ] }
# ─────────────────────────────────────────────
conversation_history: dict[int, list[dict]] = {}


def get_history(user_id: int) -> list[dict]:
    return conversation_history.setdefault(user_id, [])


def add_to_history(user_id: int, role: str, content: str) -> None:
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    # Keep only the last MAX_HISTORY messages
    if len(history) > MAX_HISTORY:
        conversation_history[user_id] = history[-MAX_HISTORY:]


def clear_history(user_id: int) -> None:
    conversation_history[user_id] = []


# ─────────────────────────────────────────────
# Claude API call
# ─────────────────────────────────────────────
async def ask_claude(user_id: int, user_message: str) -> str:
    add_to_history(user_id, "user", user_message)
    history = get_history(user_id)

    try:
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        assistant_reply = response.content[0].text
        add_to_history(user_id, "assistant", assistant_reply)
        return assistant_reply

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return "⚠️ API error. Please try again in a moment."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "⚠️ Something went wrong. Please try again."


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def split_message(text: str, limit: int = 4000) -> list[str]:
    """Split long messages to respect Telegram's 4096-char limit."""
    if len(text) <= limit:
        return [text]
    parts, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            parts.append(current)
            current = line + "\n"
        else:
            current += line + "\n"
    if current:
        parts.append(current)
    return parts


async def send_long_message(
    update: Update, text: str, parse_mode: Optional[str] = constants.ParseMode.MARKDOWN
) -> None:
    for part in split_message(text):
        try:
            await update.message.reply_text(part, parse_mode=parse_mode)
        except Exception:
            # Fallback: send without markdown if parsing fails
            await update.message.reply_text(part, parse_mode=None)


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("📘 PTB Help", callback_data="quick_ptb"),
            InlineKeyboardButton("⚡ aiogram Help", callback_data="quick_aiogram"),
        ],
        [
            InlineKeyboardButton("🐍 Python Tips", callback_data="quick_python"),
            InlineKeyboardButton("🚀 Deploy a Bot", callback_data="quick_deploy"),
        ],
        [
            InlineKeyboardButton("🔧 Debug My Code", callback_data="quick_debug"),
            InlineKeyboardButton("📦 Best Library?", callback_data="quick_best"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome = (
        f"👋 Hey *{user.first_name}*! I'm *PyDevBot* 🐍\n\n"
        "Your personal AI engineer for *Python* and *Telegram Bot* development.\n\n"
        "I can help you with:\n"
        "• Building Telegram bots (PTB, aiogram)\n"
        "• Python coding & architecture\n"
        "• Debugging & code reviews\n"
        "• Deployment & DevOps for bots\n\n"
        "Just ask me anything or pick a topic below 👇"
    )
    await update.message.reply_text(
        welcome, parse_mode=constants.ParseMode.MARKDOWN, reply_markup=reply_markup
    )


# ─────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🛠 *PyDevBot Commands*\n\n"
        "*/start* — Welcome & quick topics\n"
        "*/help* — Show this help message\n"
        "*/new* — Clear chat history & start fresh\n"
        "*/snippet <topic>* — Get a code snippet\n"
        "  _e.g._ `/snippet inline keyboard`\n"
        "*/debug* — Analyze & fix your code\n"
        "  _(paste your code after the command)_\n"
        "*/explain <concept>* — Deep-dive explanation\n"
        "  _e.g._ `/explain ConversationHandler`\n"
        "*/best <task>* — Best library recommendation\n"
        "  _e.g._ `/best async database for bots`\n"
        "*/ptb* — python\\-telegram\\-bot help hub\n"
        "*/aiogram* — aiogram help hub\n\n"
        "Or just *send any message* and I'll respond! 💬"
    )
    await update.message.reply_text(
        help_text, parse_mode=constants.ParseMode.MARKDOWN_V2
    )


# ─────────────────────────────────────────────
# /new — reset history
# ─────────────────────────────────────────────
async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clear_history(update.effective_user.id)
    await update.message.reply_text(
        "🔄 *Chat history cleared!* Starting fresh.\nAsk me anything 🐍",
        parse_mode=constants.ParseMode.MARKDOWN,
    )


# ─────────────────────────────────────────────
# /snippet
# ─────────────────────────────────────────────
async def snippet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    topic = " ".join(context.args) if context.args else None
    if not topic:
        await update.message.reply_text(
            "📘 Usage: `/snippet <topic>`\n_e.g._ `/snippet inline keyboard with callbacks`",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return
    prompt = f"Give me a clean, production-ready Python code snippet for: **{topic}**. Include brief inline comments."
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(update.effective_user.id, prompt)
    await send_long_message(update, reply)


# ─────────────────────────────────────────────
# /debug
# ─────────────────────────────────────────────
async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    code = " ".join(context.args) if context.args else None
    msg = update.message.text.replace("/debug", "").strip()
    code = msg or code

    if not code:
        await update.message.reply_text(
            "🔧 *Debug mode*\nPaste your code right after the command:\n"
            "`/debug <your code here>`\nOr just send the code as a message and ask me to debug it!",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return

    prompt = f"Please debug and fix this Python/Telegram bot code. Explain what was wrong and show the corrected version:\n\n```python\n{code}\n```"
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(update.effective_user.id, prompt)
    await send_long_message(update, reply)


# ─────────────────────────────────────────────
# /explain
# ─────────────────────────────────────────────
async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    concept = " ".join(context.args) if context.args else None
    if not concept:
        await update.message.reply_text(
            "📖 Usage: `/explain <concept>`\n_e.g._ `/explain ConversationHandler states`",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return
    prompt = f"Give a thorough but practical explanation of: **{concept}** in the context of Python/Telegram bot development. Include a code example."
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(update.effective_user.id, prompt)
    await send_long_message(update, reply)


# ─────────────────────────────────────────────
# /best
# ─────────────────────────────────────────────
async def best(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = " ".join(context.args) if context.args else None
    if not task:
        await update.message.reply_text(
            "🏆 Usage: `/best <task>`\n_e.g._ `/best async HTTP client for bots`",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return
    prompt = f"What is the best Python library or approach for: **{task}**? Compare top options briefly, then give a clear recommendation with a minimal example."
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(update.effective_user.id, prompt)
    await send_long_message(update, reply)


# ─────────────────────────────────────────────
# /ptb & /aiogram — quick help hubs
# ─────────────────────────────────────────────
async def ptb_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = "Give me a quick reference card for python-telegram-bot v20+: the most important classes, patterns, and gotchas a developer should know. Format it clearly."
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(update.effective_user.id, prompt)
    await send_long_message(update, reply)


async def aiogram_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = "Give me a quick reference card for aiogram v3: the most important concepts, Router/FSM/middleware patterns, and gotchas. Format it clearly with examples."
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(update.effective_user.id, prompt)
    await send_long_message(update, reply)


# ─────────────────────────────────────────────
# Inline keyboard button callbacks
# ─────────────────────────────────────────────
QUICK_PROMPTS = {
    "quick_ptb": "Give me a quick-start guide for python-telegram-bot v20+.",
    "quick_aiogram": "Give me a quick-start guide for aiogram v3.",
    "quick_python": "Give me 5 advanced Python tips that every bot developer should know.",
    "quick_deploy": "How do I deploy a Telegram bot to a VPS using Docker and webhooks? Show a full example.",
    "quick_debug": "What are the most common bugs and errors in Telegram bots and how do I fix them?",
    "quick_best": "What are the best libraries for Telegram bot development in Python in 2024?",
}


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    prompt = QUICK_PROMPTS.get(query.data)
    if not prompt:
        return
    await query.message.reply_text("⏳ Fetching answer...")
    await query.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(query.from_user.id, prompt)
    for part in split_message(reply):
        try:
            await query.message.reply_text(part, parse_mode=constants.ParseMode.MARKDOWN)
        except Exception:
            await query.message.reply_text(part, parse_mode=None)


# ─────────────────────────────────────────────
# General message handler
# ─────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.effective_user.id

    await update.message.chat.send_action(constants.ChatAction.TYPING)
    reply = await ask_claude(user_id, user_message)
    await send_long_message(update, reply)


# ─────────────────────────────────────────────
# Error handler
# ─────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error: {context.error}")


# ─────────────────────────────────────────────
# Bot setup & run
# ─────────────────────────────────────────────
async def post_init(application: Application) -> None:
    """Set bot commands in Telegram menu."""
    commands = [
        BotCommand("start", "👋 Welcome & quick topics"),
        BotCommand("help", "🛠 Show all commands"),
        BotCommand("new", "🔄 Clear chat & start fresh"),
        BotCommand("snippet", "📘 Get a code snippet"),
        BotCommand("debug", "🔧 Debug your code"),
        BotCommand("explain", "📖 Explain a concept"),
        BotCommand("best", "🏆 Best library recommendation"),
        BotCommand("ptb", "🤖 python-telegram-bot help"),
        BotCommand("aiogram", "⚡ aiogram help"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot commands registered.")


def main() -> None:
    logger.info("🚀 Starting PyDevBot...")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_chat))
    app.add_handler(CommandHandler("snippet", snippet))
    app.add_handler(CommandHandler("debug", debug))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("best", best))
    app.add_handler(CommandHandler("ptb", ptb_help))
    app.add_handler(CommandHandler("aiogram", aiogram_help))

    # Inline button callbacks
    app.add_handler(CallbackQueryHandler(button_callback))

    # General message handler (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("✅ PyDevBot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
