import os
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, Application

from telegram import Update, User


from .async_handlers import *

class App():

    def __init__(self):
        # Load environment variables
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.stable_diffusion_url = os.environ.get('STABLE_DIFFUSION_URL')
        self.steps = os.environ.get('STEPS')
        self.loglevel = os.environ.get('LOGLEVEL')
        self.database = os.environ.get('DATABASE_URL')

        # Setup logging
        logging.basicConfig(level=self.loglevel, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def start(self):
        logging.debug('Starting bot')

        application = Application.builder().token(self.telegram_bot_token).build()
        # application = updater.application


        # Create handler
        command_handler = RequestHandler(
            database_path=self.database,
            stable_diffusion_url=self.stable_diffusion_url,
            steps=self.steps
        )

        # Create handlers
        start_handler = CommandHandler('start', command_handler.start_command_handler)
        # help_handler = CommandHandler('help', command_handler.help_command_handler)
        # logs_handler = CommandHandler('logs', command_handler.logs_command_handler)
        picgen_handler = CommandHandler('picgen', command_handler.picgen_command_handler)
        teach_handler = CommandHandler('teach', command_handler.teach_alias_command_handler)
        forget_handler = CommandHandler('forget', command_handler.forget_alias_command_handler)
        mywords_handler = CommandHandler('mywords', command_handler.mywords_command_handler)
        photo_filter_handler = (MessageHandler(filters.PHOTO, command_handler.photo_filter_handler)) # Needed for photos sent directly with /variation in the caption
        variation_reply_handler = CommandHandler('variation', command_handler.variation_command_handler) # Needed for /variation as a reply to a photo
        safemode_handler = CommandHandler('safemode', command_handler.safemode_command_handler)

        # Add handlers to application
        application.add_handler(start_handler)
        # application.add_handler(help_handler)
        # application.add_handler(logs_handler)
        application.add_handler(picgen_handler)
        application.add_handler(teach_handler)
        application.add_handler(forget_handler)
        application.add_handler(mywords_handler)
        application.add_handler(photo_filter_handler)
        application.add_handler(variation_reply_handler)
        application.add_handler(safemode_handler)
        

        # Start the bot
        application.run_polling()
        logging.debug('Bot started')
