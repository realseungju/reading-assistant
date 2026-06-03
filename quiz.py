# -*- coding: utf-8 -*-
from google import genai

class ReadingAssistantQuiz:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def generate_quiz(self, text):
        if not text:
            return "퀴즈 생성할 내용이 없습니다."
        print("[OCR 원문 기반] 퀴즈 생성 중...")
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""
다음 내용을 바탕으로 학습용 퀴즈를 만들어줘.
조건:
- 객관식 2문제 (4지선다)
- 주관식 1문제
- 정답 포함
- 한국어로 작성
[내용]
{text}
"""
            )
            return response.text
        except Exception as e:
            return f"퀴즈 생성 오류: {e}"
