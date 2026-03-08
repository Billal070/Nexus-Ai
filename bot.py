"""
🐍 PyDevBot — Telegram AI for Python & Bot Developers
100% offline, zero external API keys required.
Powered by a hand-crafted expert knowledge base.
"""

import os
import random
import logging
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
)

from knowledge import (
    SNIPPETS, EXPLANATIONS, BEST, KEYWORD_RESPONSES,
    PTB_REFERENCE, AIOGRAM_REFERENCE, DEPLOY_GUIDE, TIPS,
    SNIPPET_KEYS, EXPLAIN_KEYS, BEST_KEYS,
)

# ─────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────
load_dotenv()
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Try multiple common variable names
TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TELEGRAM_TOKEN")
    or os.getenv("TOKEN")
    or ""
)

# Debug: print all env var names so Railway logs show what was injected
logger.info("Env vars present: %s", list(os.environ.keys()))

if not TOKEN:
    logger.error("No token found! Set TELEGRAM_BOT_TOKEN in Railway Variables.")
    raise EnvironmentError("Bot token missing. Set TELEGRAM_BOT_TOKEN in Railway Variables.")

logger.info("Token loaded OK (first 8 chars: %s...)", TOKEN[:8])

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
async def send_safe(update: Update, text: str, parse_mode=constants.ParseMode.MARKDOWN) -> None:
    """Send message, fall back to plain text on parse error."""
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception:
            await update.message.reply_text(chunk, parse_mode=None)


def normalize(text: str) -> str:
    return text.lower().strip()


def keyword_match(text: str):
    """Return first matching response for the user's message."""
    t = normalize(text)
    for keywords, response in KEYWORD_RESPONSES:
        if any(kw in t for kw in keywords):
            return response
    return None


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📘 Code Snippets",   callback_data="menu_snippets"),
         InlineKeyboardButton("🧠 Explanations",    callback_data="menu_explain")],
        [InlineKeyboardButton("🏆 Best Libraries",  callback_data="menu_best"),
         InlineKeyboardButton("💡 Dev Tips",        callback_data="menu_tips")],
        [InlineKeyboardButton("🤖 PTB Reference",   callback_data="menu_ptb"),
         InlineKeyboardButton("⚡ aiogram Reference",callback_data="menu_aiogram")],
        [InlineKeyboardButton("🚀 Deploy Guide",    callback_data="menu_deploy")],
    ]
    await update.message.reply_text(
        f"👋 Hey *{user.first_name}*\\! I'm *PyDevBot* 🐍\n\n"
        "Your offline AI\\-free expert for:\n"
        "• Python development\n"
        "• Telegram bot building \\(PTB & aiogram\\)\n"
        "• Deployment & DevOps\n"
        "• Debugging & best practices\n\n"
        "Pick a topic below or just *ask me anything* 💬",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🛠 *PyDevBot Commands*\n\n"
        "*/start* — Main menu\n"
        "*/help* — This message\n"
        "*/snippet <topic>* — Code snippet\n"
        "  `inline_keyboard` · `conversation_handler`\n"
        "  `send_photo` · `schedule_job` · `webhook`\n"
        "  `sqlite` · `fsm_aiogram` · `middleware_aiogram`\n"
        "  `env` · `error_handler` · `pagination`\n"
        "  `broadcast` · `decorator` · `typing_action`\n"
        "  `inline_query`\n\n"
        "*/explain <topic>* — Deep explanation\n"
        "  `conversationhandler` · `webhook` · `fsm`\n"
        "  `middleware` · `jobqueue` · `inline_keyboard`\n"
        "  `filters` · `context_user_data` · `rate_limiting`\n\n"
        "*/best <topic>* — Best library recommendation\n"
        "  `database` · `http` · `scheduler`\n"
        "  `deployment` · `bot_framework`\n\n"
        "*/ptb* — python-telegram-bot reference card\n"
        "*/aiogram* — aiogram v3 reference card\n"
        "*/deploy* — Deployment guide\n"
        "*/tip* — Random developer tip\n"
        "*/snippets* — Browse all snippets\n\n"
        "Or just *type your question* and I'll answer it! 💬"
    )
    await send_safe(update, text)


