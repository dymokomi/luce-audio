#!/bin/sh
set -eu
cd "$(dirname "$0")"
BASE=${LUCE_BASE_COMPILER:-../luce-base/build/luce-base}
"$BASE" test src/luce_audio/audio.lucb --native
"$BASE" test src/luce_audio/audio.lucb --backend=c
