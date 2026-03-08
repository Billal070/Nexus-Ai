"""
knowledge.py — PyDevBot's built-in expert knowledge base
All responses are hand-crafted for Python & Telegram bot developers.
"""

# ─────────────────────────────────────────────────────────────
# SNIPPETS  — /snippet command  (keyword → code block)
# ─────────────────────────────────────────────────────────────
SNIPPETS = {
    "inline_keyboard": (
        "📘 *Inline Keyboard with Callbacks*",
        """```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

async def show_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data="yes"),
         InlineKeyboardButton("❌ No",  callback_data="no")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")],
    ]
    await update.message.reply_text(
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()          # removes the loading spinner
    data = query.data

    if data == "yes":
        await query.edit_message_text("You chose ✅ Yes!")
    elif data == "no":
        await query.edit_message_text("You chose ❌ No!")

# Register:
# app.add_handler(CallbackQueryHandler(button_handler))
```"""
    ),

    "conversation_handler": (
        "📘 *ConversationHandler (multi-step form)*",
        """```python
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

NAME, AGE = range(2)   # States

async def start(update, context):
    await update.message.reply_text("What's your name?")
    return NAME

async def get_name(update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("How old are you?")
    return AGE

async def get_age(update, context):
    name = context.user_data["name"]
    age  = update.message.text
    await update.message.reply_text(f"Got it! {name}, {age} years old.")
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        AGE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
# app.add_handler(conv)
```"""
    ),

    "send_photo": (
        "📘 *Send Photo / File*",
        """```python
# Send a photo from URL
await context.bot.send_photo(
    chat_id=update.effective_chat.id,
    photo="https://example.com/image.png",
    caption="Here's your image 🖼"
)

# Send a local file
with open("image.png", "rb") as f:
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)

# Send a document
with open("report.pdf", "rb") as f:
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=f,
        caption="Your report 📄"
    )
```"""
    ),

    "schedule_job": (
        "📘 *Schedule a Repeating Job*",
        """```python
from telegram.ext import Application
from datetime import datetime
import pytz

async def daily_message(context):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🌅 Good morning! Daily reminder."
    )

async def set_timer(update, context):
    chat_id = update.effective_chat.id
    # Remove existing job for this chat (if any)
    current = context.chat_data.get("job")
    if current:
        current.schedule_removal()

    # Run every day at 9:00 AM UTC
    job = context.job_queue.run_daily(
        daily_message,
        time=datetime.time(9, 0, tzinfo=pytz.utc),
        chat_id=chat_id,
        name=str(chat_id),
    )
    context.chat_data["job"] = job
    await update.message.reply_text("⏰ Daily reminder set for 9:00 AM UTC!")
```"""
    ),

    "webhook": (
        "📘 *Webhook Setup (FastAPI)*",
        """```python
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://yourapp.railway.app

app_tg = Application.builder().token(TOKEN).build()
app    = FastAPI()

@app.on_event("startup")
async def startup():
    await app_tg.initialize()
    await app_tg.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    await app_tg.start()

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app_tg.bot)
    await app_tg.process_update(update)
    return {"ok": True}

@app.on_event("shutdown")
async def shutdown():
    await app_tg.stop()
```"""
    ),

    "sqlite": (
        "📘 *SQLite Database with aiosqlite*",
        """```python
import aiosqlite

DB = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY,
                username TEXT,
                joined   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_user(user_id: int, username: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()
```"""
    ),

    "middleware_aiogram": (
        "📘 *Middleware in aiogram v3*",
        """```python
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Any, Awaitable

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 1.0):
        self.limit = limit
        self.users: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any]
    ) -> Any:
        import time
        uid = event.from_user.id
        now = time.time()

        if uid in self.users and now - self.users[uid] < self.limit:
            await event.answer("⚠️ Slow down! Too many messages.")
            return

        self.users[uid] = now
        return await handler(event, data)

# Register:
# dp.message.middleware(ThrottlingMiddleware(limit=1.0))
```"""
    ),

    "fsm_aiogram": (
        "📘 *FSM (Finite State Machine) in aiogram v3*",
        """```python
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

class Form(StatesGroup):
    name = State()
    age  = State()

@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await msg.answer("What's your name?")
    await state.set_state(Form.name)

@router.message(Form.name)
async def process_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("How old are you?")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(msg: Message, state: FSMContext):
    data = await state.get_data()
    await msg.answer(f"Hello {data['name']}, age {msg.text}!")
    await state.clear()
```"""
    ),

    "env": (
        "📘 *Loading .env Variables*",
        """```python
# Install: pip install python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env file

TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
DB_URL  = os.getenv("DATABASE_URL", "sqlite:///bot.db")
DEBUG   = os.getenv("DEBUG", "false").lower() == "true"

# .env file looks like:
# TELEGRAM_BOT_TOKEN=1234567890:AAFxxx...
# DATABASE_URL=postgresql://user:pass@host/db
# DEBUG=true
```"""
    ),

    "error_handler": (
        "📘 *Global Error Handler*",
        """```python
import traceback
import logging

logger = logging.getLogger(__name__)

async def error_handler(update, context):
    # Log the full traceback
    logger.error("Exception:", exc_info=context.error)
    tb = "".join(traceback.format_exception(
        type(context.error), context.error, context.error.__traceback__
    ))

    # Notify the user gracefully
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something went wrong. Please try again later."
        )

    # Optionally: notify admin
    ADMIN_ID = 123456789  # your Telegram user ID
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"⚠️ Error:\\n```\\n{tb[:3000]}\\n```",
        parse_mode="Markdown"
    )

# Register:
# app.add_error_handler(error_handler)
```"""
    ),

    "pagination": (
        "📘 *Paginated Results with Inline Buttons*",
        """```python
ITEMS_PER_PAGE = 5

async def show_page(update, context, items: list, page: int = 0):
    start = page * ITEMS_PER_PAGE
    chunk = items[start : start + ITEMS_PER_PAGE]
    text  = "\\n".join(f"{i+1+start}. {item}" for i, item in enumerate(chunk))

    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page-1}"))
    if start + ITEMS_PER_PAGE < len(items):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))
    if nav:
        buttons.append(nav)

    await update.message.reply_text(
        text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )

# In callback handler:
# if query.data.startswith("page_"):
#     page = int(query.data.split("_")[1])
#     await show_page(update, context, my_items, page)
```"""
    ),

    "broadcast": (
        "📘 *Broadcast Message to All Users*",
        """```python
import asyncio

async def broadcast(update, context):
    # Only allow admin
    if update.effective_user.id != ADMIN_ID:
        return

    text    = " ".join(context.args)
    user_ids = await get_all_user_ids()   # your DB function
    success, failed = 0, 0

    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)   # respect Telegram rate limits

    await update.message.reply_text(
        f"📢 Broadcast done!\\n✅ Sent: {success}\\n❌ Failed: {failed}"
    )
```"""
    ),

    "decorator": (
        "📘 *Admin-only Decorator*",
        """```python
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

ADMIN_IDS = {123456789, 987654321}   # your admin user IDs

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Admins only.")
            return
        return await func(update, context)
    return wrapper

# Usage:
@admin_only
async def admin_panel(update, context):
    await update.message.reply_text("👑 Welcome to admin panel!")
```"""
    ),

    "typing_action": (
        "📘 *Show Typing... Action*",
        """```python
from telegram import constants

async def slow_command(update, context):
    # Show "typing..." while processing
    await update.message.chat.send_action(constants.ChatAction.TYPING)

    result = await do_heavy_work()   # your async task

    await update.message.reply_text(result)

# Other chat actions:
# ChatAction.UPLOAD_PHOTO
# ChatAction.UPLOAD_DOCUMENT
# ChatAction.RECORD_VOICE
# ChatAction.FIND_LOCATION
```"""
    ),

    "inline_query": (
        "📘 *Inline Query Handler*",
        """```python
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
import uuid

async def inline_query(update, context):
    query = update.inline_query.query.strip()
    if not query:
        return

    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Send: {query}",
            input_message_content=InputTextMessageContent(query),
            description="Tap to send this message"
        )
    ]
    await update.inline_query.answer(results, cache_time=10)

# Register:
# app.add_handler(InlineQueryHandler(inline_query))
# Also: enable inline mode in @BotFather with /setinline
```"""
    ),
}

