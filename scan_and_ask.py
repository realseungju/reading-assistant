# -*- coding: utf-8 -*-
import google.generativeai as genai
from google.cloud import vision
import subprocess
import io
import os
import shutil
from datetime import datetime
from database import init_db, add_book, get_all_books, save_scan

# ===== 설정 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_VISION_CREDENTIALS = os.path.join(BASE_DIR, "Your_project_credentials.json")
GEMINI_API_KEY = "Your_API_Key_Here"
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images")
COVER_DIR = os.path.join(BASE_DIR, "static", "covers")
ROI = "0.25,0.25,0.5,0.5"
# ================

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_VISION_CREDENTIALS
genai.configure(api_key=GEMINI_API_KEY)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)

def take_photo(save_path, preview_seconds=5):
    print(f"카메라 미리보기 시작... {preview_seconds}초 후 자동 촬영됩니다.")
    command = [
        "rpicam-still",
        "--qt-preview",
        "-t", str(preview_seconds * 1000),
        "-o", save_path,
        "--roi", ROI,
        "--vflip",
        "--hflip",
    ]
    try:
        subprocess.run(command, check=True)
        print("촬영 완료!")
        return save_path
    except subprocess.CalledProcessError as e:
        print(f"촬영 오류: {e}")
        return None
    except FileNotFoundError:
        print("오류: 'rpicam-still' 명령어를 찾을 수 없습니다.")
        return None

def extract_text(image_path):
    print("Google Vision OCR 처리 중...")
    client = vision.ImageAnnotatorClient()
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    confidence = None
    if response.full_text_annotation.pages:
        confidences = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                confidences.append(block.confidence)
        if confidences:
            confidence = round(sum(confidences) / len(confidences), 4)

    if texts:
        return texts[0].description, confidence
    return None, None

