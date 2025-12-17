"""
TTS (Text-to-Speech) API 라우터
"""

from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import FileResponse
from services.tts_service import TTSService
from pathlib import Path


# FastAPI Router 인스턴스 생성
router = APIRouter(
    prefix="/tts",
    tags=["Text-to-Speech"],
)


@router.get(
    "/speak",
    response_class=FileResponse,
    summary="Generate or Retrieve Cached Speech Audio",
    description="영어 텍스트를 음성(MP3)으로 변환합니다. 캐시가 있으면 캐시를 반환합니다.",
)
async def speak(
    text: str = Query(
        ...,
        description="음성으로 변환할 영어 텍스트",
        min_length=1,
        max_length=500,
        examples=["Hello World"],
    ),
):
    """
    영어 텍스트를 음성 파일(MP3)로 변환합니다.

    Args:
        text: 음성으로 변환할 영어 텍스트

    Returns:
        FileResponse: MP3 오디오 파일

    Raises:
        HTTPException 400: 잘못된 텍스트 입력
        HTTPException 500: TTS 생성 실패
    """
    try:
        # TTS 서비스 인스턴스 생성
        tts_service = TTSService()

        # 음성 생성 (캐시가 있으면 캐시 반환)
        audio_path = await tts_service.generate_speech(text)

        # 파일 응답 반환
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            filename=f"{text[:30]}.mp3",  # 파일명은 텍스트 앞부분 사용
            headers={
                "Cache-Control": "public, max-age=31536000",  # 1년 캐싱
            },
        )

    except ValueError as e:
        # 입력 검증 오류
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        # TTS 생성 실패
        print(f"[TTS Error] Failed to generate speech: {str(e)}")  # Error Logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성 생성에 실패했습니다: {str(e)}",
        )


@router.delete(
    "/cache",
    summary="Delete Cached Audio",
    description="특정 텍스트의 캐시된 오디오를 삭제합니다.",
)
async def delete_cache(
    text: str = Query(
        ...,
        description="삭제할 텍스트",
        min_length=1,
    ),
):
    """
    특정 텍스트의 캐시된 오디오를 삭제합니다.

    Args:
        text: 삭제할 텍스트

    Returns:
        dict: 삭제 결과
    """
    tts_service = TTSService()
    deleted = tts_service.delete_cache(text)

    if deleted:
        return {
            "success": True,
            "message": f"'{text}'의 캐시가 삭제되었습니다.",
        }
    else:
        return {
            "success": False,
            "message": f"'{text}'의 캐시를 찾을 수 없습니다.",
        }


@router.delete(
    "/cache/all",
    summary="Clear All Cached Audio",
    description="모든 캐시된 오디오를 삭제합니다.",
)
async def clear_all_cache():
    """
    모든 캐시된 오디오를 삭제합니다.

    Returns:
        dict: 삭제된 파일 수
    """
    tts_service = TTSService()
    count = tts_service.clear_all_cache()

    return {
        "success": True,
        "deleted_count": count,
        "message": f"{count}개의 캐시 파일이 삭제되었습니다.",
    }
