"""
TTS (Text-to-Speech) 서비스
edge-tts를 사용하여 영어 텍스트를 음성으로 변환하고 캐싱합니다.
"""

import os
import hashlib
import edge_tts
from pathlib import Path
from typing import Optional


class TTSService:
    """TTS 서비스 클래스"""

    # 음성 모델: en-US-AriaNeural (여자 음성) 고정
    VOICE = "en-US-AriaNeural"

    # 오디오 파일 저장 디렉토리
    AUDIO_DIR = Path(__file__).parent.parent / "static" / "audio"

    # 텍스트 최대 길이 제한
    MAX_TEXT_LENGTH = 500

    def __init__(self):
        """TTS 서비스 초기화 및 디렉토리 확인"""
        # 오디오 디렉토리가 없으면 생성
        self.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    def _create_hash(self, text: str) -> str:
        """
        텍스트를 정규화하고 MD5 해시를 생성합니다.

        Args:
            text: 원본 텍스트

        Returns:
            MD5 해시 문자열
        """
        # 텍스트 정규화: 소문자 변환 + 공백 제거
        normalized = text.lower().strip()

        # MD5 해시 생성
        hash_object = hashlib.md5(normalized.encode('utf-8'))
        return hash_object.hexdigest()

    def _get_audio_path(self, text: str) -> Path:
        """
        텍스트에 대응하는 오디오 파일 경로를 반환합니다.

        Args:
            text: 텍스트

        Returns:
            오디오 파일 경로 (Path 객체)
        """
        hash_value = self._create_hash(text)
        filename = f"{hash_value}.mp3"
        return self.AUDIO_DIR / filename

    def get_cached_audio(self, text: str) -> Optional[Path]:
        """
        캐시된 오디오 파일이 있는지 확인합니다.

        Args:
            text: 텍스트

        Returns:
            캐시된 파일 경로 (있으면) 또는 None
        """
        audio_path = self._get_audio_path(text)

        if audio_path.exists():
            return audio_path

        return None

    async def generate_speech(self, text: str) -> Path:
        """
        텍스트를 음성으로 변환합니다. 캐시가 있으면 캐시를 반환합니다.

        Args:
            text: 변환할 텍스트

        Returns:
            생성된 오디오 파일 경로

        Raises:
            ValueError: 텍스트가 비어있거나 너무 긴 경우
            Exception: TTS 생성 실패 시
        """
        # 입력 검증
        if not text or not text.strip():
            raise ValueError("텍스트가 비어있습니다.")

        if len(text) > self.MAX_TEXT_LENGTH:
            raise ValueError(f"텍스트가 너무 깁니다. (최대 {self.MAX_TEXT_LENGTH}자)")

        # 캐시 확인
        cached_path = self.get_cached_audio(text)
        if cached_path:
            return cached_path

        # 캐시가 없으면 새로 생성
        audio_path = self._get_audio_path(text)

        try:
            # edge-tts를 사용하여 음성 생성
            communicate = edge_tts.Communicate(text, self.VOICE)
            await communicate.save(str(audio_path))

            return audio_path

        except Exception as e:
            # 생성 실패 시 파일 삭제 (중간 상태 방지)
            if audio_path.exists():
                audio_path.unlink()

            raise Exception(f"TTS 생성 실패: {str(e)}")

    def delete_cache(self, text: str) -> bool:
        """
        특정 텍스트의 캐시를 삭제합니다.

        Args:
            text: 텍스트

        Returns:
            삭제 성공 여부
        """
        audio_path = self._get_audio_path(text)

        if audio_path.exists():
            audio_path.unlink()
            return True

        return False

    def clear_all_cache(self) -> int:
        """
        모든 오디오 캐시를 삭제합니다.

        Returns:
            삭제된 파일 수
        """
        count = 0

        for file_path in self.AUDIO_DIR.glob("*.mp3"):
            if file_path.is_file():
                file_path.unlink()
                count += 1

        return count
