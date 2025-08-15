import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging

# 로깅 설정 (다른 모듈과 일관성 유지)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# ---------------------------------------------------
# 헬퍼 함수: 공통 레이아웃 업데이트
# ---------------------------------------------------
def _update_common_layout(fig: go.Figure, title: str, dark_mode: bool = False):
    """
    Plotly 차트의 공통 레이아웃을 업데이트합니다.
    Args:
        fig (go.Figure): Plotly Figure 객체.
        title (str): 차트 제목.
        dark_mode (bool): 다크 모드 적용 여부.
    """
    template = "plotly_dark" if dark_mode else "plotly_white"
    fig.update_layout(
        title_text=title,
        title_x=0.5,  # 제목 중앙 정렬
        template=template,
        hovermode="x unified",  # 마우스 오버 시 정보 표시 방식
        font=dict(
            family="Arial, sans-serif", size=12, color="white" if dark_mode else "black"
        ),
        paper_bgcolor=(
            "rgba(0,0,0,0)" if dark_mode else "rgba(0,0,0,0)"
        ),  # 배경 투명하게
        plot_bgcolor=(
            "rgba(0,0,0,0)" if dark_mode else "rgba(0,0,0,0)"
        ),  # 플롯 영역 배경 투명하게
    )
    # 축 색상 설정
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(150,150,150,0.2)" if dark_mode else "rgba(200,200,200,0.5)",
        zeroline=False,
        linecolor="rgba(150,150,150,0.5)" if dark_mode else "rgba(100,100,100,0.5)",
        tickfont=dict(color="white" if dark_mode else "black"),
        title_font=dict(color="white" if dark_mode else "black"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(150,150,150,0.2)" if dark_mode else "rgba(200,200,200,0.5)",
        zeroline=False,
        linecolor="rgba(150,150,150,0.5)" if dark_mode else "rgba(100,100,100,0.5)",
        tickfont=dict(color="white" if dark_mode else "black"),
        title_font=dict(color="white" if dark_mode else "black"),
    )


# ---------------------------------------------------
# 재무 비율 막대그래프
# ---------------------------------------------------
def plot_ratios(
    health_dict: dict, title: str = "주요 재무 비율", dark_mode: bool = False
) -> go.Figure:
    """
    재무 건전성 지표를 막대그래프로 시각화합니다.
    Args:
        health_dict (dict): 재무 건전성 지표 딕셔너리 (calculate_financial_health 결과).
        title (str): 차트 제목.
        dark_mode (bool): 다크 모드 적용 여부.
    Returns:
        go.Figure: Plotly Figure 객체.
    """
    if not health_dict or all(pd.isna(v) for v in health_dict.values()):
        logging.warning(
            "재무 건전성 데이터가 비어있어 재무 비율 차트를 생성할 수 없습니다."
        )
        fig = go.Figure()
        _update_common_layout(fig, f"{title} (데이터 없음)", dark_mode)
        return fig

    # total_score와 grade 제외
    df_ratios = pd.DataFrame(health_dict.items(), columns=["지표", "값"])
    df_ratios = df_ratios[~df_ratios["지표"].isin(["total_score", "grade"])]

    # NaN 값 제거 (차트에 표시되지 않도록)
    df_ratios = df_ratios.dropna(subset=["값"])

    if df_ratios.empty:
        logging.warning("유효한 재무 비율 데이터가 없어 차트를 생성할 수 없습니다.")
        fig = go.Figure()
        _update_common_layout(fig, f"{title} (데이터 없음)", dark_mode)
        return fig

    fig = px.bar(
        df_ratios,
        x="지표",
        y="값",
        text="값",
        color="지표",
        color_discrete_sequence=px.colors.qualitative.Pastel,  # 부드러운 색상 팔레트
    )
    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        marker_line_color="rgb(8,48,107)",
        marker_line_width=1.5,
        opacity=0.8,
    )
    fig.update_layout(yaxis_title="값", xaxis_title="지표", showlegend=False)

    _update_common_layout(fig, title, dark_mode)
    logging.info(f"✅ 재무 비율 차트 생성 완료: {title}")
    return fig


