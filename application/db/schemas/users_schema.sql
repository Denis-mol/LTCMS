CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE ,
            password TEXT NOT NULL,
            permissions TEXT NOT NULL,
            status TEXT NOT NULL,
            range TEXT NOT NULL
             );