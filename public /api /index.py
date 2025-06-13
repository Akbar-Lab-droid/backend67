# api/index.py
from flask import Flask, jsonify, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('perpustakaan.db')
    c = conn.cursor()
    
    # Create tables if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        publisher TEXT NOT NULL,
        year INTEGER NOT NULL,
        category TEXT NOT NULL,
        stock INTEGER NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        class TEXT NOT NULL,
        member_id TEXT NOT NULL UNIQUE,
        phone TEXT,
        email TEXT,
        status TEXT DEFAULT 'Aktif'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS borrows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        borrow_date DATE NOT NULL,
        return_date DATE NOT NULL,
        status TEXT DEFAULT 'Dipinjam',
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        borrow_id INTEGER NOT NULL,
        return_date DATE NOT NULL,
        fine INTEGER DEFAULT 0,
        reason TEXT,
        FOREIGN KEY (borrow_id) REFERENCES borrows(id)
    )''')
    
    # Insert sample data if tables are empty
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            ("Pemrograman JavaScript Modern", "Budi Raharjo", "Informatika", 2022, "Teknologi", 15),
            ("Fiqih Ibadah untuk Pemula", "Ust. Ahmad Syafi'i", "Pustaka Muslim", 2021, "Agama", 22),
            ("Matematika Kelas 9", "Dewi Sartika", "Erlangga", 2020, "Pelajaran", 18),
            ("Sejarah Peradaban Islam", "Prof. Dr. Hamka", "Pustaka Alvabet", 2019, "Sejarah", 12),
            ("Kumpulan Cerpen Islami", "Asma Nadia", "Republika", 2021, "Sastra", 20)
        ]
        c.executemany("INSERT INTO books (title, author, publisher, year, category, stock) VALUES (?, ?, ?, ?, ?, ?)", sample_books)
    
    c.execute("SELECT COUNT(*) FROM members")
    if c.fetchone()[0] == 0:
        sample_members = [
            ("Ahmad Fauzi", "9A", "MTSN001", "081234567890", "ahmad@example.com"),
            ("Siti Rahayu", "8B", "MTSN002", "081298765432", "siti@example.com"),
            ("Budi Santoso", "9C", "MTSN003", "085678901234", "budi@example.com"),
            ("Dewi Anggraini", "8A", "MTSN004", "087812345678", "dewi@example.com")
        ]
        c.executemany("INSERT INTO members (name, class, member_id, phone, email) VALUES (?, ?, ?, ?, ?)", sample_members)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Helper function to get database connection
def get_db():
    conn = sqlite3.connect('perpustakaan.db')
    conn.row_factory = sqlite3.Row
    return conn

# API Endpoints

# Dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    conn = get_db()
    c = conn.cursor()
    
    # Total books
    c.execute("SELECT COUNT(*) FROM books")
    total_books = c.fetchone()[0]
    
    # Active members
    c.execute("SELECT COUNT(*) FROM members WHERE status = 'Aktif'")
    active_members = c.fetchone()[0]
    
    # Active borrows
    c.execute("SELECT COUNT(*) FROM borrows WHERE status = 'Dipinjam'")
    active_borrows = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'totalBooks': total_books,
        'activeMembers': active_members,
        'activeBorrows': active_borrows
    })

# Books
@app.route('/books', methods=['GET'])
def get_books():
    search = request.args.get('search', '')
    conn = get_db()
    c = conn.cursor()
    
    if search:
        query = '''
            SELECT * FROM books 
            WHERE title LIKE ? OR author LIKE ? OR category LIKE ?
        '''
        c.execute(query, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        c.execute("SELECT * FROM books")
    
    books = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(books)

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = c.fetchone()
    conn.close()
    
    if book:
        return jsonify(dict(book))
    return jsonify({'error': 'Book not found'}), 404

@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    required_fields = ['title', 'author', 'publisher', 'year', 'category', 'stock']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO books (title, author, publisher, year, category, stock)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['title'],
        data['author'],
        data['publisher'],
        data['year'],
        data['category'],
        data['stock']
    ))
    conn.commit()
    book_id = c.lastrowid
    conn.close()
    
    return jsonify({'id': book_id}), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        UPDATE books SET 
        title = ?,
        author = ?,
        publisher = ?,
        year = ?,
        category = ?,
        stock = ?
        WHERE id = ?
    ''', (
        data.get('title', ''),
        data.get('author', ''),
        data.get('publisher', ''),
        data.get('year', 0),
        data.get('category', ''),
        data.get('stock', 0),
        book_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# Members
@app.route('/members', methods=['GET'])
def get_members():
    status = request.args.get('status', '')
    conn = get_db()
    c = conn.cursor()
    
    if status:
        c.execute("SELECT * FROM members WHERE status = ?", (status,))
    else:
        c.execute("SELECT * FROM members")
    
    members = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(members)

# Borrows
@app.route('/borrows', methods=['GET'])
def get_borrows():
    status = request.args.get('status', '')
    conn = get_db()
    c = conn.cursor()
    
    query = '''
        SELECT borrows.*, 
               members.name AS memberName, 
               members.class AS memberClass,
               books.title AS bookTitle
        FROM borrows
        JOIN members ON borrows.member_id = members.id
        JOIN books ON borrows.book_id = books.id
    '''
    
    if status:
        query += " WHERE borrows.status = ?"
        c.execute(query, (status,))
    else:
        c.execute(query)
    
    borrows = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(borrows)

# Returns
@app.route('/returns', methods=['GET'])
def get_returns():
    conn = get_db()
    c = conn.cursor()
    
    query = '''
        SELECT returns.*, 
               members.name AS memberName, 
               books.title AS bookTitle,
               borrows.borrow_date AS borrowDate
        FROM returns
        JOIN borrows ON returns.borrow_id = borrows.id
        JOIN members ON borrows.member_id = members.id
        JOIN books ON borrows.book_id = books.id
    '''
    
    c.execute(query)
    returns = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(returns)

# Popular books
@app.route('/popular-books', methods=['GET'])
def popular_books():
    conn = get_db()
    c = conn.cursor()
    
    query = '''
        SELECT books.id, books.title, books.author, books.category, COUNT(borrows.id) AS borrowCount
        FROM books
        LEFT JOIN borrows ON books.id = borrows.book_id
        GROUP BY books.id
        ORDER BY borrowCount DESC
        LIMIT 5
    '''
    
    c.execute(query)
    books = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(books)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