# ---------------------------------------------------
# 주가 데이터 시각화 (라인 차트 또는 캔들스틱 차트)
# ---------------------------------------------------
def plot_price(
    price_df: pd.DataFrame,
    corp_name: str,
    chart_type: str = "line",
    dark_mode: bool = False,
) -> go.Figure:
    """
    주가 데이터를 라인 차트 또는 캔들스틱 차트로 시각화합니다.
    Args:
        price_df (pd.DataFrame): 주가 데이터 DataFrame (date, open, high, low, close, volume 컬럼 포함).
        corp_name (str): 기업명.
        chart_type (str): "line" (라인 차트) 또는 "candlestick" (캔들스틱 차트). 기본값 "line".
        dark_mode (bool): 다크 모드 적용 여부.
    Returns:
        go.Figure: Plotly Figure 객체.
    """
    if price_df.empty or "date" not in price_df.columns:
        logging.warning(
            f"{corp_name} 주가 데이터가 비어있거나 'date' 컬럼이 없어 차트를 생성할 수 없습니다."
        )
        fig = go.Figure()
        _update_common_layout(fig, f"{corp_name} 주가 추이 (데이터 없음)", dark_mode)
        return fig

    # 컬럼명 영문화 (data_fetch에서 이미 처리되지만, 안전을 위해 다시 확인)
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

    # 'date' 컬럼을 datetime으로 변환
    price_df["date"] = pd.to_datetime(price_df["date"])
    price_df = price_df.sort_values("date")  # 날짜 오름차순 정렬

    fig = go.Figure()
    chart_title = f"{corp_name} 주가 추이"

    if chart_type == "candlestick":
        # 캔들스틱 차트 생성에 필요한 컬럼 확인
        required_cols = ["open", "high", "low", "close"]
        if not all(col in price_df.columns for col in required_cols):
            logging.warning(
                f"캔들스틱 차트 생성에 필요한 컬럼({required_cols})이 부족합니다. 라인 차트로 대체합니다."
            )
            chart_type = "line"  # 필요한 컬럼이 없으면 라인 차트로 대체

        if chart_type == "candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=price_df["date"],
                    open=price_df["open"],
                    high=price_df["high"],
                    low=price_df["low"],
                    close=price_df["close"],
                    name="주가",
                )
            )
            chart_title = f"{corp_name} 주가 캔들스틱 차트"
            fig.update_layout(
                xaxis_rangeslider_visible=False
            )  # 캔들스틱 기본 슬라이더 숨김

    if chart_type == "line":
        fig.add_trace(
            go.Scatter(
                x=price_df["date"],
                y=price_df["close"],
                mode="lines",
                name="종가",
                line=dict(color="royalblue", width=2),
            )
        )
        chart_title = f"{corp_name} 주가 라인 차트"

    # 범위 슬라이더 추가
    fig.update_layout(
        xaxis_rangeslider_visible=True,
        xaxis_rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all"),
                ]
            )
        ),
    )

    _update_common_layout(fig, chart_title, dark_mode)
    logging.info(f"✅ 주가 차트 생성 완료: {corp_name} ({chart_type})")
    return fig


# ---------------------------------------------------
# 업종별 평균 지표 막대그래프
# ---------------------------------------------------
def plot_industry_avg(
    industry_avg_df: pd.DataFrame,
    title: str = "업종별 평균 총점",
    dark_mode: bool = False,
) -> go.Figure:
    """
    업종별 평균 총점을 막대그래프로 시각화합니다.
    Args:
        industry_avg_df (pd.DataFrame): 업종별 평균 데이터 DataFrame.
        title (str): 차트 제목.
        dark_mode (bool): 다크 모드 적용 여부.
    Returns:
        go.Figure: Plotly Figure 객체.
    """
    if (
        industry_avg_df.empty
        or "업종" not in industry_avg_df.columns
        or "total_score" not in industry_avg_df.columns
    ):
        logging.warning(
            "업종별 평균 데이터가 비어있거나 필수 컬럼이 없어 업종 평균 차트를 생성할 수 없습니다."
        )
        fig = go.Figure()
        _update_common_layout(fig, f"{title} (데이터 없음)", dark_mode)
        return fig

    # '총점' 대신 'total_score' 컬럼 사용 (analysis.py의 calculate_financial_health 결과와 일관성 유지)
    df = industry_avg_df.reset_index()

    fig = px.bar(
        df,
        x="업종",
        y="total_score",  # '총점' 대신 'total_score' 사용
        text="total_score",
        color="업종",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        marker_line_color="rgb(8,48,107)",
        marker_line_width=1.5,
        opacity=0.8,
    )
    fig.update_layout(yaxis_title="총점", xaxis_title="업종", showlegend=False)

    _update_common_layout(fig, title, dark_mode)
    logging.info(f"✅ 업종별 평균 차트 생성 완료: {title}")
    return fig


