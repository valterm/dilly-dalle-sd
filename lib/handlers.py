from telegram import Update, User, Message
from telegram.ext import Updater,CallbackContext

from .stable_diffusion import StableDiffusion
from .dataprocessor import DataProcessor

import logging
import threading
import requests
import uuid
from io import BytesIO
import apsw


class RequestHandler:
    def __init__(self, database_path: str, stable_diffusion_url: str):
        self.logger = logging.getLogger(__name__)
        self.stable_diffusion_url = stable_diffusion_url
        self.dp = DataProcessor(database_path)

### HELPERS
    def __strip_input(self, input: str, experssions: list):
        """
        Removes the list of expressions from the input.
        Used to remove the command from the prompt.
        """

        for experssion in experssions:
            input = input.replace(experssion, '')
        return input

    def __get_username_from_message(self, update: Update):
        user_data = {}
        # Get user
        user = update.effective_user
        if not user.username:
            # return(f"{user.last_name} {user.first_name}")
            user_data['full_name'] = (user.last_name + user.first_name)
        else:
            user_data['username'] = user.username
            user_data['full_name'] = (user.last_name + user.first_name)
        return user_data

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

    ### SENDERS
    def __send_text_message(self, update: Update, context: CallbackContext, message: str):
        """
        Sends a text message to the chat
        """
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )

    def __send_text_reply(self, update: Update, context: CallbackContext, message: str):
        """
        Send a text message as a reply to another message
        """
        # Send message
        update.message.reply_text(
            text=message,
            reply_to_message_id=update.message.message_id
        )

    def __send_photo_reply(self, update: Update, context: CallbackContext, photo: bytes, caption: str = None):
        """
        Send a photo as a reply to another message
        """
        # Send photo
        update.message.reply_photo(
            photo=photo,
            reply_to_message_id=update.message.message_id,
            caption=caption
        )

    ### IMAGE HELPERS
    def __get_image_from_message(self, update: Update):
        """
        Get the attached image from a message
        """
        logging.debug('Entering: __get_image_from_message')
        # Get image from message
        message = update.effective_message
        photo = message.photo[-1]
        image = photo.get_file()
        return image

    def __get_image_from_reply(self, message: Message):
        """
        Get the attached image from a message that is being replied to
        """
        logging.debug('Entering: __get_image_from_reply')
        # Get image from message
        photo = message.photo[-1]
        image = photo.get_file()
        return image

    def __get_image_caption(self, update: Update):
        """
        Get the caption from an image message
        """
        logging.debug('Entering: __get_image_caption')
        # Get image caption
        image = update.message.photo[-1]
        caption = image.caption
        return caption

    def __read_image_file_into_memory(self, image_path: str):
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

        logging.debug('Entering: __download_image_into_memory')
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


