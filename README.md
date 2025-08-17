# 📊 Opendart 기반 종합 금융 분석 대시보드

이 프로젝트는 **Opendart API**, **KRX 업종 데이터**, **네이버 금융 주가**를 활용하여 기업별 재무 분석, 업종 평균 비교, ESG 분석, 포트폴리오 최적화, 보고서 생성을 제공하는 풀스택 대시보드입니다.

## 🏗️ Architecture

- **backend/** – FastAPI 서비스와 배경 작업
- **apps/web/** – Next.js 기반 PWA 프론트엔드
- **packages/core/** – 백엔드와 스크립트에서 공유하는 Python 라이브러리
- **seeds/**, **scripts/** – 데이터 시드 및 유틸리티 스크립트
- `pnpm`/`pip`으로 관리되는 모노레포 구조

## 🚀 Setup

### Install dependencies

````bash
pip install -r requirements.txt
pip install -e packages/core
pnpm install

### Configure environment
`.env` 파일에 아래 환경 변수를 설정하고 PostgreSQL 인스턴스를 실행하세요.

### Database migration & seed
```bash
alembic upgrade head
python scripts/seed_companies.py

````

## 🔧 Feature Flags

| Flag              | Default | Description                                                         |
| ----------------- | ------- | ------------------------------------------------------------------- |
| `FF_LIVE_WS`      | `false` | `FF_WS_ENDPOINT`에 정의된 WebSocket을 사용하여 실시간 시세 스트리밍 |
| `FF_SCREENERS`    | `true`  | 주식 스크리너 API 노출 여부                                         |
| `FF_AI_EXPLAINER` | `false` | AI 설명 기능 활성화 (`OPENAI_API_KEY` 필요)                         |

## 🌍 Environment Variables

| Variable                 | Purpose                                                         |
| ------------------------ | --------------------------------------------------------------- |
| `APP_KEY` / `APP_SECRET` | 한국투자증권(KIS) API 키                                        |
| `API_KEY`                | OpenDART API 키                                                 |
| `DATABASE_URL`           | Postgres 연결 문자열 (`postgresql+psycopg://user:pass@host/db`) |
| `OPENAI_API_KEY`         | `FF_AI_EXPLAINER` 사용 시 필요                                  |
| `FF_WS_ENDPOINT`         | `FF_LIVE_WS=true`일 때 사용할 WebSocket 엔드포인트              |

## 📦 Seeding the Database

```bash
python scripts/seed_companies.py
```

## 🧪 Tests

백엔드:

```bash
pytest
```

프론트엔드 단위 테스트:

```bash
cd apps/web
pnpm test
```

프론트엔드 E2E 테스트:

```bash
cd apps/web
pnpm playwright test
```

## 💻 Development Servers

백엔드:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

특정 기능을 켜려면 환경 변수로 플래그를 전달하세요:

```bash
FF_LIVE_WS=true uvicorn backend.app.main:app
FF_SCREENERS=false uvicorn backend.app.main:app
```

프론트엔드:

```bash
cd apps/web
pnpm dev
```

## 🛠️ Troubleshooting

- 환경 변수가 누락되면 서버가 500 오류를 반환합니다.
- 데이터베이스 연결 오류 시 `DATABASE_URL`과 마이그레이션 적용 여부를 확인하세요.
- 프론트엔드가 실행되지 않으면 `pnpm install`을 다시 실행하세요.
- Playwright 브라우저 설치가 필요하면 `pnpm exec playwright install`을 실행하세요.

## 🤝 Contributing

1. 저장소를 포크하고 브랜치를 생성합니다.
2. 커밋은 작은 단위로 작성하고 명확한 메시지를 사용하세요.
3. PR 제출 전 모든 테스트와 린트를 실행하세요.
4. 변경 사항을 설명하는 Pull Request를 생성합니다.
