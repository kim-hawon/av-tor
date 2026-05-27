#!/usr/bin/env bash
# av-tor 상태기계 데모 실행.
# 프로젝트 루트(av-tor)로 이동한 뒤 실행해야 상대경로(config/audio/models)가 맞는다.
set -e
cd "$(dirname "$0")/.."
# python 이 없으면 python3 로 폴백 (맥 등)
if command -v python >/dev/null 2>&1; then
  python src/app.py
else
  python3 src/app.py
fi
