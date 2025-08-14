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
├── data/
│ └── reports/
│
├── src/
│ ├── data_fetch.py
│ ├── analysis.py
│ ├── visualization.py
│ ├── portfolio.py
│ ├── report_generator.py
│ └── utils.py
│
├── dashboard/
│ ├── app.py
│ └── pages/
│ ├── 1_단일기업분석.py
│ ├── 2_다중기업분석.py
│ └── 3_업종평균비교.py
│ 
├── requirements.txt
└── README.md
---

## 🔑 실행 전 준비
1. **Opendart API Key 발급**
   - [opendart.fss.or.kr](https://opendart.fss.or.kr/) 회원가입 → API 인증키 발급
   - `src/data_fetch.py` 상단의 `API_KEY = "YOUR_API_KEY"` 부분 수정

2. **라이브러리 설치**
   ```bash
   pip install -r requirements.txt

3. 폴더 생성

mkdir -p data/reports

4. 실행방법
streamlit run dashboard/app.py
