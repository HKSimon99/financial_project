# 📊 Opendart 기반 종합 금융 분석 대시보드

이 프로젝트는 **Opendart API**, **KRX 업종 데이터**, **네이버 금융 주가**를 활용하여  
기업별 재무 분석, 업종 평균 비교, ESG 분석, 포트폴리오 최적화, PDF/Excel 보고서 생성을 수행하는 종합 대시보드입니다.

---

## 🚀 주요 기능

1. **단일 기업 분석**
   - 재무健全성 점수 계산 (부채비율, ROE, 유동비율, 영업이익률, 이자보상배율, Z-score)
   - Plotly 시각화
   - PDF 보고서 다운로드

2. **다중 기업 분석**
   - 여러 기업의 재무健全성 점수 일괄 계산
   - 업종 평균 비교
   - Excel 보고서 다운로드

3. **업종 평균 비교**
   - 업종별 평균 점수 시각화

4. **ESG 분석**
   - 사업보고서 또는 공시 텍스트에서 ESG 키워드 빈도 분석
   - 카테고리별 점수 비중 파이차트 시각화

---

## 📂 폴더 구조

financial_project/
│

---

## 🔑 실행 전 준비

1. from repository root

pip install -e packages/core

2. FastAPI 서버실행

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

3. Frontend 실행

cd apps/web
pnpm install
pnpm run lint
pnpm run dev

4. 데이터베이스 시드

uv run python scripts/seed_companies.py

# Python setup

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://user:pass@localhost/db
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_companies.py

# Backend

uvicorn backend.app.main:app --reload # SSE default
FF_LIVE_WS=true uvicorn backend.app.main:app # enable WebSocket
FF_SCREENERS=false uvicorn backend.app.main:app # disable screeners

# Frontend

cd apps/web
pnpm install
pnpm dev

# Tests

Backend tests are located in `backend/tests`. Run `pytest` from the repository root to execute them.
pytest
pnpm test
pnpm playwright test

# PWA build

pnpm build && pnpm start
