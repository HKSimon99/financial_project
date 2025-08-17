import os
import requests
import pandas as pd
import numpy as np  # np.nan 사용을 위해 추가
from fpdf import FPDF
import plotly.express as px
import logging
from io import BytesIO
from dotenv import load_dotenv  # API_KEY 로드를 위해 추가 (독립 실행시)

# src 폴더 내 모듈 임포트
from ._legacy_analysis import extract_fs_summary
from ._legacy_data_fetch import (
    load_or_create_corp_code_list,
)  # get_fiscal_month는 현재 사용되지 않지만, 혹시 모를 미래 확장을 위해 유지

# 로깅 설정 (다른 모듈과 일관성 유지)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 환경변수 로드 (이 모듈이 독립적으로 실행될 경우를 대비)
load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logging.warning(
        "API_KEY가 설정되지 않았습니다. .env 파일을 확인하거나 data_fetch 모듈이 먼저 실행되었는지 확인하세요."
    )

# 리포트 저장 경로 생성
os.makedirs("data/reports", exist_ok=True)
os.makedirs("data/fonts", exist_ok=True)  # 폰트 폴더 생성


# ---------------------------------------------------
# PDF 생성 클래스 확장
# ---------------------------------------------------
class PDFReport(FPDF):
    def __init__(self, orientation="P", unit="mm", format="A4"):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=True, margin=15)
        self.add_korean_font()  # 한글 폰트 추가
        self.set_font("CustomFont", "", 12)  # 기본 폰트 설정

    def add_korean_font(self):
        """
        한글 폰트(NotoSansKR-Regular.ttf)를 로드합니다.
        폰트 파일이 없으면 Arial로 대체됩니다.
        """
        # 폰트 파일 경로: 프로젝트 루트의 fonts/ 디렉토리
        font_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "fonts",
            "NotoSansKR-Regular.ttf",
        )
        font_path = os.path.normpath(font_path)  # 경로 정규화

        if os.path.exists(font_path):
            try:
                self.add_font("CustomFont", "", font_path, uni=True)
                logging.info(f"✅ 한글 폰트 로드 성공: {font_path}")
            except Exception as e:
                logging.error(
                    f"❌ 한글 폰트 로드 실패 ({font_path}): {e}. Arial로 대체됩니다.",
                    exc_info=True,
                )
                self.set_font("Arial", "", 12)
        else:
            logging.warning(
                f"❌ 한글 폰트 파일이 없습니다: {font_path}. Arial로 대체됩니다. fonts/NotoSansKR-Regular.ttf를 추가해주세요."
            )
            self.set_font("Arial", "", 12)  # 폰트 파일이 없으면 Arial로 대체

    def header(self):
        self.set_font("CustomFont", "B", 16)
        self.cell(0, 10, self.safe_text("기업 재무 분석 보고서"), ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("CustomFont", "I", 8)
        self.cell(0, 10, self.safe_text(f"페이지 {self.page_no()}/{{nb}}"), 0, 0, "C")

    def chapter_title(self, title):
        self.set_font("CustomFont", "B", 12)
        self.cell(0, 10, self.safe_text(title), ln=True)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("CustomFont", "", 10)
        self.multi_cell(0, 7, self.safe_text(body))
        self.ln()

    def add_image_from_bytes(self, img_bytes, w=180, h=0, x=None, y=None):
        """BytesIO 객체에서 이미지를 추가합니다."""
        try:
            self.image(img_bytes, x=x, y=y, w=w, h=h, type="PNG")
            self.ln(5)
        except Exception as e:
            logging.error(f"이미지 추가 중 오류 발생: {e}", exc_info=True)

    def safe_text(self, text):
        """FPDF 폰트가 지원하지 않는 문자를 제거합니다."""
        if self.font_family == "Arial":  # Arial 폰트 사용 시 이모티콘 등 제거
            return "".join(ch for ch in text if ord(ch) <= 0xFFFF)
        return text  # CustomFont는 유니코드 지원하므로 그대로 반환


# ---------------------------------------------------
# 헬퍼 함수: 기업 코드 정보 조회
# ---------------------------------------------------
def _get_corp_codes_info(corp_name: str) -> tuple[str, str]:
    """
    기업명으로 corp_code와 stock_code를 조회합니다.
    """
    corp_codes_df = load_or_create_corp_code_list()
    row = corp_codes_df[corp_codes_df["corp_name"] == corp_name]
    if row.empty:
        logging.error(f"기업명 '{corp_name}'에 해당하는 기업 코드를 찾을 수 없습니다.")
        raise ValueError(f"기업명 '{corp_name}'을(를) 찾을 수 없습니다.")

    row = row.iloc[0]
    corp_code = row["corp_code"]
    stock_code = (
        str(row["stock_code"]).zfill(6) if pd.notna(row["stock_code"]) else None
    )
    return corp_code, stock_code


# ---------------------------------------------------
# 헬퍼 함수: 기업 개요 및 로고 조회
# ---------------------------------------------------
def _fetch_company_overview_safe(corp_code: str) -> dict:
    """DART API에서 기업 개요를 안전하게 가져옵니다."""
    url = "https://opendart.fss.or.kr/api/company.json"
    params = {"crtfc_key": API_KEY, "corp_code": corp_code}
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()  # HTTP 에러 발생 시 예외 발생
        data = res.json()
        if data.get("status") == "000":
            logging.info(f"✅ 기업 개요 조회 성공: {corp_code}")
            return {
                "기업명": data.get("corp_name"),
                "영문명": data.get("corp_name_eng"),
                "업종": data.get("industry"),
                "설립일": data.get("est_dt"),
                "대표자": data.get("ceo_nm"),
                "홈페이지": data.get("hm_url"),
                "주소": data.get("adres"),
            }
        else:
            logging.warning(
                f"DART 기업 개요 조회 실패 ({corp_code}): {data.get('message', '알 수 없는 오류')}"
            )
            return {}
    except requests.exceptions.RequestException as e:
        logging.error(f"DART 기업 개요 API 요청 오류 ({corp_code}): {e}", exc_info=True)
        return {}
    except Exception as e:
        logging.error(
            f"기업 개요 처리 중 예상치 못한 오류 발생 ({corp_code}): {e}", exc_info=True
        )
        return {}


def _fetch_company_logo_safe(stock_code: str) -> BytesIO | None:
    """네이버 금융에서 기업 로고를 안전하게 가져옵니다."""
    if not stock_code:
        return None
    try:
        logo_url = (
            f"https://ssl.pstatic.net/imgfinance/chart/item/200x200/{stock_code}.png"
        )
        res = requests.get(logo_url, timeout=5)
        res.raise_for_status()
        if res.status_code == 200 and res.content:
            logging.info(f"✅ 기업 로고 조회 성공: {stock_code}")
            return BytesIO(res.content)
        else:
            logging.warning(
                f"기업 로고를 찾을 수 없거나 응답이 비어있습니다: {stock_code}"
            )
            return None
    except requests.exceptions.RequestException as e:
        logging.warning(f"기업 로고 다운로드 실패 ({stock_code}): {e}")
        return None
    except Exception as e:
        logging.error(
            f"기업 로고 처리 중 예상치 못한 오류 발생 ({stock_code}): {e}",
            exc_info=True,
        )
        return None


# ---------------------------------------------------
# 헬퍼 함수: Plotly 차트 생성
# ---------------------------------------------------
def _create_price_chart(price_df: pd.DataFrame, corp_name: str) -> BytesIO | None:
    """
    주가 추이 차트를 생성하고 BytesIO 객체로 반환합니다.
    """
    if (
        price_df.empty
        or "date" not in price_df.columns
        or "close" not in price_df.columns
    ):
        logging.warning(
            f"주가 데이터가 불완전하여 주가 차트를 생성할 수 없습니다: {corp_name}"
        )
        return None

    # price_df의 컬럼명을 영문화 (data_fetch에서 이미 처리되지만, 안전을 위해 다시 확인)
    if "날짜" in price_df.columns:
        price_df.rename(
            columns={
                "날짜": "date",
                "종가": "close",
                "전일비": "diff",
                "시가": "open",
                "고가": "high",
                "저가": "low",
                "거래량": "volume",
            },
            inplace=True,
        )

    fig_price = px.line(
        price_df,
        x="date",
        y="close",
        title=f"{corp_name} 주가 추이",
        labels={"date": "날짜", "close": "종가"},
        template="plotly_white",  # 깔끔한 배경
    )
    fig_price.update_layout(title_x=0.5)  # 제목 중앙 정렬
    try:
        img_bytes = BytesIO()
        fig_price.write_image(img_bytes, format="png", scale=2)  # 고해상도 PNG
        img_bytes.seek(0)
        logging.info(f"✅ 주가 차트 생성 성공: {corp_name}")
        return img_bytes
    except Exception as e:
        logging.error(f"주가 차트 이미지 생성 실패 ({corp_name}): {e}", exc_info=True)
        return None


def _create_ratio_chart(health: dict, corp_name: str, year: int) -> BytesIO | None:
    """
    주요 재무비율 차트를 생성하고 BytesIO 객체로 반환합니다.
    """
    if not health or all(pd.isna(v) for v in health.values()):
        logging.warning(
            f"재무 건전성 데이터가 없어 재무비율 차트를 생성할 수 없습니다: {corp_name}"
        )
        return None

    # 차트 데이터 준비
    ratio_names = [
        "ROE",
        "부채비율",
        "유동비율",
        "영업이익률",
        "이자보상배율",
        "Z-score",
    ]
    ratio_values = [
        health.get("roe", np.nan),
        health.get("debt_ratio", np.nan),
        health.get("current_ratio", np.nan),
        health.get("op_margin", np.nan),
        health.get("interest_coverage", np.nan),
        health.get("z_score", np.nan),
    ]

    # NaN 값은 차트에 표시되지 않도록 필터링
    filtered_ratios = [
        (name, value)
        for name, value in zip(ratio_names, ratio_values)
        if not pd.isna(value)
    ]
    if not filtered_ratios:
        logging.warning(
            f"유효한 재무비율 데이터가 없어 재무비율 차트를 생성할 수 없습니다: {corp_name}"
        )
        return None

    chart_df = pd.DataFrame(filtered_ratios, columns=["Ratio", "Value"])

    fig_ratio = px.bar(
        chart_df,
        x="Ratio",
        y="Value",
        title=f"{corp_name} 주요 재무비율 ({year})",
        labels={"Ratio": "재무비율", "Value": "값"},
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Pastel,  # 색상 팔레트 변경
    )
    fig_ratio.update_layout(title_x=0.5)
    try:
        img_bytes = BytesIO()
        fig_ratio.write_image(img_bytes, format="png", scale=2)
        img_bytes.seek(0)
        logging.info(f"✅ 재무비율 차트 생성 성공: {corp_name}")
        return img_bytes
    except Exception as e:
        logging.error(
            f"재무비율 차트 이미지 생성 실패 ({corp_name}): {e}", exc_info=True
        )
        return None


# ---------------------------------------------------
# Excel 보고서 저장 (기존 기능 유지)
# ---------------------------------------------------
def save_excel_report(
    df_results: pd.DataFrame,
    df_industry_avg: pd.DataFrame,
    filename: str = "financial_report.xlsx",
) -> str:
    """
    분석 결과를 Excel 파일로 저장합니다.
    """
    file_path = os.path.join("data/reports", filename)
    try:
        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            df_results.to_excel(writer, sheet_name="기업별 분석", index=False)
            df_industry_avg.to_excel(writer, sheet_name="업종별 평균")
        logging.info(f"✅ Excel 보고서 저장 완료: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"❌ Excel 보고서 저장 실패 ({file_path}): {e}", exc_info=True)
        return ""


# ---------------------------------------------------
# 통합 투자 리포트 생성 (PDF)
# ---------------------------------------------------
def generate_investment_report(
    corp_name: str, year: int, health: dict, fs_df: pd.DataFrame, price_df: pd.DataFrame
) -> BytesIO | None:
    """
    증권사 리서치센터 스타일의 통합 투자 리포트(PDF)를 생성합니다.

    Args:
        corp_name (str): 기업명.
        year (int): 분석 연도.
        health (dict): calculate_financial_health 함수에서 반환된 재무 건전성 지표.
        fs_df (pd.DataFrame): 재무제표 데이터 DataFrame.
        price_df (pd.DataFrame): 주가 데이터 DataFrame.

    Returns:
        BytesIO | None: 생성된 PDF 파일의 BytesIO 객체. 실패 시 None.
    """
    try:
        # 1. 기업 코드 및 주식 코드 조회
        corp_code, stock_code = _get_corp_codes_info(corp_name)
        if not corp_code:
            return None

        # 2. 기업 개요 및 로고 조회
        overview = _fetch_company_overview_safe(corp_code)
        logo_img_bytes = _fetch_company_logo_safe(stock_code)

        # 3. 재무제표 요약
        fs_summary = extract_fs_summary(fs_df)

        # 4. 차트 생성 (BytesIO로 직접 받음)
        price_chart_bytes = _create_price_chart(price_df, corp_name)
        ratio_chart_bytes = _create_ratio_chart(health, corp_name, year)

        # 5. PDF 생성 시작
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_left_margin(20)
        pdf.set_right_margin(20)

        # 제목 섹션
        pdf.set_font("CustomFont", "B", 24)
        pdf.cell(
            0, 15, pdf.safe_text(f"{corp_name} {year} 투자 리포트"), ln=True, align="C"
        )
        pdf.ln(5)

        # 로고 추가 (있다면)
        if logo_img_bytes:
            # 로고를 오른쪽 상단에 배치
            pdf.image(logo_img_bytes, x=pdf.w - 40, y=10, w=30)
            logo_img_bytes.seek(0)  # 재사용을 위해 포인터 초기화

        # 구분선
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.5)
        pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
        pdf.ln(10)

        # 종합 점수 및 등급
        pdf.set_font("CustomFont", "", 14)
        total_score_str = (
            f"{health['total_score']:.2f}"
            if not pd.isna(health.get("total_score"))
            else "N/A"
        )
        grade_str = health.get("grade", "N/A")
        pdf.cell(
            0,
            10,
            pdf.safe_text(f"✨ 종합 점수: {total_score_str} | 등급: {grade_str}"),
            ln=True,
        )
        pdf.ln(5)

        # 기업 개요
        if overview:
            pdf.set_font("CustomFont", "B", 14)
            pdf.cell(0, 10, pdf.safe_text("📄 기업 개요"), ln=True)
            pdf.set_font("CustomFont", "", 11)
            for k, v in overview.items():
                if v:
                    pdf.cell(0, 7, pdf.safe_text(f"{k}: {v}"), ln=True)
            pdf.ln(5)

        # 재무제표 요약
        if fs_summary:
            pdf.set_font("CustomFont", "B", 14)
            pdf.cell(0, 10, pdf.safe_text("📊 재무제표 요약"), ln=True)
            pdf.set_font("CustomFont", "", 11)
            for k, v in fs_summary.items():
                if not pd.isna(v):
                    pdf.cell(
                        0, 7, pdf.safe_text(f"{k}: {v:,.0f} 원"), ln=True
                    )  # 천단위 콤마, 원 표시
            pdf.ln(5)

        # 재무비율 차트
        if ratio_chart_bytes:
            pdf.add_page()  # 새 페이지에 차트 추가
            pdf.set_font("CustomFont", "B", 14)
            pdf.cell(0, 10, pdf.safe_text("📈 주요 재무비율 분석"), ln=True)
            pdf.ln(5)
            pdf.add_image_from_bytes(ratio_chart_bytes, w=180)
            ratio_chart_bytes.seek(0)  # 재사용을 위해 포인터 초기화
            pdf.ln(5)

        # 주가 차트
        if price_chart_bytes:
            if (
                pdf.get_y() > pdf.h - 80
            ):  # 현재 페이지 하단에 공간이 부족하면 새 페이지 시작
                pdf.add_page()
            pdf.set_font("CustomFont", "B", 14)
            pdf.cell(0, 10, pdf.safe_text("💹 주가 추이 분석"), ln=True)
            pdf.ln(5)
            pdf.add_image_from_bytes(price_chart_bytes, w=180)
            price_chart_bytes.seek(0)  # 재사용을 위해 포인터 초기화
            pdf.ln(5)

        # PDF를 BytesIO 객체로 저장
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)  # 스트림의 시작으로 포인터 이동

        logging.info(f"✅ '{corp_name}' {year} 투자 리포트 PDF 생성 완료.")
        return pdf_output

    except ValueError as e:
        logging.error(f"리포트 생성 오류 (데이터 문제): {e}")
        return None
    except Exception as e:
        logging.error(f"리포트 생성 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return None


# 기존 generate_investment_report_full 및 create_visual_pdf는 제거됨
# generate_investment_report 함수가 모든 기능을 통합함.