# ─────────────────────────────────────────────
# /snippet
# ─────────────────────────────────────────────
async def snippet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        keys = "\n".join(f"• `{k}`" for k in SNIPPET_KEYS)
        await send_safe(update, f"📘 *Available Snippets:*\n\n{keys}\n\n_Usage:_ `/snippet inline_keyboard`")
        return

    key = "_".join(context.args).lower().replace(" ", "_").replace("-", "_")
    # Fuzzy: find first key that contains the search term
    match = next((k for k in SNIPPETS if key in k or k in key), None)
    if not match:
        await send_safe(update, f"❓ No snippet found for `{key}`.\n\nType `/snippets` to see all available snippets.")
        return

    title, code = SNIPPETS[match]
    await send_safe(update, f"{title}\n\n{code}")


# ─────────────────────────────────────────────
# /snippets — browse menu
# ─────────────────────────────────────────────
async def snippets_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = []
    row = []
    for i, key in enumerate(SNIPPET_KEYS):
        label = key.replace("_", " ").title()
        row.append(InlineKeyboardButton(label, callback_data=f"snip_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    await update.message.reply_text(
        "📘 *Choose a snippet:*",
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ─────────────────────────────────────────────
# /explain
# ─────────────────────────────────────────────
async def explain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        keys = "\n".join(f"• `{k}`" for k in EXPLAIN_KEYS)
        await send_safe(update, f"📖 *Explainable Topics:*\n\n{keys}\n\n_Usage:_ `/explain webhook`")
        return

    key = "_".join(context.args).lower().replace(" ", "").replace("-", "").replace("_", "")
    match = next((k for k in EXPLANATIONS if key in k or k in key), None)
    if not match:
        await send_safe(update, f"❓ No explanation found for `{'_'.join(context.args)}`.\n\nAvailable: {', '.join(f'`{k}`' for k in EXPLAIN_KEYS)}")
        return

    await send_safe(update, EXPLANATIONS[match])


# ─────────────────────────────────────────────
# /best
# ─────────────────────────────────────────────
async def best_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        keys = "\n".join(f"• `{k}`" for k in BEST_KEYS)
        await send_safe(update, f"🏆 *Best Library Topics:*\n\n{keys}\n\n_Usage:_ `/best database`")
        return

    key = "_".join(context.args).lower().replace(" ", "_")
    match = next((k for k in BEST if key in k or k in key), None)
    if not match:
        await send_safe(update, f"❓ No recommendation found for `{key}`.\n\nAvailable: {', '.join(f'`{k}`' for k in BEST_KEYS)}")
        return

    await send_safe(update, BEST[match])


# ─────────────────────────────────────────────
# /ptb / /aiogram / /deploy
# ─────────────────────────────────────────────
async def ptb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_safe(update, PTB_REFERENCE)

async def aiogram_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_safe(update, AIOGRAM_REFERENCE)

async def deploy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_safe(update, DEPLOY_GUIDE)


# ─────────────────────────────────────────────
# /tip
# ─────────────────────────────────────────────
async def tip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_safe(update, random.choice(TIPS))


# ─────────────────────────────────────────────
# Inline keyboard callbacks
# ─────────────────────────────────────────────
MENU_RESPONSES = {
    "menu_ptb":     PTB_REFERENCE,
    "menu_aiogram": AIOGRAM_REFERENCE,
    "menu_deploy":  DEPLOY_GUIDE,
}

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # Static menu responses
    if data in MENU_RESPONSES:
        chunks = [MENU_RESPONSES[data][i:i+4000] for i in range(0, len(MENU_RESPONSES[data]), 4000)]
        for chunk in chunks:
            try:
                await query.message.reply_text(chunk, parse_mode=constants.ParseMode.MARKDOWN)
            except Exception:
                await query.message.reply_text(chunk, parse_mode=None)
        return

    # Snippet browser
    if data.startswith("snip_"):
        key = data[5:]
        if key in SNIPPETS:
            title, code = SNIPPETS[key]
            text = f"{title}\n\n{code}"
            try:
                await query.message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)
            except Exception:
                await query.message.reply_text(text, parse_mode=None)
        return

    # Snippet menu button
    if data == "menu_snippets":
        buttons = []
        row = []
        for i, key in enumerate(SNIPPET_KEYS):
            label = key.replace("_", " ").title()
            row.append(InlineKeyboardButton(label, callback_data=f"snip_{key}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        await query.message.reply_text(
            "📘 *Choose a snippet:*",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # Explain menu button
    if data == "menu_explain":
        buttons = []
        row = []
        for i, key in enumerate(EXPLAIN_KEYS):
            label = key.replace("_", " ").title()
            row.append(InlineKeyboardButton(label, callback_data=f"exp_{key}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        await query.message.reply_text(
            "🧠 *Choose a topic to explain:*",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # Explain item
    if data.startswith("exp_"):
        key = data[4:]
        if key in EXPLANATIONS:
            try:
                await query.message.reply_text(EXPLANATIONS[key], parse_mode=constants.ParseMode.MARKDOWN)
            except Exception:
                await query.message.reply_text(EXPLANATIONS[key], parse_mode=None)
        return

    # Best menu button
    if data == "menu_best":
        buttons = [[InlineKeyboardButton(k.replace("_"," ").title(), callback_data=f"best_{k}")] for k in BEST_KEYS]
        await query.message.reply_text(
            "🏆 *Choose a topic:*",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # Best item
    if data.startswith("best_"):
        key = data[5:]
        if key in BEST:
            try:
                await query.message.reply_text(BEST[key], parse_mode=constants.ParseMode.MARKDOWN)
            except Exception:
                await query.message.reply_text(BEST[key], parse_mode=None)
        return

    # Tips menu button
    if data == "menu_tips":
        keyboard = [[InlineKeyboardButton("🎲 Random Tip", callback_data="random_tip")]]
        tip = random.choice(TIPS)
        try:
            await query.message.reply_text(
                tip + "\n\n_Tap below for another tip:_",
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception:
            await query.message.reply_text(tip)
        return

    if data == "random_tip":
        keyboard = [[InlineKeyboardButton("🎲 Another Tip", callback_data="random_tip")]]
        tip = random.choice(TIPS)
        try:
            await query.message.reply_text(
                tip + "\n\n_Tap below for another tip:_",
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception:
            await query.message.reply_text(tip)
        return


# ─────────────────────────────────────────────
# General message handler — keyword engine
# ─────────────────────────────────────────────
FALLBACK_RESPONSES = [
    "🤔 I didn't quite catch that. Try asking about:\n• `inline keyboard` · `conversation handler`\n• `webhook` · `database` · `async`\n• `deploy` · `error` · `schedule`\n\nOr type /help to see all commands.",
    "🐍 Not sure what you mean. Try something like:\n`How do I send a photo?` or `explain FSM`\n\nType /help for all commands.",
    "❓ I don't have an answer for that one yet.\n\nTry `/snippet`, `/explain`, or `/best` — I know a lot about those! 💪",
]

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    response = keyword_match(text)
    if response:
        await send_safe(update, response)
    else:
        await send_safe(update, random.choice(FALLBACK_RESPONSES))


# ─────────────────────────────────────────────
# Error handler
# ─────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update caused error: {context.error}", exc_info=context.error)


# ─────────────────────────────────────────────
# Post-init: register commands in Telegram menu
# ─────────────────────────────────────────────
async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start",    "👋 Main menu"),
        BotCommand("help",     "🛠 All commands"),
        BotCommand("snippet",  "📘 Code snippet"),
        BotCommand("snippets", "📚 Browse all snippets"),
        BotCommand("explain",  "🧠 Explain a concept"),
        BotCommand("best",     "🏆 Best library recommendation"),
        BotCommand("ptb",      "🤖 PTB reference card"),
        BotCommand("aiogram",  "⚡ aiogram reference card"),
        BotCommand("deploy",   "🚀 Deployment guide"),
        BotCommand("tip",      "💡 Random dev tip"),
    ])
    logger.info("✅ Commands registered.")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main() -> None:
    logger.info("🚀 Starting PyDevBot (offline mode)...")

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_cmd))
    app.add_handler(CommandHandler("snippet",  snippet_cmd))
    app.add_handler(CommandHandler("snippets", snippets_menu))
    app.add_handler(CommandHandler("explain",  explain_cmd))
    app.add_handler(CommandHandler("best",     best_cmd))
    app.add_handler(CommandHandler("ptb",      ptb_cmd))
    app.add_handler(CommandHandler("aiogram",  aiogram_cmd))
    app.add_handler(CommandHandler("deploy",   deploy_cmd))
    app.add_handler(CommandHandler("tip",      tip_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_error_handler(error_handler)

    logger.info("✅ PyDevBot is live! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
