'''
This program requires the following modules:
- python-telegram-bot==22.5
- urllib3==2.6.2
'''
from ChatGPT_HKBU_UPDATE import ChatGPT
gpt = None

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, ContextTypes, filters,
    CommandHandler
)
import configparser
import logging
from telegram.error import TelegramError
import time
from collections import defaultdict

# Conversation context storage (in-memory)
user_conversations = {}
# Rate limit: max 5 messages per minute
RATE_LIMIT = 5
user_requests = defaultdict(list)

def main():
    # Configure logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # Load configuration
    logging.info('INIT: Loading configuration...')
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Validate config
    required_sections = ['TELEGRAM', 'CHATGPT']
    required_keys = {
        'TELEGRAM': ['ACCESS_TOKEN'],
        'CHATGPT': ['API_KEY', 'BASE_URL', 'MODEL', 'API_VER']
    }
    for section in required_sections:
        if section not in config:
            logging.fatal(f"CONFIG ERROR: Missing section [{section}] in config.ini")
            return
        for key in required_keys[section]:
            if key not in config[section] or not config[section][key]:
                logging.fatal(f"CONFIG ERROR: Missing key {key} in section [{section}]")
                return

    global gpt
    gpt = ChatGPT(config)

    logging.info('INIT: Connecting the Telegram bot...')
    app = ApplicationBuilder().token(config['TELEGRAM']['ACCESS_TOKEN']).build()

    logging.info('INIT: Registering command handlers...')
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))

    logging.info('INIT: Registering the message handler...')
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, callback))

    logging.info('INIT: Initialization done!')
    app.run_polling()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        " Hello! I'm your university assistant bot.\n"
        "Just send text to ask questions. Commands:\n"
        "/help - Show help\n"
        "/clear - Clear conversation history"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        " Help Guide:\n"
        "1. Send text to chat with AI\n"
        "2. /start - Initialize bot\n"
        "3. /clear - Clear your chat history\n"
        "4. If you get errors, please try again later"
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
    await update.message.reply_text(" Conversation history cleared!")

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger = logging.getLogger(__name__)
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    user_message = update.message.text
    logger.info(f"UPDATE: User {user_id} ({username}) sent: {user_message[:50]}")

    # Rate limit check
    current_time = time.time()
    user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < 60]
    if len(user_requests[user_id]) >= RATE_LIMIT:
        await update.message.reply_text("⚠ You are sending messages too fast. Please wait 1 minute.")
        return
    user_requests[user_id].append(current_time)

    try:
        loading_message = await update.message.reply_text('Thinking...')
    except TelegramError as e:
        logger.error(f"Failed to send loading message to {user_id}: {str(e)}")
        return

    try:
        if user_id not in user_conversations:
            user_conversations[user_id] = [
                {"role": "system", "content": gpt.system_message}
            ]
        user_conversations[user_id].append({"role": "user", "content": user_message})

        response = gpt.submit_with_context(user_conversations[user_id])

        user_conversations[user_id].append({"role": "assistant", "content": response})

        if len(user_conversations[user_id]) > 20:
            user_conversations[user_id] = [user_conversations[user_id][0]] + user_conversations[user_id][-18:]

        await loading_message.edit_text(response)

    except TelegramError as e:
        logger.error(f"Failed to send response to {user_id}: {str(e)}")
        try:
            await update.message.reply_text("Error: Failed to send message. Please try again.")
        except:
            pass
    except Exception as e:
        logger.error(f"Unexpected error in callback for {user_id}: {str(e)}", exc_info=True)
        try:
            await loading_message.edit_text("Error: An unknown error occurred.")
        except:
            await update.message.reply_text("Error: An unknown error occurred.")

if __name__ == '__main__':
    main()