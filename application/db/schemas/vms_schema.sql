CREATE TABLE IF NOT EXISTS vms (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   ip TEXT NOT NULL UNIQUE,
                   name TEXT NOT NULL,
                   status TEXT NOT NULL,
                   monitoring INTEGER,
                   category TEXT NOT NULL,
                   ssh_user TEXT NOT NULL,
                   ssh_password TEXT NOT NULL,
                   ssh_port INTEGER NOT NULL
                   );
