#!/bin/bash

# Setup the data env
mkdir -p /app/data/sqlite
mkdir -p /app/data/images

if [ ! -f /app/sqlite/shrekalicious.db ]; then
    python -c "import sqlite3; conn = sqlite3.connect('/app/data/sqlite/shrekalicious.db'); cur = conn.cursor(); cur.executescript(open('schema.sql', 'r').read()); conn.commit(); conn.close();"
else
    echo "SQLite database already exists."
fi

exec python main.py
