#!/usr/bin/env bash
# Refresh data (real fix run if it happened), re-render Draft A, re-mix sound. About 2 minutes.
# Run from anywhere: bash C:/dev/devcon/hermes-hackathon/videos/remotion/rerender.sh
set -e
cd "$(dirname "$0")"
python ../make_data.py
npx remotion render SukiPulse out/suki-pulse-draft-a.mp4 --concurrency=8
python audio/cues.py
node ~/.claude/skills/motion-design/scripts/sfx.mjs audio/cues.json audio/sfx.wav
ffmpeg -y -v error -i out/suki-pulse-draft-a.mp4 -i audio/music.mp3 -i audio/sfx.wav -filter_complex \
  "[1:a]atrim=0:53.2,asetpts=PTS-STARTPTS,volume=0.4,afade=t=in:st=0:d=0.8,afade=t=out:st=50.7:d=2.5[m];[m][2:a]amix=inputs=2:normalize=0,apad[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a pcm_s16le -shortest audio/mixed.mkv
python ~/.claude/skills/promo-video/scripts/finish.py audio/mixed.mkv out/suki-pulse-draft-a-sound.mp4 --poster 48.6 out/poster-a.jpg
echo "done: out/suki-pulse-draft-a-sound.mp4"