### INTERNAL HANDLERS
    ### ALIASING
    def __teach_alias(self, update: Update, context: CallbackContext):
        """
        Teach the bot an alias
        """
        logging.debug('Entering: __teach_alias')
        # Get the prompt from the message
        prompt = self.__strip_input(update.message.text, ['/teach', '@'+context.bot.username])

        if not prompt:
            self.__send_text_reply(update, context, 'Provide an alias and the text to teach a prompt.\nExample: /teach %Martin The most handsome man I have ever seen.')
            return

        # Split the prompt into the alias and the text
        prompt = prompt.split(' ', 2)
        alias = prompt[1].replace('%', '')
        text = prompt[2]

        # Save the alias into the database
        user = self.__get_username_from_message(update)
        try:
            self.dp.teach_alias(user, alias, text)
            self.__send_text_reply(update, context, f'Taught alias: {alias}')
        except ValueError as e:
            self.__send_text_reply(update, context, f'Error teaching alias: {e}')
        except Exception as e:
            self.__send_text_reply(update, context, f'Error teaching alias: {e}')

    def __forget_alias(self, update: Update, context: CallbackContext):
        """
        Remove an alias from the database
        """
        logging.debug('Entering: __remove_alias')
        # Get the prompt from the message
        prompt = self.__strip_input(update.message.text, ['/forget', '@'+context.bot.username])
        if not prompt:
            self.__send_text_reply(update, context, 'Provide an alias to forget.\nExample: /forget %Martin')
            return
        # Remove the alias from the database
        user = self.__get_username_from_message(update)
        alias = prompt.replace('%', '')
        alias = alias.lstrip()
        self.dp.forget_alias(user, alias)
        self.__send_text_reply(update, context, f'Forgot alias: {alias}')

    def __get_all_aliases(self, update: Update, context: CallbackContext):
        """
        Get all aliases for a user
        """
        logging.debug('Entering: __get_all_aliases')
        # Get the user
        user = self.__get_username_from_message(update)
        # Get all aliases for the user
        aliases = self.dp.dump_aliases(user)
        text = 'Your aliases:\n'
        if len(aliases) == 0:
            text = 'You have no aliases.'
        else:
            for alias in aliases:
                text += f"{alias[0]}: {alias[1]}\n"

        self.__send_text_reply(update, context, text)


    ### IMAGE GENERATION
    def __generate_new_image(self, update: Update, context: CallbackContext):

        """
        Handler for the /picgen command
        """
        self.logger.debug('Entering generate_handler')

        user = self.__get_username_from_message(update)

        # Get the prompt from the message
        prompt = self.__strip_input(update.message.text, ['/picgen', '@'+context.bot.username])
        self.logger.debug(f'Prompt: {prompt}')

        # Find aliases in the prompt
        aliases = self.__find_aliases(prompt)
        self.logger.debug(f'Aliases: {aliases}')

        # Replace aliases with their text
        for alias in aliases:
            replacement = self.dp.get_alias(user, alias)
            if replacement:
                prompt = prompt.replace(f"%{alias}", replacement)

        # Generate the image
        sd = StableDiffusion(url=self.stable_diffusion_url)
        image_name = sd.generate_image(prompt)
        image_path = f"/app/data/images/{image_name}"

        # Log generated image into database
        self.dp.log_new_image(user, image_name, prompt, "new")

        # Read the image into memory
        image = self.__read_image_file_into_memory(image_path)
        # Send the image as a reply
        self.__send_photo_reply(update, context, image)

        self.logger.debug('Exiting generate_handler')

    def __sd_variation_handler(self, update: Update, context: CallbackContext, request_type: str):
        logging.debug('Entering: __change_handler')
        try:
            if request_type == 'photo':
                image_file = self.__get_image_from_message(update)
                prompt = update.message.caption
            elif request_type == 'reply':
                image_file = self.__get_image_from_reply(update.message.reply_to_message)
                prompt = update.message.text

            image_jpg = self.__download_image_into_memory(image_file.file_path)

        except Exception as e:
            logging.error(f"Error getting image: ")
            self.__send_text_reply(update, context, f"There was an error processing the image:\n{e}")
            return

        # Get user
        user = self.__get_username_from_message(update)

        # Get prompt
        prompt = self.__strip_input(prompt, ['/variation', '@'+context.bot.username])


        sd = StableDiffusion(url=self.stable_diffusion_url)

        img = sd.generate_image_variation(image=image_jpg, prompt=prompt, username=user['username'])
        image_path = f"/app/data/images/{img}"
        image = self.__read_image_file_into_memory(image_path)

        # Log generated image into database
        self.dp.log_new_image(user, img, prompt, "variation")

        # Send image
        self.__send_photo_reply(update, context, image)
        logging.debug('Exiting: __change_handler')

### COMMAND HANDLERS
    def start_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /start command
        """
        self.logger.debug('Entering start_handler')
        update.message.reply_text('Hello! I am a bot that can generate images from text. Send me a description and I will generate an image for you!')
        self.logger.debug('Exiting start_handler')

    def help_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /help command
        """
        self.logger.debug('Entering help_handler')
        update.message.reply_text('I can generate images from text. Send me a description and I will generate an image for you!')
        self.logger.debug('Exiting help_handler')

    def logs_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /logs command
        """
        self.logger.debug('Entering logs_dump_handler')
        # Get all logs from the database
        logs = self.dp.dump_data('logs')
        # Send the logs as a reply
        self.__send_text_reply(update, context, logs)
        self.logger.debug('Exiting logs_dump_handler')

    def picgen_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /picgen command
        """
        self.logger.debug('Entering generate_handler')
        # Start thread to generate image
        threading.Thread(target=self.__generate_new_image, args=(update, context)).start()
        self.logger.debug('Exiting generate_handler')

    def teach_alias_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /teach command
        """
        self.logger.debug('Entering teach_alias_handler')
        # Teach the bot an alias
        threading.Thread(target=self.__teach_alias, args=(update, context)).start()

    def forget_alias_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /forget command
        """
        self.logger.debug('Entering forget_alias_handler')
        # Remove an alias from the database
        threading.Thread(target=self.__forget_alias, args=(update, context)).start()

    def mywords_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /mywords command
        """
        self.logger.debug('Entering mywords')
        # Get all aliases for a user
        threading.Thread(target=self.__get_all_aliases, args=(update, context)).start()

    def photo_filter_handler(self, update: Update, context: CallbackContext):
        """
        Handler for photo messages
        """
        self.logger.debug('Entering photo_filter_handler')
        # Start thread to generate image
        if update.message.caption and "/variation" in update.message.caption:
            threading.Thread(target=self.__sd_variation_handler, args=(update, context, 'photo')).start()        
        self.logger.debug('Exiting photo_filter_handler')

    def variation_command_handler(self, update: Update, context: CallbackContext):
        """
        Handler for the /variation command
        """
        self.logger.debug('Entering variation_handler')
        if update.message.reply_to_message:
            if update.message.reply_to_message.photo:
                threading.Thread(target=self.__sd_variation_handler, args=(update, context, 'reply')).start()
            else:
                self.__send_text_reply(update, context, 'Reply to an image or send a new photo to generate a variation.')
        self.logger.debug('Exiting variation_handler')