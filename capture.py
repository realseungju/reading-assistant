# -*- coding: utf-8 -*-
import subprocess
import os

def preview_and_capture(filename="book_page.jpg", preview_seconds=5):
    """
    실시간 미리보기 후 사진을 촬영합니다.
    preview_seconds: 미리보기 시간 (초)
    """
    print(f"카메라 미리보기 시작... {preview_seconds}초 후 자동 촬영됩니다.")

    command = [
        "rpicam-still",
        "--qt-preview",
        "-t", str(preview_seconds * 1000),
        "-o", filename,
    ]

    try:
        subprocess.run(command, check=True)
        print(f"촬영 완료! 저장 위치: {os.path.abspath(filename)}")
    except subprocess.CalledProcessError as e:
        print(f"오류 발생: {e}")
    except FileNotFoundError:
        print("오류: 'rpicam-still' 명령어를 찾을 수 없습니다.")

if __name__ == "__main__":
    preview_and_capture(preview_seconds=5)