# ─────────────────────────────────────────────────────────────
# EXPLANATIONS — /explain command
# ─────────────────────────────────────────────────────────────
EXPLANATIONS = {
    "conversationhandler": """🧠 *ConversationHandler Explained*

A `ConversationHandler` lets your bot have *multi-step conversations* — like a form wizard.

*How it works:*
• You define *states* (e.g. `NAME = 0`, `AGE = 1`)
• Each state has handlers that wait for input
• Handlers return the next state (or `END` to finish)
• `entry_points` — what triggers the conversation (e.g. `/start`)
• `fallbacks` — handles `/cancel` or unexpected input

*Key gotcha:*
Don't use `CommandHandler` inside states unless you want commands to work mid-conversation. Use `filters.TEXT & ~filters.COMMAND` to block commands.

Use `/snippet conversation_handler` to see a full example.""",

    "webhook": """🌐 *Polling vs Webhook*

*Polling* — bot constantly asks Telegram "any new messages?"
• Simple to set up
• Works on any machine
• Slightly higher latency
• Use for development / small bots

*Webhook* — Telegram pushes updates directly to your server
• Needs a public HTTPS URL
• Lower latency, more efficient
• Required for high-traffic bots
• Use for production on Railway/VPS

*Rule of thumb:*
Dev → polling. Production with real traffic → webhook.

Use `/snippet webhook` to see FastAPI webhook setup.""",

    "fsm": """⚙️ *FSM (Finite State Machine)*

FSM is how you manage *what state a user is currently in* during a conversation.

In *python-telegram-bot*: `ConversationHandler` handles FSM.
In *aiogram v3*: built-in `StatesGroup` + `FSMContext`.

*Why use FSM?*
Without it, your bot has no memory between messages. With FSM, you know if user is in step 1, step 2, or done.

*aiogram v3 FSM storage options:*
• `MemoryStorage()` — in-memory, lost on restart
• `RedisStorage()` — persistent, survives restarts
• `MongoStorage()` — MongoDB-backed

Use `/snippet fsm_aiogram` to see full aiogram v3 FSM example.""",

    "middleware": """🔧 *Middleware in aiogram v3*

Middleware intercepts *every update* before it hits your handler.

*Use cases:*
• Throttling / rate limiting
• Logging all messages
• Injecting database sessions
• Checking if user is banned
• Translating messages

*Order matters:* middleware runs in the order you register it.

```python
# Outer middleware (runs before & after handler)
dp.update.outer_middleware(LoggingMiddleware())

# Inner middleware (runs only for matched handlers)
dp.message.middleware(ThrottlingMiddleware())
```

Use `/snippet middleware_aiogram` to see a throttling example.""",

    "jobqueue": """⏰ *Job Queue (Scheduling)*

PTB's built-in scheduler to run tasks on a timer.

*Types:*
• `run_once(callback, when)` — run once after X seconds
• `run_repeating(callback, interval)` — run every X seconds
• `run_daily(callback, time)` — run every day at HH:MM
• `run_monthly(callback, day, time)` — monthly

*Enable it:*
```python
app = Application.builder().token(TOKEN).build()
# JobQueue is auto-enabled ✅
```

*Pass data to job:*
```python
job = context.job_queue.run_once(
    my_func, when=10,
    data={"key": "value"},
    chat_id=chat_id
)
# In callback: context.job.data["key"]
```

Use `/snippet schedule_job` for a daily reminder example.""",

    "inline_keyboard": """⌨️ *Inline Keyboards Explained*

Inline keyboards are buttons that appear *below a message* (not the chat input).

*Button types:*
• `callback_data` — triggers `CallbackQueryHandler`
• `url` — opens a URL
• `switch_inline_query` — opens inline mode
• `web_app` — opens a Telegram Web App

*Key rule:* Always call `await query.answer()` first in your callback handler — this removes the loading spinner from the button.

*Edit message after button press:*
```python
await query.edit_message_text("New text!")
await query.edit_message_reply_markup(new_keyboard)
```

Use `/snippet inline_keyboard` for a full example.""",

    "filters": """🔍 *Filters in PTB*

Filters decide which messages a handler responds to.

*Common filters:*
```python
filters.TEXT            # any text message
filters.COMMAND         # messages starting with /
filters.PHOTO           # photo messages
filters.Document.ALL    # any file/document
filters.AUDIO           # audio files
filters.Regex(r"^\\d+$") # matches regex
filters.User(user_ids=[123, 456])  # specific users
filters.Chat(chat_ids=[-100xxx])   # specific chats
```

*Combine with operators:*
```python
filters.TEXT & ~filters.COMMAND    # text but NOT a command
filters.PHOTO | filters.VIDEO      # photo OR video
```""",

    "context_user_data": """💾 *context.user_data / chat_data / bot_data*

PTB gives you free dictionaries to store temporary data.

```python
# Per-user storage
context.user_data["score"] = 10
context.user_data.get("score", 0)

# Per-chat storage
context.chat_data["topic"] = "python"

# Global bot storage
context.bot_data["total_users"] = 500
```

⚠️ This data is *in-memory only* — it's lost when bot restarts.
For persistence, use PTB's `PicklePersistence` or a real database.

```python
from telegram.ext import PicklePersistence
persistence = PicklePersistence(filepath="bot_data.pkl")
app = Application.builder().token(TOKEN).persistence(persistence).build()
```""",

    "rate_limiting": """🚦 *Rate Limiting Your Bot*

Telegram limits: 30 messages/sec globally, 1 message/sec per chat.

*Simple per-user throttle:*
```python
from collections import defaultdict
import time

last_msg = defaultdict(float)
LIMIT = 1.0  # seconds between messages

async def handle(update, context):
    uid = update.effective_user.id
    now = time.time()
    if now - last_msg[uid] < LIMIT:
        await update.message.reply_text("⚠️ Please slow down!")
        return
    last_msg[uid] = now
    # ... your handler logic
```

For aiogram, use middleware — see `/snippet middleware_aiogram`.""",
}

