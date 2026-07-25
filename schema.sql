-- ============================================================
-- Library Management System — MySQL schema
-- Run this once to create the database, tables, and starter data:
-- ============================================================

CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

-- ---------------------------------------------------------------
-- Books on the shelf
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    genre VARCHAR(100),
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    added_date DATE DEFAULT CURRENT_DATE
);

-- ---------------------------------------------------------------
-- Registered library members
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    join_date DATE DEFAULT CURRENT_DATE
);

-- ---------------------------------------------------------------
-- Borrow / return history
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    fine DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    status ENUM('borrowed', 'returned') NOT NULL DEFAULT 'borrowed',
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------
-- Librarian / admin logins
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Default login
INSERT INTO admins (username, password)
VALUES (
    'admin',
    'scrypt:32768:8:1$5x6XV976mi3zZhud$a497956d0c5fae5c1f5afc347bad63fdc6121182a2b1a3a0d4ace0949438fef053e517adf316a7f6c3669b647b0390752b80e09d3a12358e99b5e7acc2cd928d'
)
ON DUPLICATE KEY UPDATE username = username;

-- ---------------------------------------------------------------
-- Sample books
-- ---------------------------------------------------------------
INSERT INTO books (title, author, isbn, genre, total_copies, available_copies) VALUES
('The Hobbit', 'J.R.R. Tolkien', '9780547928227', 'Fantasy', 3, 3),
('Dune', 'Frank Herbert', '9780441013593', 'Science Fiction', 2, 2),
('Pride and Prejudice', 'Jane Austen', '9780141439518', 'Classic', 2, 2),
('The Silent Patient', 'Alex Michaelides', '9781250301697', 'Thriller', 2, 2),
('Sapiens', 'Yuval Noah Harari', '9780062316097', 'Non-Fiction', 3, 3)
ON DUPLICATE KEY UPDATE title = title;

-- ---------------------------------------------------------------
-- Sample members
-- ---------------------------------------------------------------
INSERT INTO members (name, email, phone) VALUES
('Ava Thompson', 'ava.thompson@example.com', '555-0101'),
('Marcus Lee', 'marcus.lee@example.com', '555-0102'),
('Priya Nair', 'priya.nair@example.com', '555-0103')
ON DUPLICATE KEY UPDATE name = name;