def process_text(ocr_text):
    print("Gemini 원문 후처리 중...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""아래는 책이나 문제집을 카메라로 촬영해서 OCR로 추출한 텍스트야.

다음 작업을 수행해줘:
1. 깨진 글자나 의미없는 기호 제거
2. 잘못 인식된 숫자나 번호 최대한 복원
3. 문장 흐름이 어색한 부분 자연스럽게 정리
4. 원문의 내용과 구조는 최대한 유지
5. 없는 내용을 추가하거나 내용을 바꾸지 말 것
6. 마크다운 문법(*, **, #, - 등) 절대 사용 금지
7. 순수한 텍스트로만 출력

정리된 텍스트만 출력해줘. 설명이나 부연은 하지 마.

[OCR 원문]
{ocr_text}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def summarize_text(text):
    print("Gemini 요약 중...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""다음 텍스트를 한국어로 읽기 쉽게 요약해줘.
핵심 내용만 간결하게 정리해줘.
마크다운 문법(*, **, #, - 등) 절대 사용 금지.
순수한 텍스트로만 출력해줘.

[텍스트]
{text}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def parse_book_info(ocr_text):
    print("Gemini로 책 정보 파싱 중...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    extract_prompt = f"""아래는 책 표지를 OCR로 인식한 텍스트야.
이 텍스트에서 책 제목과 저자만 추출해줘.
반드시 아래 형식으로만 답해줘. 다른 말은 하지 마.

제목: (책 제목)
저자: (저자 이름)

[OCR 텍스트]
{ocr_text}
"""
    extract_response = model.generate_content(extract_prompt)
    extracted = extract_response.text.strip()

    title, author = "", ""
    for line in extracted.splitlines():
        if line.startswith("제목:"):
            title = line.replace("제목:", "").strip()
        elif line.startswith("저자:"):
            author = line.replace("저자:", "").strip()

    print(f"1차 추출 결과 → 제목: {title} / 저자: {author}")

    print("Gemini 검증 중...")
    verify_prompt = f"""아래는 책 표지 OCR 텍스트에서 추출한 책 정보야.
책 제목과 저자가 실제로 존재하는 책인지, 오탈자나 오인식된 부분은 없는지 검토해줘.
문제가 있으면 올바르게 수정하고, 없으면 그대로 반환해줘.
반드시 아래 형식으로만 답해줘. 다른 말은 하지 마.

제목: (책 제목)
저자: (저자 이름)
검증: (이상없음 / 수정됨 / 확인불가)
사유: (수정했다면 이유, 이상없으면 생략)

[추출된 정보]
제목: {title}
저자: {author}

[원본 OCR 텍스트]
{ocr_text}
"""
    verify_response = model.generate_content(verify_prompt)
    verified = verify_response.text.strip()

    verified_title, verified_author, status, reason = title, author, "", ""
    for line in verified.splitlines():
        if line.startswith("제목:"):
            verified_title = line.replace("제목:", "").strip()
        elif line.startswith("저자:"):
            verified_author = line.replace("저자:", "").strip()
        elif line.startswith("검증:"):
            status = line.replace("검증:", "").strip()
        elif line.startswith("사유:"):
            reason = line.replace("사유:", "").strip()

    if status == "수정됨":
        print(f"검증 후 수정됨 → 제목: {verified_title} / 저자: {verified_author}")
        if reason:
            print(f"수정 사유: {reason}")
    elif status == "확인불가":
        print(f"확인불가 → 제목: {verified_title} / 저자: {verified_author}")
        if reason:
            print(f"사유: {reason}")
    else:
        print("검증 완료 → 이상없음")

    return verified_title, verified_author

def register_book_by_text():
    title = input("책 제목: ").strip()
    author = input("저자: ").strip()
    book_id = add_book(title, author, cover_image=None)
    print(f"책 등록 완료! (ID: {book_id})")
    return book_id

def register_book_by_cover():
    temp_path = os.path.join(BASE_DIR, "temp_cover.jpg")
    result = take_photo(save_path=temp_path)
    if result is None:
        print("촬영 실패. 텍스트 입력으로 전환합니다.")
        return register_book_by_text()

    ocr_text, _ = extract_text(temp_path)
    if not ocr_text:
        print("텍스트 인식 실패. 직접 입력해주세요.")
        return register_book_by_text()

    print(f"\n--- OCR 인식 결과 ---\n{ocr_text}\n")

    title, author = parse_book_info(ocr_text)
    print(f"Gemini 파싱 결과 → 제목: {title} / 저자: {author}")

    title_confirm = input(f"책 제목 [{title}] (수정하려면 입력, 맞으면 Enter): ").strip()
    author_confirm = input(f"저자 [{author}] (수정하려면 입력, 맞으면 Enter): ").strip()

    if title_confirm:
        title = title_confirm
    if author_confirm:
        author = author_confirm

    cover_filename = "cover_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
    cover_path = os.path.join(COVER_DIR, cover_filename)
    shutil.copy(temp_path, cover_path)
    relative_cover_path = f"covers/{cover_filename}"

    book_id = add_book(title, author, cover_image=relative_cover_path)
    print(f"책 등록 완료! (ID: {book_id})")
    return book_id

def select_book():
    books = get_all_books()
    if books:
        print("\n=== 등록된 책 목록 ===")
        for book in books:
            print(f"  [{book[0]}] {book[1]} / {book[2]}")
        print("  [0] 새 책 등록")
        choice = input("\n책 번호를 선택하세요: ").strip()
        if choice != "0" and choice.isdigit():
            return int(choice)

    print("\n책 등록 방법을 선택하세요:")
    print("  [1] 텍스트 직접 입력")
    print("  [2] 책 표지 촬영")
    method = input("선택: ").strip()

    if method == "2":
        return register_book_by_cover()
    else:
        return register_book_by_text()

def scan_and_summarize():
    init_db()

    # 1. 책 선택 또는 등록
    book_id = select_book()

    # 2. 페이지 번호 입력
    page_number = input("페이지 번호 (모르면 Enter): ").strip()
    page_number = int(page_number) if page_number.isdigit() else None

    while True:
        # 3. 촬영
        temp_path = os.path.join(BASE_DIR, "temp_scan.jpg")
        image_path = take_photo(save_path=temp_path)
        if image_path is None:
            print("촬영 실패.")
            retry = input("다시 촬영하시겠습니까? (y/n): ").strip().lower()
            if retry == 'y':
                continue
            return

        # 4. OCR
        text, confidence = extract_text(temp_path)
        if text is None:
            print("텍스트를 찾을 수 없습니다.")
            retry = input("다시 촬영하시겠습니까? (y/n): ").strip().lower()
            if retry == 'y':
                continue
            return

        # 5. OCR 신뢰도 낮으면 경고
        if confidence and confidence < 0.7:
            print(f"\n⚠️  OCR 신뢰도가 낮습니다 ({confidence * 100:.1f}%). 글자가 제대로 인식되지 않았을 수 있어요.")
            retry = input("다시 촬영하시겠습니까? (y/n): ").strip().lower()
            if retry == 'y':
                continue

        # 6. Gemini 후처리
        processed = process_text(text)
        print("\n--- Gemini 후처리 원문 ---")
        print(processed)

        # 7. Gemini 요약
        summary = summarize_text(processed)
        print("\n--- Gemini 요약 결과 ---")
        print(summary)

        # 8. 재촬영 여부
        retry = input("\n결과가 만족스럽지 않으면 다시 촬영할 수 있습니다. 다시 촬영하시겠습니까? (y/n): ").strip().lower()
        if retry == 'y':
            continue

        # 9. 이미지 저장
        now = datetime.now()
        scanned_at = now.strftime("%Y-%m-%d %H:%M:%S")
        filename = now.strftime("%Y%m%d%H%M%S") + ".jpg"
        saved_image_path = os.path.join(IMAGE_DIR, filename)
        shutil.copy(temp_path, saved_image_path)
        relative_image_path = f"images/{filename}"

        # 10. 메모 입력
        memo = input("\n메모 입력 (없으면 Enter): ").strip()

        # 11. DB 저장 (processed_text 추가)
        save_scan(book_id, page_number, scanned_at, relative_image_path, text, processed, summary, confidence, memo)
        print(f"\nDB 저장 완료! ({scanned_at})")
        break

if __name__ == "__main__":
    scan_and_summarize()
