"""
Edge TTS 엔진 모듈
Microsoft Edge의 TTS 서비스를 활용한 음성 합성
"""

import asyncio
import edge_tts
import os
import base64
from typing import Optional

# ============================================================
# 🔧 관리자 설정 영역 - 여기서 음성을 설정하세요!
# ============================================================

# 사용할 음성 선택 (아래 중 하나를 DEFAULT_VOICE에 입력)
# 
# 한국어 음성 목록:
#   - "ko-KR-SunHiNeural"   : 선희 (여성, 밝고 친근한 음성) ⭐ 추천
#   - "ko-KR-InJoonNeural"  : 인준 (남성, 차분한 음성)
#
# 음성 속도: "-20%" (느리게) ~ "+20%" (빠르게), 기본값 "+0%"
# 음성 피치: "-10Hz" (낮게) ~ "+10Hz" (높게), 기본값 "+0Hz"

DEFAULT_VOICE = "ko-KR-SunHiNeural"  # 기본 음성
DEFAULT_RATE = "+0%"                  # 음성 속도
DEFAULT_PITCH = "+0Hz"                # 음성 피치

# ============================================================

async def text_to_speech_async(
    text: str,
    voice: str = None,
    rate: str = None,
    pitch: str = None,
    output_file: Optional[str] = None
) -> bytes:
    """
    텍스트를 음성으로 변환 (비동기)
    
    Args:
        text: 변환할 텍스트
        voice: 음성 종류 (None이면 관리자 설정값 사용)
        rate: 속도 조절 (None이면 관리자 설정값 사용)
        pitch: 피치 조절 (None이면 관리자 설정값 사용)
        output_file: 저장할 파일 경로 (선택)
    
    Returns:
        MP3 오디오 데이터 (bytes)
    """
    # 관리자 설정값 사용
    voice = voice or DEFAULT_VOICE
    rate = rate or DEFAULT_RATE
    pitch = pitch or DEFAULT_PITCH
    
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )
    
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    
    if output_file:
        with open(output_file, "wb") as f:
            f.write(audio_data)
    
    return audio_data


def text_to_speech(
    text: str,
    voice: str = None,
    rate: str = None,
    pitch: str = None,
    output_file: Optional[str] = None
) -> bytes:
    """
    텍스트를 음성으로 변환 (동기 래퍼)
    """
    return asyncio.run(text_to_speech_async(text, voice, rate, pitch, output_file))


def get_audio_base64(audio_bytes: bytes) -> str:
    """오디오 바이트를 base64로 인코딩"""
    return base64.b64encode(audio_bytes).decode()


def create_audio_player_html(audio_base64: str) -> str:
    """오디오 플레이어 HTML 생성"""
    return f'''
    <audio controls autoplay style="width: 100%;">
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        브라우저가 오디오 재생을 지원하지 않습니다.
    </audio>
    '''


async def list_available_voices():
    """사용 가능한 음성 목록 조회"""
    voices = await edge_tts.list_voices()
    korean_voices = [v for v in voices if v["Locale"].startswith("ko")]
    return korean_voices


if __name__ == "__main__":
    # 테스트
    test_text = "안녕하세요! 성동글로벌경영고등학교 AI 도우미입니다."
    audio = text_to_speech(test_text)
    print(f"생성된 오디오 크기: {len(audio)} bytes")
