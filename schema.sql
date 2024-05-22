CREATE TABLE IF NOT EXISTS users (
    username VARCHAR PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    is_username BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR NOT NULL,
    action VARCHAR NOT NULL,
    prompt VARCHAR NOT NULL,
    filename VARCHAR PRIMARY KEY UNIQUE,
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE IF NOT EXISTS aliases (
    username VARCHAR,
    alias VARCHAR,
    replacement VARCHAR NOT NULL,
    PRIMARY KEY (username, alias),
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE IF NOT EXISTS prompt_types (
    prompt_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS custom_fixed_prompts(
    username VARCHAR,
    prompt_type_id INTEGER,
    prompt VARCHAR NOT NULL,
    PRIMARY KEY (username, prompt_type_id),
    FOREIGN KEY (username) REFERENCES users(username),
    FOREIGN KEY (prompt_type_id) REFERENCES prompt_types(prompt_type_id)
);

INSERT INTO prompt_types (name) VALUES ('positive'),('negative');