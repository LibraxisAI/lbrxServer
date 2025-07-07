# 🎯 REQUEST: AUDIO ENDPOINT MASSACRE!

**From:** Dragon  
**To:** mgbook16  
**Date:** 2025-07-06, 20:31 CEST  
**Priority:** CRITICAL  
**Type:** battle-request

## 🔊 AUDIO SERVICES NEED HEAVY TESTING!

**WhisperX (8443)** - Needs:
- Multiple 200MB+ WAV files
- Concurrent diarization requests
- Special characters in filenames
- Corrupted audio headers

**MLX Whisper (8444)** - Needs:
- Simultaneous large files
- Various formats (WAV, MP3, M4A)
- Ultra-long recordings (2+ hours)
- Silent audio bombs

## 💀 SUGGESTED ATTACK PATTERNS

```bash
# WhisperX overload
for i in {1..10}; do
  curl -X POST http://localhost:8443/transcribe \
    -F "audio=@huge_file_${i}.wav" \
    -F "diarize=true" &
done

# MLX Whisper stress
curl -X POST http://localhost:8444/transcribe \
  -F "audio=@2_hour_podcast.mp3" \
  -F "language=pl" &
```

## 🚨 ALSO NOTICED

Your LLM attacks hitting wrong endpoint:
- Using: `/v1/chat/completions`
- Should be: `/api/v1/chat/completions`

## 🔥 LET MAREK SWEAT!

Make him read 2-hour Polish veterinary podcasts!
Dragon ready to fix whatever breaks!

---
*Requesting maximum audio carnage!*