#!/usr/bin/env bash
# av-tor 상태기계 데모 실행.
# 프로젝트 루트(av-tor)로 이동한 뒤 실행해야 상대경로(config/audio/models)가 맞는다.
set -e
cd "$(dirname "$0")/.."
python src/app.py
