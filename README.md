# av-tor 🚗
> **Three-Phase Safety Protocol for Autonomous Vehicle Take-Over Request (TOR)**
> 
> **SAE Level 3 자율주행 환경에서 제한된 임베디드 자원(Raspberry Pi 4) 최적화를 고려한 온디바이스 다중 모달(Multi-modal) 제어권 전환 안전성 검증 시스템**

---

## 📌 Project Overview
본 프로젝트는 **SAE Level 3(조건부 자율주행)** 상황에서 시스템 한계 도달 시 발행되는 **TOR(Take-Over Request)** 시점의 안전 공백을 해결하기 위한 시스템입니다. 단순 이분법적 판단(Binary Handover)의 한계를 극복하고자, 운전자의 신체적·인지적 준비도(Driver Readiness)를 다차원적으로 검증하는 **3단계 직렬 시퀀셜 프로토콜**을 설계하고 엣지 컴퓨팅 환경에서 최적화하여 구현했습니다.

---

## 🛠️ Tech Stacks
*   **Hardware:** Raspberry Pi 4 (Quad-core CPU, No GPU/NPU Embedded Environment)
*   **Language & Library:** C/C++, Python, Linux (Raspberry Pi OS)
*   **Computer Vision & Audio AI:** Dlib (ERT Algorithm), MediaPipe, Vosk (Offline Kaldi-based STT)
*   **Protocols & Peripherals:** I2C Character LCD, TTP223 Capacitive Touch Sensor, MQTT (Telemetry), USB Camera

---

## 🚀 Key Engineering & Optimization Points

### 1. 실시간 안전성 보장을 위한 100% 온디바이스(Edge) 아키텍처
*   **SPOF(단일 장애점) 방지:** 네트워크 지연 및 음영 지역(터널 등)에서의 통신 단절로 인한 비상 제어 실패를 막기 위해, 클라우드 의존성을 100% 제거하고 모든 안전 제어 루프(TOR → 3단계 검증 → MRM)를 에지 단독으로 구동하도록 설계했습니다.
*   **계층 분리 구조:** 실시간 판단 루프는 로컬 엣지에서 닫고, 사후 분석을 위한 데이터 로그 및 텔레메트리는 MQTT를 통해 비동기 전송 처리하는 아키텍처를 확립했습니다.

### 2. 다중 모달 직렬 검증 스케줄링 및 파이프라인 최적화 (CPU 부하 완화)
*   **직렬 검증 시퀀스:** GPU가 없는 Raspberry Pi 4 환경에서 대형 AI 모델을 동시 구동 시 발생하는 실시간성 저하를 해결하기 위해, 검증 단계를 **[Phase 1: 시각+물리] ➡️ [Phase 2: 인지(음성)]**로 직렬 스케줄링하여 연산 오버헤드를 최소화했습니다.
*   **경량 안면 정렬:** 무거운 Deep Learning 파이프라인 대신, CPU 단에서 1ms 내외로 작동하는 **Dlib 프레임워크(ERT 알고리즘 기반)**를 통합하여 HELEN 데이터셋 기준 **0.049의 최적 오차율(Optimal Precision)**과 높은 리소스 효율성을 확보했습니다.
*   **수학적 생체 진단 지표:** 
    *   **졸음 검출:** 68 안면 랜드마크 기반의 $EAR(Eye\ Aspect\ Ratio) \le 0.2$ 판단 수식 적용
    *   **전방 주시 검출:** 코끝과 양안 중심점의 거리를 정규화한 $nose\_ratio$ 수식을 정의하여 유효 주시 마진($0.4 \le nose\_ratio \le 0.6$) 산출 및 실시간 융합 검증

### 3. 항공 관제 표준을 차용한 'Aviation Read-Back' 음성 검증 및 예외 처리
*   **오프라인 런타임 최적화:** 50MB 이하의 경량 오프라인 STT 엔진(**Vosk**)을 탑재하여 독립 가용성을 확보했습니다.
*   **Constrained Grammars 적용:** 오픈 도메인 인식 에러를 줄이기 위해 `SetGrammar()` 함수를 활용하여 유효 인식 어휘를 시나리오별 핵심 동작 토큰(Keyword Token)으로 강제 제한하는 최적화를 수행했습니다. 이를 통해 **60dB의 차량 내부 고속 주행 소음 환경에서도 최저 83% 이상의 정확도와 1~2초 이내의 빠른 응답성**을 확보했습니다.
*   **시스템 가용성 확장 (+3초 유예):** 차량 소음으로 인한 오인식이 즉시 비상 정차로 이어지는 오작동을 막고자 항공 관제의 'Say Again' 프로토콜을 벤치마킹하여, 인지 검증 단계에서만 **1회 재시도 및 3초의 유예 시간**을 부여하는 예외 처리 분기 로직을 결합했습니다.

### 4. 국제 안전 기준(UN R157) 기반 최소 위험 전략(MRM) 시뮬레이션
*   **Time Budget 산출 근거:** 운전자가 공간 지각력을 회복하는 데 필요한 인지 시간(선행 연구 Melcher et al. 기준 8.8초)을 고려하여, 위험 인지 시점을 400m 전방으로 설정하여 총 13초의 물리적 안전 예산(기본 10s + 음성 유예 3s)을 확보했습니다.
*   **점진적 비상 정차:** 예산 초과 시 고속 급제동으로 인한 후방 추돌을 방지하기 위해, UN R157 기준을 준수하여 **[최후 경고 ➡️ 비상등 점등 및 완만 감속(2.5m/s²) ➡️ 안전 정지]** 시퀀스를 구축하고, 실패 원인별(전방 미주시, 핸들 미파지, 인지 실패) 디스플레이 분기 시스템을 구체화했습니다.

---

## 📈 Evaluation & Benchmarks
*   **Face Alignment Precision:** Dlib ERT 프레임워크 적용을 통해 기존 EF 계열 알고리즘 대비 오차율 **0.049** 달성 (HELEN 데이터셋 검증 기준).
*   **Acoustic Robustness:** 주행 소음 가혹 조건(60dB) 환경에서 단어 사전 제한 최적화를 통해 실시간 추론 및 **83%** 이상의 Keyword Recognition Rate 방어.