# ─────────────────────────────────────────────────────────────
# BEST LIBRARY recommendations
# ─────────────────────────────────────────────────────────────
BEST = {
    "database": """🏆 *Best Database for Telegram Bots*

*Small bots (< 10k users):*
→ **SQLite + aiosqlite** — zero setup, file-based, fully async
`pip install aiosqlite`

*Medium bots (10k–100k users):*
→ **PostgreSQL + asyncpg** or **SQLAlchemy 2.0 (async)**
`pip install asyncpg sqlalchemy[asyncio]`

*Need caching / fast reads:*
→ **Redis** (via `redis.asyncio`)
Great for sessions, rate limits, leaderboards.

*Flexible schema / rapid dev:*
→ **MongoDB + motor** (async MongoDB driver)

*Recommendation for beginners:* Start with SQLite + aiosqlite. Migrate to PostgreSQL when needed. Use `/snippet sqlite` for a ready example.""",

    "http": """🏆 *Best Async HTTP Client*

→ **httpx** ✅ (recommended)
`pip install httpx`
```python
import httpx
async with httpx.AsyncClient() as client:
    r = await client.get("https://api.example.com/data")
    data = r.json()
```

→ **aiohttp** — also great, more verbose
→ **requests** — ❌ don't use in async bots, it blocks the event loop

*Rule:* Never use `requests` inside a PTB/aiogram handler. Always use async HTTP clients.""",

    "scheduler": """🏆 *Best Scheduler for Bots*

*If using python-telegram-bot:*
→ Built-in **JobQueue** — best choice, already integrated
Use `/explain jobqueue` for details.

*If using aiogram or standalone:*
→ **APScheduler** — powerful, flexible
`pip install apscheduler`
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(my_task, "interval", seconds=60)
scheduler.start()
```

*Simple one-off delays:*
→ `await asyncio.sleep(seconds)` inside a task""",

    "deployment": """🏆 *Best Deployment Platform for Bots*

*Free tier:*
→ **Railway** ✅ — $5/month free credit, Docker support, easy GitHub deploy
→ **Render** — free tier (spins down after 15min inactivity — bad for bots)
→ **Fly.io** — generous free tier, good for small bots

*Paid (cheap):*
→ **DigitalOcean / Hetzner VPS** — $4-6/month, full control
→ **Oracle Cloud Free Tier** — actually free forever, 2 VMs

*Avoid for bots:*
→ Vercel / Netlify — serverless, not suitable for long-running polling bots

*Best for beginners:* Railway (what you're using!)""",

    "bot_framework": """🏆 *PTB vs aiogram — Which to Choose?*

*python-telegram-bot (PTB):*
✅ Easier to learn, great docs
✅ Built-in JobQueue, ConversationHandler
✅ Official-style, close to Telegram Bot API
❌ Slightly less async-native

*aiogram v3:*
✅ Fully async from the ground up
✅ Powerful middleware, FSM, filters system
✅ Better for large, complex bots
❌ Steeper learning curve

*Verdict:*
→ **Beginner / medium bot** → python-telegram-bot
→ **Complex / high-traffic bot** → aiogram v3""",
}

