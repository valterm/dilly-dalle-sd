CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    is_username BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_types (
    chat_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_chat_id INTEGER UNIQUE NOT NULL,
    chat_type_id INTEGER NOT NULL,
    FOREIGN KEY (chat_type_id) REFERENCES chat_types(chat_type_id)
);

CREATE TABLE IF NOT EXISTS userchats (
    userchat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chat_id VARCHAR NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    UNIQUE (user_id, chat_id)
);

CREATE TABLE IF NOT EXISTS image_types(
    image_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS gen_log(
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    userchat_id INTEGER NOT NULL,
    prompt VARCHAR NOT NULL,
    image_type_id INTEGER NOT NULL,
    filename VARCHAR PRIMARY KEY UNIQUE,
    FOREIGN KEY (userchat_id) REFERENCES userchats(userchat_id),
    FOREIGN KEY (image_type_id) REFERENCES image_types(image_type_id)
);

CREATE TABLE IF NOT EXISTS aliases (
    userchat_id INTEGER,
    alias VARCHAR NOT NULL,
    replacement VARCHAR NOT NULL,
    PRIMARY KEY (userchat_id, alias),
    FOREIGN KEY (userchat_id) REFERENCES userchats(userchat_id)
);

CREATE TABLE IF NOT EXISTS spoiler_status (
    userchat_id INTEGER NOT NULL,
    status BOOLEAN NOT NULL,
    PRIMARY KEY (userchat_id),
    FOREIGN KEY (userchat_id) REFERENCES userchats(userchat_id)
);

CREATE TABLE IF NOT EXISTS fixed_prompt_types (
    prompt_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS custom_fixed_prompts(
    userchat_id INTEGER,
    prompt_type_id INTEGER,
    prompt VARCHAR NOT NULL,
    PRIMARY KEY (userchat_id, prompt_type_id),
    FOREIGN KEY (userchat_id) REFERENCES userchats(userchat_id),
    FOREIGN KEY (prompt_type_id) REFERENCES fixed_prompt_types(prompt_type_id)
);

INSERT INTO chat_types (name) VALUES ('private'),('group'),('channel'),('supergroup');
INSERT INTO fixed_prompt_types (name) VALUES ('positive'),('negative');
INSERT INTO image_types (name) VALUES ('new'),('variation');