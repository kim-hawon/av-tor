# audio

TOR 2단계 음성 안내(TTS)용 `.wav` 파일을 두는 폴더입니다.
`src/hmi/speaker.py`가 시나리오 종류에 따라 아래 파일을 재생합니다.

| 파일 | 용도 |
|---|---|
| `tts_construction.wav` | 공사 구간 안내 |
| `tts_rain.wav` | 강우 안내 |
| `tts_fog.wav` | 안개 안내 |
| `tts_ice.wav` | 빙판 안내 |
| `tts_retry.wav` | 리드백 실패 시 재요청 |

## 규격(권장)
- 포맷: WAV (PCM)
- 샘플레이트: 16 kHz, 모노 (STT 입력과 통일)
- 16-bit

> 실제 음성 파일은 git에 커밋하지 말고 빌드/배포 시 채워 넣는 것을 권장합니다.
> (이 README가 빈 폴더를 git에 유지하는 역할도 합니다.)