# ─────────────────────────────────────────────────────────────
# KEYWORD RESPONSE MAP — for smart chat detection
# Each entry: list of keywords → (title, response)
# ─────────────────────────────────────────────────────────────
KEYWORD_RESPONSES = [
    # ── Greetings ──
    (["hello", "hi", "hey", "sup", "what's up", "yo"],
     "👋 Hey! I'm *PyDevBot* 🐍\nAsk me anything about Python or Telegram bot development!\nOr type /help to see all commands."),

    # ── PTB basics ──
    (["python-telegram-bot", "ptb", "python telegram bot"],
     "🤖 *python-telegram-bot (PTB)*\n\nCurrent major version: *v21*\n\n*Install:*\n```\npip install python-telegram-bot\n```\n\n*Minimal bot:*\n```python\nfrom telegram.ext import Application, CommandHandler\n\nasync def start(update, context):\n    await update.message.reply_text('Hello!')\n\napp = Application.builder().token('TOKEN').build()\napp.add_handler(CommandHandler('start', start))\napp.run_polling()\n```\n\nType `/ptb` for a full reference card."),

    # ── aiogram ──
    (["aiogram"],
     "⚡ *aiogram v3*\n\n*Install:*\n```\npip install aiogram\n```\n\n*Minimal bot:*\n```python\nfrom aiogram import Bot, Dispatcher\nfrom aiogram.filters import Command\nfrom aiogram.types import Message\nimport asyncio\n\nbot = Bot(token='TOKEN')\ndp  = Dispatcher()\n\n@dp.message(Command('start'))\nasync def start(msg: Message):\n    await msg.answer('Hello!')\n\nasync def main():\n    await dp.start_polling(bot)\n\nasyncio.run(main())\n```\n\nType `/aiogram` for full reference."),

    # ── Errors ──
    (["error", "exception", "traceback", "crash", "bug"],
     "🔧 *Debugging Tips*\n\n1️⃣ Add a global error handler — `/snippet error_handler`\n2️⃣ Enable debug logging:\n```python\nimport logging\nlogging.basicConfig(level=logging.DEBUG)\n```\n3️⃣ Most common PTB errors:\n• `Conflict` — two bot instances running. Kill one.\n• `Unauthorized` — wrong token. Check .env\n• `BadRequest: Message is not modified` — you're editing a message with the same text. Add a check.\n• `RetryAfter` — you're sending too fast. Add `asyncio.sleep()`\n\nPaste your traceback and I'll help identify it!"),

    # ── Deploy / Railway ──
    (["deploy", "railway", "hosting", "vps", "server", "production"],
     "🚀 *Deploying Your Bot*\n\n*Railway (recommended for beginners):*\n1. Push code to GitHub\n2. Connect repo on railway.app\n3. Add env vars: `TELEGRAM_BOT_TOKEN`\n4. Railway auto-builds with your Dockerfile\n\n*VPS (more control):*\n```bash\n# Install Docker, then:\ndocker-compose up -d\n```\n\n*Polling vs Webhook:*\n• Polling — simple, works everywhere\n• Webhook — needs HTTPS URL, more efficient\n\nType `/explain webhook` for details."),

    # ── Webhook ──
    (["webhook"],
     "🌐 *Webhook Setup*\n\nUse `/explain webhook` for polling vs webhook comparison.\nUse `/snippet webhook` for a FastAPI webhook example."),

    # ── Database ──
    (["database", "sqlite", "postgresql", "postgres", "mongodb", "redis", "db", "store data", "save data"],
     "🗄 *Database Options*\n\nType `/best database` for full comparison.\nType `/snippet sqlite` for a ready-to-use async SQLite example.\n\n*Quick pick:*\n• Small bot → SQLite + aiosqlite ✅\n• Medium/large → PostgreSQL + asyncpg\n• Caching → Redis"),

    # ── Async ──
    (["async", "await", "asyncio", "coroutine", "event loop"],
     "⚡ *Async Python Tips*\n\n```python\nimport asyncio\n\n# Run multiple tasks at once:\nresults = await asyncio.gather(\n    fetch_data(),\n    send_notification(),\n    update_database(),\n)\n\n# Run with timeout:\ntry:\n    result = await asyncio.wait_for(slow_task(), timeout=5.0)\nexcept asyncio.TimeoutError:\n    print('Task timed out!')\n\n# Sleep without blocking:\nawait asyncio.sleep(1)\n```\n\n⚠️ Never use `time.sleep()` or `requests` in async handlers — they block the event loop!"),

    # ── Inline keyboard ──
    (["inline keyboard", "inline button", "callback", "callback_data", "callbackquery"],
     "⌨️ *Inline Keyboards*\n\nUse `/snippet inline_keyboard` for full example.\nUse `/explain inline_keyboard` for deep explanation."),

    # ── ConversationHandler ──
    (["conversation", "states", "multi-step", "conversationhandler", "wizard"],
     "🧠 *ConversationHandler*\n\nUse `/snippet conversation_handler` for full example.\nUse `/explain conversationhandler` for deep explanation."),

    # ── Send media ──
    (["send photo", "send image", "send file", "send document", "send video", "send audio"],
     "📸 *Sending Media*\n\nUse `/snippet send_photo` for a full example.\n\n*Quick reference:*\n```python\n# Photo\nawait context.bot.send_photo(chat_id, photo='URL_or_file_id')\n# Document\nawait context.bot.send_document(chat_id, document=open('f.pdf','rb'))\n# Video\nawait context.bot.send_video(chat_id, video='file_id')\n# Audio\nawait context.bot.send_audio(chat_id, audio='file_id')\n# Sticker\nawait context.bot.send_sticker(chat_id, sticker='file_id')\n```"),

    # ── Environment / .env ──
    (["env", ".env", "environment", "dotenv", "secret", "token", "api key"],
     "🔐 *Managing Secrets Safely*\n\nUse `/snippet env` for full .env example.\n\n*Never hardcode tokens in code!*\n```python\nimport os\nfrom dotenv import load_dotenv\nload_dotenv()\nTOKEN = os.getenv('TELEGRAM_BOT_TOKEN')\n```\n\n⚠️ Always add `.env` to `.gitignore` before pushing to GitHub!"),

    # ── Rate limiting ──
    (["rate limit", "flood", "spam", "throttle", "too many"],
     "🚦 *Rate Limiting*\n\nUse `/explain rate_limiting` for full explanation and code.\n\n*Telegram limits:*\n• 30 messages/sec globally\n• 1 message/sec per chat\n• Broadcast to 100+ users: add `asyncio.sleep(0.05)` between sends"),

    # ── Filters ──
    (["filter", "filters.text", "filters.command", "filters.photo"],
     "🔍 *Filters*\n\nUse `/explain filters` for full filter reference.\n\n*Most used:*\n```python\nfilters.TEXT & ~filters.COMMAND   # text, not a command\nfilters.PHOTO                      # photo messages\nfilters.Regex(r'^\\d+$')            # regex match\nfilters.User(user_ids=[123])       # specific user\n```"),

    # ── Schedule / timer ──
    (["schedule", "timer", "cron", "daily", "interval", "repeat", "job"],
     "⏰ *Scheduling Jobs*\n\nUse `/snippet schedule_job` for full example.\nUse `/explain jobqueue` for deep explanation.\n\n*Quick reference:*\n```python\n# Run once after 10 seconds\ncontext.job_queue.run_once(callback, when=10)\n# Repeat every 60 seconds\ncontext.job_queue.run_repeating(callback, interval=60)\n# Every day at 9 AM UTC\ncontext.job_queue.run_daily(callback, time=datetime.time(9, 0))\n```"),

    # ── Broadcast ──
    (["broadcast", "send all", "send to all", "mass message", "notify all"],
     "📢 *Broadcast to All Users*\n\nUse `/snippet broadcast` for full admin broadcast example.\n\n⚠️ Key rule: add `await asyncio.sleep(0.05)` between sends to avoid hitting Telegram rate limits."),

    # ── Admin ──
    (["admin", "admin only", "restrict", "permission"],
     "👑 *Admin-only Commands*\n\nUse `/snippet decorator` for an `@admin_only` decorator.\n\n*Quick check:*\n```python\nADMIN_ID = 123456789\nasync def admin_cmd(update, context):\n    if update.effective_user.id != ADMIN_ID:\n        await update.message.reply_text('⛔ Admins only.')\n        return\n    # ... admin logic\n```"),

    # ── Pagination ──
    (["paginate", "pagination", "pages", "page", "next page"],
     "📄 *Pagination*\n\nUse `/snippet pagination` for a full paginated list example with Prev/Next buttons."),

    # ── Inline query ──
    (["inline query", "inline mode", "setinline", "@bot"],
     "🔎 *Inline Mode*\n\nUse `/snippet inline_query` for full inline query handler example.\n\nDon't forget to enable inline mode in *@BotFather* → `/setinline`"),

    # ── Python tips ──
    (["python tip", "best practice", "pythonic", "clean code", "pep8", "type hint"],
     "🐍 *Pythonic Tips*\n\n```python\n# Type hints (always use them!)\nasync def greet(name: str) -> str:\n    return f'Hello, {name}'\n\n# Dataclasses over dicts\nfrom dataclasses import dataclass\n@dataclass\nclass User:\n    id: int\n    name: str\n    score: int = 0\n\n# Walrus operator\nif (n := len(data)) > 10:\n    print(f'Too many items: {n}')\n\n# f-string formatting\nprice = 1234.5\nprint(f'Price: {price:,.2f}')   # Price: 1,234.50\n\n# Pathlib over os.path\nfrom pathlib import Path\nconfig = Path('config') / 'settings.json'\n```"),

    # ── Docker ──
    (["docker", "dockerfile", "container", "docker-compose"],
     "🐳 *Docker for Bots*\n\n*Minimal Dockerfile:*\n```dockerfile\nFROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY bot.py .\nCMD [\"python\", \"bot.py\"]\n```\n\n*Build & run:*\n```bash\ndocker build -t mybot .\ndocker run -d --env-file .env mybot\n```\n\nYour Railway deployment already uses this Dockerfile!"),

    # ── BotFather ──
    (["botfather", "create bot", "new bot", "bot token"],
     "🤖 *Creating a Bot with BotFather*\n\n1. Open Telegram → search `@BotFather`\n2. Send `/newbot`\n3. Choose a display name (e.g. `My Dev Bot`)\n4. Choose a username ending in `bot` (e.g. `mydevbot`)\n5. Copy the token: `1234567890:AAFxxx...`\n6. Store it in your `.env` file as `TELEGRAM_BOT_TOKEN`\n\n*Useful BotFather commands:*\n• `/setdescription` — bot description\n• `/setuserpic` — bot profile photo\n• `/setcommands` — visible command menu\n• `/setinline` — enable inline mode"),

    # ── Getting user info ──
    (["get user", "user id", "username", "user info", "effective_user"],
     "👤 *Getting User Info*\n\n```python\nasync def handler(update, context):\n    user = update.effective_user\n    print(user.id)           # numeric ID\n    print(user.username)     # @username (can be None!)\n    print(user.first_name)   # first name\n    print(user.full_name)    # first + last name\n    print(user.language_code)# 'en', 'tr', etc.\n    print(user.is_bot)       # False for humans\n\n    # Get chat info\n    chat = update.effective_chat\n    print(chat.id)    # same as user.id in private chats\n    print(chat.type)  # 'private', 'group', 'supergroup', 'channel'\n```"),

    # ── How to get chat ID ──
    (["chat id", "get chat id", "my id", "find id"],
     "🆔 *How to Get a Chat ID*\n\n*Your own ID:*\nSend any message to your bot and use:\n```python\nasync def handler(update, context):\n    print(update.effective_user.id)  # prints your ID\n```\n\nOr just message `@userinfobot` on Telegram — it tells you your ID instantly.\n\n*Group/Channel ID:*\nAdd your bot to the group, send a message, check:\n```python\nprint(update.effective_chat.id)  # negative number for groups\n```"),

    # ── Logging ──
    (["logging", "log", "logger", "debug log"],
     "📋 *Logging Best Practices*\n\n```python\nimport logging\n\n# Setup at the top of your bot.py\nlogging.basicConfig(\n    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',\n    level=logging.INFO,   # Change to DEBUG for more detail\n)\nlogger = logging.getLogger(__name__)\n\n# Use in handlers:\nlogger.info(f'User {user.id} used /start')\nlogger.warning('Rate limit approaching')\nlogger.error('DB connection failed', exc_info=True)\n```\n\nFor production: log to a file or use a service like Sentry."),
]