# ---------------------------------------------------
# 개별 기업 vs 업종 평균 지표 비교 막대그래프 (새로 추가)
# ---------------------------------------------------
def plot_company_vs_industry_avg(
    company_data: pd.Series,
    industry_avg_df: pd.DataFrame,
    metric_name: str,
    company_name: str,
    dark_mode: bool = False,
) -> go.Figure:
    """
    개별 기업의 특정 지표를 해당 기업의 업종 평균과 비교하는 막대그래프를 생성합니다.
    Args:
        company_data (pd.Series): 선택된 기업의 분석 결과 (예: multi_results_df의 한 행).
        industry_avg_df (pd.DataFrame): 업종별 평균 데이터 DataFrame.
        metric_name (str): 비교할 지표의 이름 (예: '총점', 'ROE', 'PER').
        company_name (str): 비교할 기업의 이름.
        dark_mode (bool): 다크 모드 적용 여부.
    Returns:
        go.Figure: Plotly Figure 객체.
    """
    if (
        company_data.empty
        or metric_name not in company_data.index
        or pd.isna(company_data[metric_name])
    ):
        logging.warning(
            f"기업 '{company_name}'의 '{metric_name}' 데이터가 유효하지 않아 비교 차트를 생성할 수 없습니다."
        )
        fig = go.Figure()
        _update_common_layout(
            fig,
            f"'{company_name}' vs 업종 평균 ({metric_name}) (데이터 없음)",
            dark_mode,
        )
        return fig

    company_industry = company_data.get("업종", "알 수 없음")

    # 해당 업종의 평균값 찾기
    industry_avg_value = np.nan
    if "업종" in industry_avg_df.columns and metric_name in industry_avg_df.columns:
        avg_row = industry_avg_df[industry_avg_df["업종"] == company_industry]
        if not avg_row.empty:
            industry_avg_value = avg_row.iloc[0][metric_name]

    if pd.isna(industry_avg_value):
        logging.warning(
            f"업종 '{company_industry}'의 '{metric_name}' 평균 데이터를 찾을 수 없어 비교 차트를 생성할 수 없습니다."
        )
        fig = go.Figure()
        _update_common_layout(
            fig,
            f"'{company_name}' vs 업종 평균 ({metric_name}) (업종 평균 데이터 없음)",
            dark_mode,
        )
        return fig

    # 차트 데이터 생성
    data = {
        "Category": [company_name, f"{company_industry} 평균"],
        "Value": [company_data[metric_name], industry_avg_value],
    }
    df_plot = pd.DataFrame(data)

    fig = px.bar(
        df_plot,
        x="Category",
        y="Value",
        text="Value",
        title=f"'{company_name}' ({company_industry}) vs 업종 평균: {metric_name}",
        labels={"Category": "구분", "Value": metric_name},
        color="Category",
        color_discrete_map={
            company_name: px.colors.qualitative.Pastel[0],  # 기업 색상
            f"{company_industry} 평균": px.colors.qualitative.Pastel[
                1
            ],  # 업종 평균 색상
        },
    )
    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        marker_line_color="rgb(8,48,107)",
        marker_line_width=1.5,
        opacity=0.8,
    )
    fig.update_layout(showlegend=False)  # 범례 숨기기

    _update_common_layout(
        fig,
        f"'{company_name}' ({company_industry}) vs 업종 평균: {metric_name}",
        dark_mode,
    )
    logging.info(
        f"✅ 기업 vs 업종 평균 비교 차트 생성 완료: {company_name} - {metric_name}"
    )
    return fig
