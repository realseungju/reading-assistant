# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scans.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            author      TEXT,
            cover_image TEXT,
            created_at  TEXT    NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id         INTEGER,
            page_number     INTEGER,
            scanned_at      TEXT    NOT NULL,
            image_path      TEXT    NOT NULL,
            ocr_result      TEXT,
            processed_text  TEXT,
            summary         TEXT,
            ocr_confidence  REAL,
            is_favorite     INTEGER DEFAULT 0,
            memo            TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')

    conn.commit()
    conn.close()

def add_book(title, author="", cover_image=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO books (title, author, cover_image, created_at)
        VALUES (?, ?, ?, ?)
    ''', (title, author, cover_image, created_at))
    book_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return book_id

def get_all_books():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM books ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_book_by_id(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def save_scan(book_id, page_number, scanned_at, image_path, ocr_result, processed_text, summary, ocr_confidence=None, memo=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scans (book_id, page_number, scanned_at, image_path, ocr_result, processed_text, summary, ocr_confidence, memo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (book_id, page_number, scanned_at, image_path, ocr_result, processed_text, summary, ocr_confidence, memo))
    conn.commit()
    conn.close()

def get_all_scans():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, b.title, b.author
        FROM scans s
        LEFT JOIN books b ON s.book_id = b.id
        ORDER BY s.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_scans_by_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, b.title, b.author
        FROM scans s
        LEFT JOIN books b ON s.book_id = b.id
        WHERE s.book_id = ?
        ORDER BY s.page_number ASC
    ''', (book_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_favorite_scans():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, b.title, b.author
        FROM scans s
        LEFT JOIN books b ON s.book_id = b.id
        WHERE s.is_favorite = 1
        ORDER BY s.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def toggle_favorite(scan_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE scans SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    ''', (scan_id,))
    conn.commit()
    conn.close()

def delete_scan(scan_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT image_path FROM scans WHERE id = ?', (scan_id,))
    row = cursor.fetchone()
    cursor.execute('DELETE FROM scans WHERE id = ?', (scan_id,))
    conn.commit()
    conn.close()
    if row and row[0]:
        image_full_path = os.path.join(os.path.dirname(DB_PATH), "static", row[0])
        if os.path.exists(image_full_path):
            os.remove(image_full_path)

def delete_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT image_path FROM scans WHERE book_id = ?', (book_id,))
    scan_images = cursor.fetchall()
    cursor.execute('SELECT cover_image FROM books WHERE id = ?', (book_id,))
    cover = cursor.fetchone()
    cursor.execute('DELETE FROM scans WHERE book_id = ?', (book_id,))
    cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()
    for row in scan_images:
        if row[0]:
            path = os.path.join(os.path.dirname(DB_PATH), "static", row[0])
            if os.path.exists(path):
                os.remove(path)
    if cover and cover[0]:
        cover_path = os.path.join(os.path.dirname(DB_PATH), "static", cover[0])
        if os.path.exists(cover_path):
            os.remove(cover_path)

def get_scan_count_by_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM scans WHERE book_id = ?', (book_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count
