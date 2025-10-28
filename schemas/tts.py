"""
TTS (Text-to-Speech) 스키마
"""

from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """TTS 요청 스키마"""

    text: str = Field(
        ...,
        description="음성으로 변환할 영어 텍스트",
        min_length=1,
        max_length=500,
        examples=["Hello World", "Good morning"],
    )


class TTSResponse(BaseModel):
    """TTS 응답 스키마"""

    success: bool = Field(
        ...,
        description="성공 여부",
    )
    file_url: str = Field(
        ...,
        description="오디오 파일 URL",
        examples=["/static/audio/ed076287532e86365e841e92bfc50d8c.mp3"],
    )
    cached: bool = Field(
        ...,
        description="캐시 사용 여부",
    )
    message: str = Field(
        default="",
        description="추가 메시지",
    )