# ─────────────────────────────────────────────────────────────
# PTB REFERENCE CARD
# ─────────────────────────────────────────────────────────────
PTB_REFERENCE = """🤖 *python-telegram-bot v21 — Reference Card*

*Install:*
```
pip install python-telegram-bot
```

*Core Classes:*
• `Application` — the main bot app
• `Update` — incoming event (message, callback, etc.)
• `ContextTypes.DEFAULT_TYPE` — context object
• `Bot` — raw API methods (`context.bot`)

*Handler Types:*
```python
CommandHandler("start", fn)           # /start
MessageHandler(filters.TEXT, fn)      # text messages
CallbackQueryHandler(fn)              # inline button press
InlineQueryHandler(fn)                # inline @bot queries
ConversationHandler(...)              # multi-step flows
ChatMemberHandler(fn)                 # join/leave events
```

*Useful Update Properties:*
```python
update.effective_user      # the user
update.effective_chat      # the chat
update.effective_message   # the message
update.callback_query      # if button was pressed
```

*Sending Messages:*
```python
await update.message.reply_text("Hello!")
await update.message.reply_text("*Bold*", parse_mode="Markdown")
await context.bot.send_message(chat_id=123, text="Hi")
```

*Run the bot:*
```python
app.run_polling()    # development
app.run_webhook()    # production
```

Use `/snippet <topic>` for code examples!"""

