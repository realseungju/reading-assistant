# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import init_db, get_all_scans, get_all_books, get_scans_by_book, get_favorite_scans, toggle_favorite, delete_scan, delete_book, get_scan_count_by_book
from my_translator import ReadingAssistantTranslator
from quiz import ReadingAssistantQuiz
from voice import ReadingAssistantVoice
from google import genai
import sqlite3
import os
from database import DB_PATH
import re

app = Flask(__name__)
GEMINI_API_KEY = "Your_API_Key_Here"
quiz_gen = ReadingAssistantQuiz(api_key=GEMINI_API_KEY)
translator = ReadingAssistantTranslator()
voice = ReadingAssistantVoice()

@app.route("/")
def index():
    init_db()
    book_id = request.args.get("book_id", type=int)
    favorite_only = request.args.get("favorite") == "1"
    books = get_all_books()
    if favorite_only:
        scans = get_favorite_scans()
    elif book_id:
        scans = get_scans_by_book(book_id)
    else:
        scans = get_all_scans()
    return render_template("index.html", scans=scans, books=books, selected_book=book_id, favorite_only=favorite_only)

@app.route("/books")
def books():
    init_db()
    all_books = get_all_books()
    books_with_count = []
    for book in all_books:
        count = get_scan_count_by_book(book[0])
        books_with_count.append({
            "id": book[0],
            "title": book[1],
            "author": book[2],
            "cover_image": book[3],
            "created_at": book[4],
            "scan_count": count
        })
    return render_template("books.html", books=books_with_count)

@app.route("/favorite/<int:scan_id>", methods=["POST"])
def favorite(scan_id):
    toggle_favorite(scan_id)
    return redirect(request.referrer or url_for("index"))

@app.route("/delete/<int:scan_id>", methods=["POST"])
def delete(scan_id):
    delete_scan(scan_id)
    return redirect(request.referrer or url_for("index"))

@app.route("/delete_book/<int:book_id>", methods=["POST"])
def delete_book_route(book_id):
    delete_book(book_id)
    return redirect(url_for("books"))

# 번역 API
@app.route("/api/translate/<int:scan_id>", methods=["POST"])
def translate(scan_id):
    mode = request.json.get("mode", "en_to_ko")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT processed_text FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]:
        return jsonify({"error": "OCR 결과가 없습니다."}), 404
    result = translator.get_translation(row[0], mode=mode)
    return jsonify({"result": result})

# 퀴즈 API
@app.route("/api/quiz/<int:scan_id>", methods=["POST"])
def quiz(scan_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT processed_text FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]:
        return jsonify({"error": "OCR 결과가 없습니다."}), 404
    result = quiz_gen.generate_quiz(row[0])
    return jsonify({"result": result})

# 음성 API (브라우저 재생용)
@app.route("/api/voice/<int:scan_id>", methods=["POST"])
def voice_play(scan_id):
    content_type = request.json.get("content_type", "summary")
    lang = request.json.get("lang", "ko")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT processed_text, summary FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "데이터가 없습니다."}), 404
    text = row[0] if content_type == "ocr" else row[1]
    if not text:
        return jsonify({"error": "읽을 내용이 없습니다."}), 404
    audio_path, error = voice.generate_audio(text, lang=lang)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"audio_url": url_for("static", filename=audio_path)})
    
# 어린이 단어 설명 API
@app.route("/api/explain", methods=["POST"])
def explain_word():
    word = request.json.get("word", "")
    context = request.json.get("context", "")
    if not word:
        return jsonify({"error": "단어가 없습니다."}), 400

    try:
        import google.generativeai as genai_old
        genai_old.configure(api_key=GEMINI_API_KEY)
        model = genai_old.GenerativeModel("gemini-2.5-flash")

        # 영어 단어 여부 확인
        is_english = bool(re.search(r'[a-zA-Z]', word))

        if is_english:
            prompt = f"""초등학생도 이해할 수 있도록 영어 단어를 설명해줘.
조건:
- 먼저 한국어 뜻을 알려줘 (예: "사과"라는 뜻이에요)
- 단어의 의미를 2~3문장으로 쉽게 설명해줘
- 실생활 예시나 비유를 들어줘
- 마크다운 문법 절대 사용 금지
- 설명만 출력, 다른 말 하지 마

영어 단어: {word}
문맥: {context}
"""
        else:
            prompt = f"""초등학생도 이해할 수 있도록 단어를 설명해줘.
조건:
- 2~3문장 이내로 짧게
- 쉬운 말만 사용
- 비유나 예시를 들어 설명
- 마크다운 문법 절대 사용 금지
- 설명만 출력, 다른 말 하지 마

단어: {word}
문맥: {context}
"""

        response = model.generate_content(prompt)
        return jsonify({"explanation": response.text.strip()})
    except Exception as e:
        return jsonify({"error": f"설명 오류: {str(e)}"}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
