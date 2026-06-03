# -*- coding: utf-8 -*-
from deep_translator import GoogleTranslator

class ReadingAssistantTranslator:
    def __init__(self):
        pass

    def get_translation(self, text, mode='en_to_ko'):
        if not text:
            return "내용이 없습니다."
        if mode == 'en_to_ko':
            source_lang, target_lang = 'en', 'ko'
            desc = "영->한"
        else:
            source_lang, target_lang = 'ko', 'en'
            desc = "한->영"
        try:
            print(f"[{desc}] 모드로 번역 중...")
            translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
            return translated
        except Exception as e:
            return f"번역 모듈 오류: {e}"