# ─────────────────────────────────────────────────────────────
# AIOGRAM REFERENCE CARD
# ─────────────────────────────────────────────────────────────
AIOGRAM_REFERENCE = """⚡ *aiogram v3 — Reference Card*

*Install:*
```
pip install aiogram
```

*Core Objects:*
• `Bot` — Telegram API client
• `Dispatcher` — routes updates to handlers
• `Router` — group related handlers
• `FSMContext` — state management
• `StatesGroup` — define conversation states

*Handler Decorators:*
```python
@router.message(Command("start"))       # /start command
@router.message(F.text == "Hello")      # exact text match
@router.message(F.text.startswith("/")) # starts with /
@router.callback_query(F.data == "yes") # button callback
@router.message(StateFilter(MyState.step1)) # FSM state
```

*Magic Filter (F):*
```python
F.text              # message text
F.from_user.id      # user ID
F.chat.type         # chat type
F.photo             # has photo
F.content_type == ContentType.PHOTO
```

*Sending Messages:*
```python
await message.answer("Hello!")           # reply to same chat
await message.answer("*Bold*", parse_mode="Markdown")
await bot.send_message(chat_id, "Hi")
```

*Run the bot:*
```python
await dp.start_polling(bot)
```

Use `/snippet fsm_aiogram` or `/snippet middleware_aiogram` for examples!"""

