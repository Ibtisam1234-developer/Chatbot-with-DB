DROP TABLE IF EXISTS chat_messages;

CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
