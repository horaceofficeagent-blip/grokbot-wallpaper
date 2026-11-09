#!/usr/bin/env bash
# Encode a loop-raw.wav (+ ir.wav) into a seamless m4a for web/audio/sound.js.
# Usage: build_loop.sh <work_dir> <cycle_sec> <overlap_sec> <out.m4a>
# Expects <work_dir>/loop-raw.wav and <work_dir>/ir.wav from make_*.py (3 cycles + tail).
set -euo pipefail
DIR=${1:?work dir}
CYCLE=${2:?cycle seconds}
OVERLAP=${3:?overlap seconds}
OUT=${4:?output m4a}
RAW="$DIR/loop-raw.wav"
IR="$DIR/ir.wav"
WET="$DIR/loop-wet.wav"
CUT="$DIR/loop-cut.wav"
test -f "$RAW" && test -f "$IR"

# Light convolution reverb, then take the steady middle cycle + overlap tail.
ffmpeg -y -hide_banner -loglevel error \
  -i "$RAW" -i "$IR" \
  -filter_complex "[0][1]afir=dry=0.82:wet=0.18[r];[r]alimiter=limit=0.95[a]" \
  -map "[a]" -c:a pcm_s16le "$WET"

# Start at one full cycle so the IR has already built up.
ffmpeg -y -hide_banner -loglevel error \
  -ss "$CYCLE" -t "$(python3 -c "print($CYCLE + $OVERLAP)")" \
  -i "$WET" -c:a pcm_s16le "$CUT"

ffmpeg -y -hide_banner -loglevel error \
  -i "$CUT" -c:a aac -b:a 128k -movflags +faststart "$OUT"

echo "wrote $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT") s)"
