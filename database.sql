CREATE TABLE feeds (
    id SERIAL PRIMARY KEY,
    status VARCHAR(15) NOT NULL DEFAULT 'processing'
                   CHECK (status IN ('processing', 'done', 'failed'))
);
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    feed_id INT NOT NULL REFERENCES feeds(id),
    g_id VARCHAR(63) NOT NULL,
    title TEXT,
    description TEXT,
    price NUMERIC,
    currency VARCHAR(15),
    UNIQUE (feed_id, g_id)
);
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    feed_id INT NOT NULL REFERENCES feeds(id),
    image_data BYTEA,
    image_format TEXT,
    url TEXT
);

