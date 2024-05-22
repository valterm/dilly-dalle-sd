import os
import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

from telegram import Update, User


from .handlers import *

class App():

    def __init__(self):
        # Load environment variables
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.stable_diffusion_url = os.environ.get('STABLE_DIFFUSION_URL')
        self.loglevel = os.environ.get('LOGLEVEL')
        self.database = os.environ.get('DATABASE_URL')

        print(f"TELEGRAM_BOT_TOKEN: {self.telegram_bot_token}")
        # Setup logging
        logging.basicConfig(level=self.loglevel, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def start(self):
        logging.debug('Starting bot')

        updater = Updater(self.telegram_bot_token)
        dispatcher = updater.dispatcher


        # Create handler
        command_handler = RequestHandler(
            database_path=self.database,
            stable_diffusion_url=self.stable_diffusion_url
        )

        # Create handlers
        start_handler = CommandHandler('start', command_handler.start_command_handler)
        help_handler = CommandHandler('help', command_handler.help_command_handler)
        logs_handler = CommandHandler('logs', command_handler.logs_command_handler)
        picgen_handler = CommandHandler('picgen', command_handler.picgen_command_handler)
        teach_handler = CommandHandler('teach', command_handler.teach_alias_command_handler)
        forget_handler = CommandHandler('forget', command_handler.forget_alias_command_handler)
        mywords_handler = CommandHandler('mywords', command_handler.mywords_command_handler)
        photo_filter_handler = (MessageHandler(filters.photo, command_handler.photo_filter_handler)) # Needed for photos sent directly with /variation in the caption
        variation_reply_handler = CommandHandler('variation', command_handler.variation_command_handler) # Needed for /variation as a reply to a photo

        # Add handlers to dispatcher
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(help_handler)
        dispatcher.add_handler(logs_handler)
        dispatcher.add_handler(picgen_handler)
        dispatcher.add_handler(teach_handler)
        dispatcher.add_handler(forget_handler)
        dispatcher.add_handler(mywords_handler)
        dispatcher.add_handler(photo_filter_handler)
        dispatcher.add_handler(variation_reply_handler)

        # Start the bot
        updater.start_polling()
        updater.idle()
        logging.debug('Bot started')