# ─────────────────────────────────────────────────────────────
# DEPLOY GUIDE
# ─────────────────────────────────────────────────────────────
DEPLOY_GUIDE = """🚀 *Deployment Guide*

*Option 1 — Railway (Recommended for beginners):*
1. Push code to GitHub
2. Go to railway.app → New Project → GitHub repo
3. Add env var: `TELEGRAM_BOT_TOKEN`
4. Railway auto-builds via Dockerfile ✅

*Option 2 — VPS with Docker:*
```bash
# On your server:
git clone your-repo && cd your-repo
cp .env.example .env && nano .env
docker-compose up -d

# View logs:
docker-compose logs -f
```

*Option 3 — systemd service (no Docker):*
```ini
# /etc/systemd/system/mybot.service
[Unit]
Description=Telegram Bot
After=network.target

[Service]
WorkingDirectory=/home/user/mybot
ExecStart=/home/user/mybot/venv/bin/python bot.py
Restart=always
EnvironmentFile=/home/user/mybot/.env

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable mybot && systemctl start mybot
```

*Polling vs Webhook:*
• Dev / simple hosting → polling (what you're using)
• Production HTTPS server → webhook (more efficient)"""

# ─────────────────────────────────────────────────────────────
# TIPS LIST
# ─────────────────────────────────────────────────────────────
TIPS = [
    "💡 *Tip #1* — Never hardcode your bot token. Always use environment variables and `.env` files.",
    "💡 *Tip #2* — Use `await query.answer()` immediately in callback handlers to remove the button's loading spinner.",
    "💡 *Tip #3* — Add `show_alert=True` to `query.answer()` to show a popup instead of a toast notification.",
    "💡 *Tip #4* — Use `filters.TEXT & ~filters.COMMAND` to match text messages that aren't commands.",
    "💡 *Tip #5* — `context.user_data` is a free dict for storing per-user data in memory between messages.",
    "💡 *Tip #6* — Always add a global error handler with `app.add_error_handler()` to catch unexpected crashes.",
    "💡 *Tip #7* — For broadcasts, add `await asyncio.sleep(0.05)` between sends to avoid Telegram's 30 msg/sec limit.",
    "💡 *Tip #8* — Use `update.effective_user`, `update.effective_chat`, `update.effective_message` — they work across all update types.",
    "💡 *Tip #9* — `await update.message.reply_text()` is shorthand for `await context.bot.send_message(chat_id=..., text=...)`.",
    "💡 *Tip #10* — Use `parse_mode='MarkdownV2'` in PTB v20+ for full Markdown support. Escape special chars with `\\`.",
    "💡 *Tip #11* — Set your bot's commands in BotFather with `/setcommands` so they appear in the chat menu.",
    "💡 *Tip #12* — `ConversationHandler.END` (-1) ends a conversation. Always return it in your final handler.",
    "💡 *Tip #13* — Use `run_async=True` (PTB) or aiogram's background tasks for slow operations that shouldn't block updates.",
    "💡 *Tip #14* — Group related commands using `Router` in aiogram — keeps your code organized.",
    "💡 *Tip #15* — PTB's `PicklePersistence` saves `user_data/chat_data` to disk so it survives bot restarts.",
]
"""

# Quick-access snippet keys list (for /snippets menu)
SNIPPET_KEYS = list(SNIPPETS.keys())
EXPLAIN_KEYS = list(EXPLANATIONS.keys())
BEST_KEYS = list(BEST.keys())
