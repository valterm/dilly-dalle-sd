import apsw
import uuid
import logging

# @TODO: Add logging
# @TODO: Update handlers in async_handlers.py to pass chat <dict> instead of chat_id <int>; update
#        the aliasing and spoiler handlers to use __user_chat_handler() to log new chats in case they don't exist
# @TODO: Create method to validate user username; raise exception if username is invalid for alias

class DataProcessor:
    def __init__(self, database: str):
        self.con = apsw.Connection(database)
        self.cursor = self.con.cursor()
        self.logger = logging.getLogger(__name__)

    ###########
    # Getters #
    ###########

    def __get_chat_type_id(self, chat_type: str):
        """
        Get the chat_type_id from the chat type name.
        """
        sql = 'SELECT chat_type_id FROM chat_types WHERE name = ?'
        try:
            self.cursor.execute(sql, (chat_type,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error('Error getting chat type id: %s', e)
            return None
        
    def __get_user_id(self, user: dict):
        """
        Get the user_id from the user.
        """
        # If the user has a username, use that
        if user.get('username'):
            sql = 'SELECT user_id FROM users WHERE username = ?'
            try:
                self.cursor.execute(sql, (user['username'],))
                result = self.cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                self.logger.error('Error getting user id: %s', e)
                return None
        # If the user doesn't have a username, use the full name
        else:
            sql = 'SELECT user_id FROM users WHERE full_name = ?'
            try:
                self.cursor.execute(sql, (user['full_name'],))
                return self.cursor.fetchone()
            except Exception as e:
                self.logger.error('Error getting user id: %s', e)
                return None
        
    def __get_userchat_id(self, user_id: int, chat_id: int):
        """
        Get the userchat_id from the user_id and chat_id.
        """
        sql = 'SELECT userchat_id FROM userchats WHERE user_id = ? AND chat_id = ?'
        data = (user_id, chat_id)
        try:
            self.cursor.execute(sql, data)
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error('Error getting userchat id: %s', e)
            return None

    def __get_image_type_id(self, image_type: str):
        """
        Get the image_type_id from the image type name.
        """
        sql = 'SELECT image_type_id FROM image_types WHERE name = ?'
        try:
            self.cursor.execute(sql, (image_type,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error('Error getting image type id: %s', e)
            return None

    def __get_chat_id(self, chat_id: int):
        """
        Get the chat_id from the chat_id.
        """
        sql = 'SELECT chat_id FROM chats WHERE telegram_chat_id = ?'
        try:
            self.cursor.execute(sql, (chat_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error('Error getting chat id: %s', e)
            return None

    def __get_spoiler_status(self, userchat_id: int):
        """
        Get the spoiler status from the userchat_id.
        """
        sql = 'SELECT status FROM spoiler_status WHERE userchat_id = ?'
        try:
            self.cursor.execute(sql, (userchat_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error('Error getting spoiler status: %s', e)
            return None

    def __dump_aliases(self, userchat_id: int):
        """
        Get all the aliases and their values for the userchat.
        """
        sql = 'SELECT alias, replacement FROM aliases WHERE userchat_id = ?'
        try:
            self.cursor.execute(sql, (userchat_id,))
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            self.logger.error('Error dumping aliases: %s', e)
            return None 
        
    def __get_alias(self, userchat_id: int, alias: str):
        """
        Get an the alias.
        """
        sql = 'SELECT replacement FROM aliases WHERE userchat_id = ? AND alias = ?'
        data = (userchat_id, alias)
        try:
            self.cursor.execute(sql, data)
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error('Error getting alias: %s', e)
            return None
        
    ###########
    # Loggers #
    ###########

    def __log_new_image(self, userchat_id, image_name: str, prompt: str, action_type_id: int):
        """
        Log a new image into the database.
        """
        try:
            sql = 'INSERT INTO gen_log (userchat_id, prompt, image_type_id, filename) VALUES (?, ?, ?, ?)'
            self.cursor.execute(sql, (userchat_id, prompt, action_type_id, image_name))
        except Exception as e:
            self.logger.error('Error logging image: %s', e)    
    
    def __log_new_user(self, user: dict):
        """
        Log a new user into the database.
        """
        sql = 'INSERT or IGNORE INTO users (username, full_name, is_username) VALUES (?, ?, ?)'
        if user.get('username'):
            data = (user['username'], user['full_name'], True)
        else:
            data = (str(uuid.uuid4()), user['full_name'], False)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error logging user: %s', e)
            self.logger.error(f"user: {user}")
    
    def __log_new_chat(self, chat_id: int, chat_type_id: int):
        """
        Log a new chat into the database.
        """
        sql = 'INSERT or IGNORE INTO chats (telegram_chat_id, chat_type_id) VALUES (?, ?)'
        data = (chat_id, chat_type_id)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error logging chat: %s', e)
            self.logger.error(f"chat_id: {chat_id}, chat_type_id: {chat_type_id}")

    def __log_new_userchat(self, user_id: int, chat_id: int):
        """
        Log a new userchat into the database.
        """
        sql = 'INSERT or IGNORE INTO userchats (user_id, chat_id) VALUES (?, ?)'
        data = (user_id, chat_id)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error logging userchat: %s', e)
        
        # Initialize the spoiler status for the userchat
        sql = 'INSERT or IGNORE INTO spoiler_status (userchat_id, status) VALUES (?, ?)'
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        data = (userchat_id, False)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error initializing spoiler status: %s', e)

    def __user_chat_handler(self, user: dict, chat_id, chat_type: str):
        """
        Log a new user and chat into the database.
        """
        self.__log_new_user(user)
        user_id = self.__get_user_id(user)
        chat_type_id = self.__get_chat_type_id(chat_type)
        self.__log_new_chat(chat_id, chat_type_id)
        chat_id = self.__get_chat_id(chat_id)
        self.__log_new_userchat(user_id, chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)

        retval = {
            'user_id': user_id,
            'chat_id': chat_id,
            'userchat_id': userchat_id
        }
        return retval
        
    ###########
    # Setters #
    ###########

    def __set_spoiler_status(self, userchat_id: int, spoiler_status: bool):
        """
        Set the spoiler status for the user.
        """
        sql = 'UPDATE spoiler_status SET status = ? WHERE userchat_id = ?'
        data = (spoiler_status, userchat_id)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error setting spoiler status: %s', e)

    def __set_alias(self, userchat_id: int, alias: str, replacement: str):
        """
        Set the alias for the userchat.
        """
        sql = 'INSERT or REPLACE INTO aliases (userchat_id, alias, replacement) VALUES (?, ?, ?)'
        data = (userchat_id, alias, replacement)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error setting alias: %s', e)
    
    def __delete_alias(self, userchat_id: int, alias: str):
        """
        Delete the alias for the userchat.
        """
        sql = 'DELETE FROM aliases WHERE userchat_id = ? AND alias = ?'
        data = (userchat_id, alias)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error deleting alias: %s', e)

    ##################
    # Public methods #  
    ##################

    def log_new_image(self, user: dict, chat_id: int, image_name: str, prompt: str, image_type: str, chat_type: str):
        """
        Log a new image into the database.
        """
        self.__user_chat_handler(user, chat_id, chat_type)
        user_id = self.__get_user_id(user)
        chat_id = self.__get_chat_id(chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        image_type_id = self.__get_image_type_id(image_type)
        self.__log_new_image(userchat_id, image_name, prompt, image_type_id)
        
    
    def set_spoiler_status(self, user: dict, chat_id: int, spoiler_status: bool):
        """
        Set the spoiler status for the user.
        """
        user_id = self.__get_user_id(user)
        chat_id = self.__get_chat_id(chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        self.__set_spoiler_status(userchat_id, spoiler_status)

    def get_spoiler_status(self, user: dict, chat_id: int):
        """
        Get the spoiler status for the user.
        """
        self.logger.debug(f'user: {user}, chat_id: {chat_id}')
        user_id = self.__get_user_id(user)
        chat_id = self.__get_chat_id(chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        return self.__get_spoiler_status(userchat_id)
    
    def teach_alias(self, user: dict, chat_id: int, alias: str, replacement: str):
        """
        Set the alias for the user.
        """
        user_id = self.__get_user_id(user)
        chat_id = self.__get_chat_id(chat_id)
        self.__log_new_userchat(user_id, chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        self.__set_alias(userchat_id, alias, replacement)
    
    def forget_alias(self, user: dict, chat_id: int, alias: str):
        """
        Delete the alias for the user.
        """
        user_id = self.__get_user_id(user)
        chat_id = self.__get_chat_id(chat_id)
        self.__log_new_userchat(user_id, chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        self.__delete_alias(userchat_id, alias)
    
    def dump_aliases(self, user: dict, chat_id: int):
        """
        Get all the aliases for the user.
        """
        user_id = self.__get_user_id(user)
        chat_id = self.__get_chat_id(chat_id)
        self.__log_new_userchat(user_id, chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        return self.__dump_aliases(userchat_id)
    
    def get_alias(self, user: dict, chat_id: int, alias: str):
        """
        Get the alias for the user.
        """
        user_id = self.__get_user_id(user)
        chat_id = self.__get_chat_id(chat_id)
        self.__log_new_userchat(user_id, chat_id)
        userchat_id = self.__get_userchat_id(user_id, chat_id)
        return self.__get_alias(userchat_id, alias)