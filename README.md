# 📖 Reading Assistant

> AI-powered reading assistant built with Raspberry Pi 5.  
> 카메라로 책 페이지를 촬영하면 OCR, AI 요약, 번역, 퀴즈, 음성까지 한 번에 제공하는 통합 독서 보조 시스템입니다.

---

## 🎯 주요 기능

| 기능 | 설명 |
|------|------|
| 📷 **카메라 촬영** | 라즈베리파이 카메라로 책 페이지 촬영 (ROI 줌, 상하좌우 반전 지원) |
| 🔍 **OCR 텍스트 추출** | Google Cloud Vision API를 통한 텍스트 추출 및 신뢰도 분석 |
| 🤖 **AI 후처리 및 요약** | Gemini 2.5 Flash로 OCR 노이즈 제거 및 핵심 내용 요약 |
| 🌐 **번역** | 영어↔한국어 양방향 번역 (deep-translator) |
| 📝 **퀴즈 생성** | 스캔 내용 기반 객관식 2문제 + 주관식 1문제 자동 생성 |
| 🔊 **음성 변환** | 요약/원문 텍스트를 음성으로 변환하여 브라우저에서 재생 (gTTS) |
| 🧒 **어린이 단어 설명** | 텍스트 내 단어 클릭 시 Gemini AI가 어린이 눈높이로 설명 |
| 📚 **책 관리** | 책 표지 촬영으로 제목·저자 자동 추출, 스캔 기록 관리 |

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| **Hardware** | Raspberry Pi 5, Camera Module |
| **OCR** | Google Cloud Vision API |
| **AI** | Google Gemini 2.5 Flash |
| **번역** | deep-translator |
| **음성** | gTTS |
| **Backend** | Python, Flask |
| **Database** | SQLite |
| **Frontend** | HTML, CSS, JavaScript |

---

## 📁 프로젝트 구조

```
reading-assistant/
├── app.py                          # Flask 웹서버 및 API 라우팅
├── scan_and_ask.py                 # 촬영, OCR, AI 처리, DB 저장
├── database.py                     # SQLite DB 초기화 및 CRUD
├── my_translator.py                # 번역 모듈
├── quiz.py                         # 퀴즈 생성 모듈
├── voice.py                        # 음성 변환 모듈
├── webproject-405904-xxxx.json     # Google Cloud 인증 키 (Git 제외)
├── scans.db                        # SQLite DB (자동 생성)
├── static/
│   ├── images/                     # 스캔 이미지 저장
│   ├── covers/                     # 책 표지 이미지 저장
│   └── audio/                      # 음성 파일 저장
└── templates/
    ├── index.html                  # 스캔 기록 페이지
    └── books.html                  # 책 목록 페이지
```

---

## ⚙️ 설치 및 실행

### 1. 사전 준비

- Raspberry Pi 5 (OS: Bookworm)
- 카메라 모듈 연결
- Google Cloud Vision API 서비스 계정 키 (`.json`)
- Google Gemini API 키

### 2. 가상환경 생성 및 패키지 설치

```bash
python3 -m venv venv
source venv/bin/activate

pip install flask \
            google-cloud-vision \
            google-generativeai \
            google-genai \
            deep-translator \
            gtts
```

### 3. API 키 설정

`scan_and_ask.py` 및 `app.py` 상단의 설정 부분을 수정합니다:

```python
GOOGLE_VISION_CREDENTIALS = "your_project_api.json"  # Vision API 키 파일 경로
GEMINI_API_KEY = "your-gemini-api-key"                      # Gemini API 키
```

### 4. 책 스캔 실행

```bash
source venv/bin/activate
python3 scan_and_ask.py
```

### 5. 웹서버 실행

```bash
source venv/bin/activate
python3 app.py
```

브라우저에서 접속:
```
http://라즈베리파이IP:5000
```

라즈베리파이 IP 확인:
```bash
hostname -I
```

---

## 🗄️ DB 스키마

### books 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | 기본키 (자동 증가) |
| title | TEXT | 책 제목 |
| author | TEXT | 저자 |
| cover_image | TEXT | 표지 이미지 경로 |
| created_at | TEXT | 등록일시 |

### scans 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | 기본키 (자동 증가) |
| book_id | INTEGER | books 테이블 참조 |
| page_number | INTEGER | 페이지 번호 |
| scanned_at | TEXT | 스캔 일시 |
| image_path | TEXT | 스캔 이미지 경로 |
| ocr_result | TEXT | OCR 원문 |
| processed_text | TEXT | Gemini 후처리 원문 |
| summary | TEXT | Gemini 요약 |
| ocr_confidence | REAL | OCR 신뢰도 (0.0~1.0) |
| is_favorite | INTEGER | 즐겨찾기 여부 (0/1) |
| memo | TEXT | 사용자 메모 |

---

## 🌐 API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/` | 스캔 기록 페이지 |
| GET | `/books` | 책 목록 페이지 |
| POST | `/api/translate/<id>` | 번역 |
| POST | `/api/quiz/<id>` | 퀴즈 생성 |
| POST | `/api/voice/<id>` | 음성 변환 |
| POST | `/api/explain` | 단어 설명 (어린이 눈높이) |
| POST | `/favorite/<id>` | 즐겨찾기 토글 |
| POST | `/delete/<id>` | 스캔 삭제 |
| POST | `/delete_book/<id>` | 책 삭제 |

---

## 🚀 향후 개선 계획

- [ ] 다국어 번역 지원 확대
- [ ] 점자 출력 연동 (시각 장애인 접근성 강화)
- [ ] 어린이 맞춤 쉬운 말 요약 기능
- [ ] 사용자별 독서 이력 분석 및 맞춤형 학습 추천
- [ ] 모바일 앱 연동

---

## 👥 팀 정보

- **팀명**: 라스트댄스
- **학과**: 배재대학교 소프트웨어공학부 (컴퓨터공학전공)
- **학기**: 2026학년도 1학기 캡스톤디자인
