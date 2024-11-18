from telegram import Update, Message
from telegram.ext import CallbackContext

from .dataprocessor import DataProcessor
from .stable_diffusion import StableDiffusion

import requests
import logging
from io import BytesIO

# @TODO: Actually implement value error handling for the username for aliases



'''
Class to handle requests from the user using async functions.
'''

class RequestHandler:
    def __init__(self, database_path: str, stable_diffusion_url: str):
        self.database = DataProcessor(database_path)
        self.sd = StableDiffusion(stable_diffusion_url)
        self.dp = DataProcessor(database_path)
        
        self.logger = logging.getLogger(__name__)

    ###########
    # HELPERS #
    ###########

    def __get_username_from_update(self, update: Update) -> str:
        '''
        Retrieve username from update object.
        '''

        user_data = {}
        user = update.effective_user
        try:
            if user.username:
                if user.full_name:
                    user_data = {'username': user.username, 'full_name': user.full_name}
                user_data['username'] = user.username
            elif user.full_name:
                user_data['full_name'] = user.full_name
        except Exception as e:
            self.logger.error(f'Error getting username: {e}')
        
        return(user_data)

    def __get_bot_username(self, update: Update) -> str:
        '''
        Retrieve bot username from update object.
        '''
        return(update.effective_user.username)
    
    def __clean_input(self, update: Update) -> str:
        '''
        Remove command and botname from user input.
        '''
        commands = ["/start", "/help", "/logs", "/picgen", "/teach", "/forget", "/mywords", "/variation", "/safemode"]
        bot_username = self.__get_bot_username(update)
        text = update.message.text

        for command in commands:
            text = text.replace(command, '')
        text = text.replace(f'@{bot_username}', '')

        text = text.strip()

        return(text)

    async def __get_image_from_reply(self, message: Message) -> str:
        '''
        Get image from reply.
        '''
        photo = message.photo[-1]
        image = await photo.get_file()
        return image
    
    async def __get_image_from_message(self, update: Update) -> str:
        '''
        Get image from message.
        '''
        message = update.effective_message
        photo = message.photo[-1]
        image = await photo.get_file()
        return image

    ####################
    # IMAGE GENERATION #
    ####################

    def __read_image_file_into_memory(self, image_path: str):
        '''
        Read image file into memory.
        '''
        try:
            with open(image_path, "rb") as file:
                image = file.read()
                byte_stream = BytesIO(image)
                byte_array = byte_stream.getvalue()
                return byte_array
        except Exception as e:
            self.logger.error(f'Error reading image file into memory: {e}')
            return None
        
    def __download_image_into_memory(self, *args, url=None):
        """
        Download an image from a url and read it into memory
        """
        if not url and args:
            url = args[0]
        headers = {
            "User-Agent": "Chrome/51.0.2704.103",
        }
        response = requests.get(url,headers=headers)

        if response.status_code == 200:
            byte_stream = BytesIO(response.content)
            byte_array = byte_stream.getvalue()
            return byte_array
        else:
            return 1
        
    async def __generate_new_image(self, update: Update, context: CallbackContext):
        '''
        Generate an image based on user input.
        '''
        user = self.__get_username_from_update(update)
        chat_id = update.effective_chat.id
        user_input = self.__clean_input(update)

        if not user_input:
            await update.message.reply_text(f'Please provide a prompt to generate an image.')
            return
        
        aliases = self.__find_aliases(user_input)

        for alias in aliases:
            alias_text = self.dp.get_alias(user, chat_id, alias)
            if alias_text:
                user_input = user_input.replace(f'%{alias}', alias_text)

        image_name = self.sd.generate_image(user_input)
        image_path = f"/app/data/images/{image_name}"
        self.logger.debug(f"user: {user}, chat_id: {update.effective_chat.id}, image_name: {image_name}, prompt: {user_input}, image_type: 'new', chat_type: {update.effective_chat.type}")
        self.dp.log_new_image(user=user, chat_id=update.effective_chat.id, image_name=image_name, prompt=user_input, image_type='new', chat_type=update.effective_chat.type)
        image = self.__read_image_file_into_memory(image_path)
        await update.message.reply_photo(
            image,
            has_spoiler=self.dp.get_spoiler_status(user, update.effective_chat.id)
            )
    
    async def __generate_variation_image(self, update: Update, context: CallbackContext, request_type: str):
        '''
        Generate a variation image based on user input.
        '''
        user = self.__get_username_from_update(update)
        chat_id = update.effective_chat.id
        user_input = self.__clean_input(update)

        if not user_input:
            await update.message.reply_text(f'Please provide (or replay to) an image with a prompt to generate a variation of it.')
            return
        
        aliases = self.__find_aliases(user_input)

        for alias in aliases:
            alias_text = self.dp.get_alias(user, chat_id, alias)
            if alias_text:
                user_input = user_input.replace(f'%{alias}', alias_text)

        if request_type == 'photo':
            image = await self.__get_image_from_message(update)
            prompt = update.message.caption
        elif request_type == 'reply':
            image = await self.__get_image_from_reply(update.message.reply_to_message)
            prompt = user_input
        
        image_jpg = self.__download_image_into_memory(image.file_path)

        image_name = self.sd.generate_image_variation(image_jpg, prompt=prompt)
        image_path = f"/app/data/images/{image_name}"
        self.logger.debug(f"user: {user}, chat_id: {update.effective_chat.id}, image_name: {image_name}, prompt: {prompt}, image_type: 'variation', chat_type: {update.effective_chat.type}")
        self.dp.log_new_image(user=user, chat_id=update.effective_chat.id, image_name=image_name, prompt=prompt, image_type='variation', chat_type=update.effective_chat.type)
        image = self.__read_image_file_into_memory(image_path)
        await update.message.reply_photo(
            image,
            has_spoiler=self.dp.get_spoiler_status(user, update.effective_chat.id)
        )

    ####################
    # ALIAS MANAGEMENT #
    ####################

    def __find_aliases(self, text: str):
        """
        Find words marked as aliases in the text
        """
        marker_string = "%"

        # Split the text into words
        words = text.split(' ')
        # Find the aliases
        aliases = []
        for word in words:
            try:
                # Strip any trailing special characters
                word = word.strip('.,!?')
                if word[0] == marker_string:
                    aliases.append(word[1:])
            except:
                pass
        return aliases

    async def __get_all_aliases(self, update: Update, context: CallbackContext):
        """
        Get all aliases for a user
        """
        # Get the user
        user = self.__get_username_from_update(update)
        chat_id = update.effective_chat.id
        # Get list with all aliases and their values for the user
        aliases = self.dp.dump_aliases(user, chat_id)

        if aliases:
            alias_list = ''
            for alias in aliases:
                alias_list += f'{alias[0]}: {alias[1]}\n'
            await update.message.reply_text(f'Your aliases:\n{alias_list}')
        else:
            await update.message.reply_text('No aliases found.')

    async def __teach_alias(self, update: Update, context: CallbackContext):
        '''
        Teach an alias to the bot.
        '''
        username = self.__get_username_from_update(update)
        chat_id = update.effective_chat.id
        user_input = self.__clean_input(update)

        if not user_input:
            await update.message.reply_text(f'Please provide an alias and text to teach.')
            return
        
        if len(user_input.split(' ', 2)) < 2:
            await update.message.reply_text(f'Please provide an alias and text to teach.')
            return

        alias, text = user_input.split(' ', 1)
        alias = alias.replace('%','')

        self.logger.info(f'Text: {text}')

        try:
            self.logger.debug(f'Teaching alias {alias} for user {username}')
            self.dp.teach_alias(username, chat_id, alias, text)
            await update.message.reply_text(f'Taught alias {alias}.')
        # except ValueError as e: # ValueError is raised when the user does not have a valid username
        #     self.logger.error(f'Error teaching alias: {e}')
        #     await update.message.reply_text(f'Error teaching alias: {e}')
        except Exception as e:
            self.logger.error(f'Error teaching alias: {e}')
            await update.message.reply_text(f'Error teaching alias: {e}')
    
    async def __forget_alias(self, update: Update, context: CallbackContext):
        '''
        Forget an alias from the bot.
        '''
        username = self.__get_username_from_update(update)
        chat_id = update.effective_chat.id
        user_input = self.__clean_input(update)

        if not user_input:
            await update.message.reply_text(f'Please provide an alias to forget.')
            return
        
        alias = user_input.replace('%','')

        try:
            self.logger.debug(f'Forgetting alias {alias} for user {username}')
            self.dp.forget_alias(username, chat_id, alias)
            await update.message.reply_text(f'Forgot alias {alias}.')
        # except ValueError as e: # ValueError is raised when the user does not have a valid username
        #     self.logger.error(f'Error forgetting alias: {e}')
        #     await update.message.reply_text(f'Error forgetting alias: {e}')
        except Exception as e:
            self.logger.error(f'Error forgetting alias: {e}')
            await update.message.reply_text(f'Error forgetting alias: {e}')

    ####################
    # SPOILER SETTINGS #
    ####################

    async def __set_spoiler_status(self, update: Update, context: CallbackContext):
        '''
        Set the spoiler status for the user.
        '''
        user = self.__get_username_from_update(update)
        chat_id = update.effective_chat.id
        
        # Get message text
        status = self.__clean_input(update)
        if not status or status not in ['on', 'off']:
            await update.message.reply_text(f'Please provide a status ("on" or "off") to set the filter status to.')
            return
        
        spoiler_status = True if status == 'on' else False
        self.dp.set_spoiler_status(user, chat_id, spoiler_status)
        await update.message.reply_text(f'Safemode is now {status}.')

    #####################
    # INTERNAL HANDLERS #
    #####################

    async def __start_command_handler(self, update: Update, context: CallbackContext):
        '''
        Handler for the /start command.
        '''
        await update.message.reply_text(f'Yo, read my README if you don\'t know what to do.')

    async def __help_command_handler(self, update: Update, context: CallbackContext):
        '''
        Handler for the /help command.
        '''
        await update.message.reply_text(f'Help message here.')
    
    async def __teach_alias_command_handler(self, update: Update, context: CallbackContext):
        '''
        Handler for the /alias command.
        '''
        await self.__teach_alias(update, context)

    async def __forget_alias_command_handler(self, update: Update, context: CallbackContext):
        '''
        Handler for the /forget command.
        '''
        await self.__forget_alias(update, context)
    
    async def __generate_image_command_handler(self, update: Update, context: CallbackContext):
        '''
        Handler for the /picgen command.
        '''
        await self.__generate_new_image(update, context)

    async def __generate_variation_command_handler(self, update: Update, context: CallbackContext, request_type: str):
        '''
        Handler for the /variation command.
        '''
        if request_type == 'photo':
            await self.__generate_variation_image(update, context, 'photo')
        elif request_type == 'reply':
            await self.__generate_variation_image(update, context, 'reply')

    async def __set_safemode_command_handler(self, update: Update, context: CallbackContext):
        '''
        Handler for the /safemode command.
        '''
        await self.__set_spoiler_status(update, context)

    async def __mywords_command_handler(self, update: Update, context: CallbackContext):
        '''
        Handler for the /mywords command.
        '''
        await self.__get_all_aliases(update, context)

    ####################
    # COMMAND HANDLERS #
    ####################

    async def start_command_handler(self, update: Update, context: CallbackContext):
        await self.__start_command_handler(update, context)

    async def help_command_handler(self, update: Update, context: CallbackContext):
        await self.__help_command_handler(update, context)

    async def teach_alias_command_handler(self, update: Update, context: CallbackContext):
        await self.__teach_alias_command_handler(update, context)

    async def forget_alias_command_handler(self, update: Update, context: CallbackContext):
        await self.__forget_alias_command_handler(update, context)
    
    async def picgen_command_handler(self, update: Update, context: CallbackContext):
        await self.__generate_image_command_handler(update, context)

    async def variation_command_handler(self, update: Update, context: CallbackContext):
        if update.message.reply_to_message:
            await self.__generate_variation_command_handler(update, context, 'reply')
        else:
            await self.__send_text_reply(update, context, 'Please reply to an (or send a new) image with a prompt to generate a variation of it.')
    
    async def photo_filter_handler(self, update: Update, context: CallbackContext):
        if update.message.caption and update.message.caption.startswith('/variation'):
            await self.__generate_variation_command_handler(update, context, 'photo')
    
    async def safemode_command_handler(self, update: Update, context: CallbackContext):
        await self.__set_safemode_command_handler(update, context)
    
    async def mywords_command_handler(self, update: Update, context: CallbackContext):
        await self.__mywords_command_handler(update, context)
    