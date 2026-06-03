# -*- coding: utf-8 -*-
from gtts import gTTS
import os
import re

class ReadingAssistantVoice:
    def __init__(self):
        pass

    def clean_text(self, text):
        """마크다운 기호 제거"""
        text = re.sub(r'\*+', '', text)       # * ** 제거
        text = re.sub(r'#+\s?', '', text)      # # ## 제거
        text = re.sub(r'-{2,}', '', text)      # --- 제거
        text = re.sub(r'^\s*[-•]\s+', '', text, flags=re.MULTILINE)  # 목록 기호 제거
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # 링크 제거
        text = re.sub(r'\n{3,}', '\n\n', text) # 과도한 줄바꿈 제거
        return text.strip()

    def generate_audio(self, text, lang='ko'):
        if not text:
            return None, "읽을 내용이 없습니다."
        try:
            print(f"[{lang}] 모드로 음성 변환 중...")
            cleaned = self.clean_text(text)
            tts = gTTS(text=cleaned, lang=lang)
            filename = f"voice_{os.getpid()}.mp3"
            filepath = os.path.join("static", "audio", filename)
            os.makedirs(os.path.join("static", "audio"), exist_ok=True)
            tts.save(filepath)
            return f"audio/{filename}", None
        except Exception as e:
            return None, f"음성 출력 오류: {e}"
