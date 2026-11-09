CREATE TABLE user (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash CHAR(60)     NOT NULL,
    role          ENUM('client', 'admin') NOT NULL,
    -- Target of the composite foreign key in client, which lets only users with role 'client' have a client row
    CONSTRAINT uq_user_id_role UNIQUE (id, role)
);

CREATE TABLE client (
    user_id INT PRIMARY KEY,
    role    ENUM('client') NOT NULL DEFAULT 'client',
    name    VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    CONSTRAINT fk_client_user FOREIGN KEY (user_id, role) REFERENCES user (id, role)
);

CREATE TABLE payment_method (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    client_id       INT          NOT NULL REFERENCES client (user_id),
    type            ENUM('credit', 'debit') NOT NULL,
    card_number     VARCHAR(19)  NOT NULL UNIQUE,
    billing_address VARCHAR(255) NULL
);

CREATE TABLE theater (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    max_occupancy      INT     NOT NULL CHECK (max_occupancy > 0),
    supports_3d        BOOLEAN NOT NULL,
    has_enhanced_sound BOOLEAN NOT NULL
);

CREATE TABLE language (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE genre (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE movie (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    title                VARCHAR(200) NOT NULL,
    release_date         DATE         NOT NULL,
    running_time_minutes SMALLINT     NOT NULL CHECK (running_time_minutes > 0),
    original_language_id INT          NOT NULL REFERENCES language (id),
    description          TEXT         NOT NULL
);

CREATE TABLE movie_language (
    movie_id    INT NOT NULL REFERENCES movie (id),
    language_id INT NOT NULL REFERENCES language (id),
    PRIMARY KEY (movie_id, language_id)
);

CREATE TABLE movie_genre (
    movie_id INT NOT NULL REFERENCES movie (id),
    genre_id INT NOT NULL REFERENCES genre (id),
    PRIMARY KEY (movie_id, genre_id)
);

CREATE TABLE movie_embedding (
    movie_id  INT PRIMARY KEY REFERENCES movie (id),
    embedding VECTOR NOT NULL
);

CREATE TABLE screening (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    movie_id     INT      NOT NULL,
    theater_id   INT      NOT NULL REFERENCES theater (id),
    language_id  INT      NOT NULL,
    starts_at    DATETIME NOT NULL,
    tickets_sold INT      NOT NULL DEFAULT 0 CHECK (tickets_sold >= 0),
    CONSTRAINT uq_screening_theater_start UNIQUE (theater_id, starts_at),
    CONSTRAINT fk_screening_movie_language FOREIGN KEY (movie_id, language_id)
        REFERENCES movie_language (movie_id, language_id),
    INDEX ix_screening_starts_at (starts_at)
);

CREATE TABLE purchase (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    screening_id      INT           NOT NULL REFERENCES screening (id),
    payment_method_id INT           NOT NULL REFERENCES payment_method (id),
    num_tickets       INT           NOT NULL CHECK (num_tickets > 0),
    total_amount      DECIMAL(8, 2) NOT NULL CHECK (total_amount >= 0),
    purchased_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
