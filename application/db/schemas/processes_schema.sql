CREATE TABLE IF NOT EXISTS processes (
            ip TEXT NOT NULL,
            name TEXT NOT NULL,
            version TEXT,
            monitoring_period INTEGER,
            logs_path TEXT,
            UNIQUE (ip, name));