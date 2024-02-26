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