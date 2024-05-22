import apsw
import uuid
import logging

class DataProcessor:
    def __init__(self, database: str):
        self.con = apsw.Connection(database)
        self.cursor = self.con.cursor()
        self.logger = logging.getLogger(__name__)

    def __log_new_user(self, user: dict):
        """
        Log a new user into the database.
        """
        sql = 'INSERT INTO users (username, full_name, is_username) VALUES (?, ?, ?)'
        if user.get('username'):
            data = (user['username'], user['full_name'], True)
        else:
            data = (str(uuid.uuid4()), user['full_name'], False)
        try:
            self.cursor.execute(sql, data)
        except Exception as e:
            self.logger.error('Error logging user: %s', e)

    def __log_new_chat(self, chat: dict):
        """
        Log a new chat into the database.
        """
        sql = 'INSERT INTO chats (telegram_chat_id, chat_name) VALUES (?, ?,)'
        try:
            self.cursor.execute(sql, (chat['id'], chat['title']))
        except Exception as e:
            self.logger.error('Error logging chat: %s', e)

    def __log_new_image(self, username: str, image_name: str, prompt: str, action_type: str = 'new'):
        """
        Log a new image into the database.
        """
        try:
            sql = 'INSERT INTO logs (username, filename, action, prompt) VALUES (?, ?, ?, ?)'
            self.cursor.execute(sql, (username, image_name, action_type, prompt))
        except Exception as e:
            self.logger.error('Error logging image: %s', e)

    def __user_exists(self, username: str):
        """
        Check if a user exists in the database.
        """
        try:
            self.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            self.logger.error('Error checking if user exists: %s', e)
            return False

    def __validate_user(self, username: str):
        """
        Check if the user has a valid username using the is_username field.
        """
        try:
            self.cursor.execute('SELECT * FROM users WHERE username = ? AND is_username = 1', (username,))
            user = self.cursor.fetchone()
            if user:
                return True  # is_username
            else:
                return False
        except Exception as e:
            self.logger.error(f'Error validating user: {e}')
            return False

    def __get_all_data_from_table(self, table: str):
        """
        Get all data from a table.
        """
        try:
            sql = f'SELECT * FROM {table}'
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error('Error getting all data from table: %s', e)
            return []

    def __save_alias(self, username: str, alias: str, text: str):
        """
        Save an alias into the database for users with a valid username.
        """
        # Remove newlines and replace them with spaces
        text = text.replace('\n', ' ')
        
        if self.__validate_user(username):
            try:
                sql = 'INSERT INTO aliases (username, alias, replacement) VALUES (?, ?, ?) ON CONFLICT(username, alias) DO UPDATE SET replacement = ?'
                self.cursor.execute(sql, (username, alias, text, text))
            except Exception as e:
                self.logger.error(f'Error saving alias: {e}')
        else:
            self.logger.error('No valid username for user')
            raise ValueError(f'No valid username for user {username}')

    def __retrieve_alias(self, username: str, alias: str):
        """
        Retrieve an alias from the database.
        """
        try:
            sql = 'SELECT replacement FROM aliases WHERE username = ? AND alias = ?'
            self.cursor.execute(sql, (username, alias))
            alias = self.cursor.fetchone()

            if alias:
                return alias[0]
            else:
                return None

        except Exception as e:
            self.logger.error(f'Error retrieving alias: {e}')
            return None

    def __delete_alias(self, username: str, alias: str):
        """
        Delete an alias from the database.
        """
        try:
            logging.debug(f'Deleting alias {alias} for user {username}')
            sql = 'DELETE FROM aliases WHERE username = ? AND alias = ?'
            self.cursor.execute(sql, (username, alias))
        except Exception as e:
            self.logger.error(f'Error deleting alias: {e}')

    def __get_all_aliases(self, username: str):
        """
        Get all aliases for a user.
        """
        try:
            sql = 'SELECT alias, replacement FROM aliases WHERE username = ?'
            self.cursor.execute(sql, (username,))
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f'Error getting all aliases: {e}')
            return []

    ### PUBLIC METHODS
    def log_new_image(self, user: dict, image_name: str, prompt: str, action_type: str = 'new'):
        """
        Log a new image into the database.
        """
        if not self.__user_exists(user['username']):
            self.__log_new_user(user)
        logging.info('Logging new image')
        self.__log_new_image(user['username'], image_name, prompt, action_type)

    def dump_data(self, table: str):
        """
        Get all data from a table.
        """
        return self.__get_all_data_from_table(table)

    def teach_alias(self, user: dict, alias: str, text: str):
        """
        Save an alias into the database for users with a valid username.
        """
        if not self.__user_exists(user['username']):
            self.__log_new_user(user)

        if self.__validate_user(user['username']):
            self.__save_alias(user['username'], alias, text)
        else:
            raise ValueError('No valid username for user')

    def get_alias(self, user: dict, alias: str):
        """
        Retrieve an alias from the database.
        """
        if self.__user_exists(user['username']):
            if self.__validate_user(user['username']):
                return self.__retrieve_alias(user['username'], alias)
            else:
                raise ValueError('No valid username for user')
        else:
            self.__log_new_user(user)
            return None

    def forget_alias(self, user: dict, alias: str):
        """
        Delete an alias from the database.
        """
        if self.__user_exists(user['username']):
            if self.__validate_user(user['username']):
                self.__delete_alias(user['username'], alias)
        else:
            self.__log_new_user(user)

    def dump_aliases(self, user: dict):
        """
        Get all aliases for a user.
        """
        if self.__user_exists(user['username']):
            if self.__validate_user(user['username']):
                return self.__get_all_aliases(user['username'])    
        else:
            self.__log_new_user(user)
        return []
    
    def get_spoiler_status(self, chat_id: dict):
        return True