import os
import requests
import zipfile
import io
import pandas as pd
import time
import aiohttp
import asyncio
import logging
import numpy as np
from xml.etree.ElementTree import parse
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# --- 기본 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
API_KEY = os.getenv("API_KEY")
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")

if not all([API_KEY, APP_KEY, APP_SECRET]):
    raise ValueError("API 키가 .env 파일에 올바르게 설정되지 않았습니다.")

CACHE_DIR = "data/cache"
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"
KIS_ACCESS_TOKEN_CACHE = {"token": None, "expires_at": None}
os.makedirs(CACHE_DIR, exist_ok=True)

# --- 캐싱 헬퍼 함수 ---
def _get_cache_path(cache_type, *args):
    return os.path.join(CACHE_DIR, cache_type, *[str(a) for a in args])

def _is_cache_valid(file_path, duration_days=0):
    if not os.path.exists(file_path): return False
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return (datetime.now() - file_mod_time) < timedelta(days=duration_days)

def _json_default(o):
    """numpy 숫자를 파이썬 기본형으로 변환"""
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    raise TypeError(f"{type(o)} is not JSON serializable")

def _save_data_to_cache(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        if isinstance(data, pd.DataFrame):
            data.to_parquet(file_path, index=False)
        elif isinstance(data, dict):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4, default=_json_default)
        logging.info(f"✅ 데이터 캐시 저장: {file_path}")
    except Exception as e:
        logging.error(f"❌ 캐시 저장 실패 ({file_path}): {e}")

def _load_data_from_cache(file_path):
    try:
        if file_path.endswith('.parquet'):
            return pd.read_parquet(file_path)
        elif file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        return None

# --- KIS API 공통 함수 ---
async def _get_kis_access_token_async(session):
    if KIS_ACCESS_TOKEN_CACHE["token"] and datetime.now() < KIS_ACCESS_TOKEN_CACHE["expires_at"]:
        return KIS_ACCESS_TOKEN_CACHE["token"]
    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    try:
        async with session.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(body), timeout=10) as resp:
            resp.raise_for_status()
            token_data = await resp.json()
            if "access_token" in token_data:
                token = token_data["access_token"]
                expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 86400) - 300)
                KIS_ACCESS_TOKEN_CACHE.update({"token": token, "expires_at": expires_at})
                return token
    except Exception as e:
        logging.error(f"❌ KIS 액세스 토큰 발급 실패: {e}")
    return None

async def _fetch_kis_data(session, url, tr_id, params):
    token = await _get_kis_access_token_async(session)
    if not token: return None
    headers = {
        "Authorization": f"Bearer {token}", "appkey": APP_KEY, "appsecret": APP_SECRET,
        "tr_id": tr_id, "custtype": "P"
    }
    try:
        async with session.get(url, headers=headers, params=params, timeout=10) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("rt_cd") == "0":
                return data
            else:
                logging.warning(f"KIS API 조회 실패 ({tr_id} / {params.get('fid_input_iscd')}): {data.get('msg1')}")
    except Exception as e:
        logging.error(f"❌ KIS API 요청 오류 ({tr_id}): {e}")
    return None

# --- 데이터 소스별 조회 함수 ---

def load_or_create_corp_code_list():
    filename = _get_cache_path('corp_codes', 'corp_code_list.parquet')
    if _is_cache_valid(filename, duration_days=1):
        cached_df = _load_data_from_cache(filename)
        if cached_df is not None: return cached_df
    try:
        dart_url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={API_KEY}"
        res = requests.get(dart_url)
        res.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(res.content)) as z, z.open('CORPCODE.xml') as f:
            tree = parse(f)
        root = tree.getroot()
        data = [(c.find('corp_code').text, c.find('corp_name').text, c.find('stock_code').text.strip()) for c in root.findall('list') if c.find('stock_code').text.strip()]
        dart_df = pd.DataFrame(data, columns=['corp_code', 'corp_name', 'stock_code'])
        dart_df['stock_code'] = dart_df['stock_code'].str.zfill(6)
        
        otp_url = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
        otp_form = {"mktId": "ALL", "trdDd": pd.Timestamp.today().strftime("%Y%m%d"), "url": "dbms/MDC/STAT/standard/MDCSTAT01901"}
        otp_res = requests.post(otp_url, data=otp_form, headers={"User-Agent": "Mozilla/5.0"})
        otp_res.raise_for_status()
        
        download_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
        krx_res = requests.post(download_url, data={"code": otp_res.text}, headers={"User-Agent": "Mozilla/5.0"})
        krx_res.raise_for_status()
        
        krx_df = pd.read_csv(io.BytesIO(krx_res.content), encoding="euc-kr")
        code_col = next((col for col in ['종목코드', '단축코드'] if col in krx_df.columns), None)
        if not code_col: raise KeyError("KRX 데이터에서 종목코드 컬럼을 찾을 수 없습니다.")
        
        krx_df.rename(columns={code_col: "stock_code", "기업명": "corp_name_krx", "시장구분": "market"}, inplace=True)
        krx_df["stock_code"] = krx_df["stock_code"].astype(str).str.zfill(6)
        
        merged_df = pd.merge(dart_df, krx_df[['stock_code', 'market']], on="stock_code", how="inner")
        _save_data_to_cache(merged_df, filename)
        return merged_df
    except Exception as e:
        logging.error(f"❌ 최신 상장사 목록 불러오기 실패: {e}", exc_info=True)
        return pd.DataFrame()

async def get_financial_statement_async(session, corp_code, year, return_report_name=False):
    report_configs = [("11011", "사업보고서"),("11014", "3분기보고서"),("11012", "반기보고서"),("11013", "1분기보고서")]
    fs_configs = [("CFS", "연결"),("OFS", "별도")]
    for rp_code, rp_name in report_configs:
        for fs_div, fs_name in fs_configs:
            cache_file = _get_cache_path('financials', corp_code, f'async_{year}_{rp_code}_{fs_div}.parquet')
            if _is_cache_valid(cache_file, duration_days=7):
                df = _load_data_from_cache(cache_file)
                if df is not None:
                    result = (corp_code, {"status": "000", "list": df.to_dict(orient='records')})
                    return (*result, f"{rp_name} - {fs_name}") if return_report_name else result
            url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
            params = {"crtfc_key": API_KEY, "corp_code": corp_code, "bsns_year": str(year), "reprt_code": rp_code, "fs_div": fs_div}
            try:
                await asyncio.sleep(0.1)
                async with session.get(url, params=params, timeout=10) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if data.get("status") == "000" and data.get("list"):
                        df = pd.DataFrame(data["list"])
                        _save_data_to_cache(df, cache_file)
                        result = (corp_code, data)
                        return (*result, f"{rp_name} - {fs_name}") if return_report_name else result
            except Exception as e:
                logging.error(f"DART API 오류 ({corp_code}, {year}, {rp_name}): {e}")
                error_result = (corp_code, {"status": "999", "message": str(e)}, None)
                return error_result if return_report_name else error_result[:2]

    logging.warning(f"❌ {corp_code}의 {year}년 재무제표를 찾을 수 없습니다.")
    final_result = (corp_code, {"status": "013", "message": "데이터 없음"})
    return (*final_result, "N/A") if return_report_name else final_result

async def get_kis_daily_price_async(session, stock_code, start_date, end_date):
    start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)
    cache_file = _get_cache_path('prices', stock_code, f'kis_{start_dt.strftime("%Y%m%d")}_{end_dt.strftime("%Y%m%d")}.parquet')
    if _is_cache_valid(cache_file, duration_days=1):
        df = _load_data_from_cache(cache_file)
        if df is not None: return stock_code, df
    
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": stock_code, "FID_INPUT_DATE_1": start_dt.strftime("%Y%m%d"), "FID_INPUT_DATE_2": end_dt.strftime("%Y%m%d"), "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "1"}
    data = await _fetch_kis_data(session, url, "FHKST01010400", params)
    
    if data and data.get("output"):
        df = pd.DataFrame(data["output"])
        df.rename(columns={"stck_bsop_date": "date", "stck_oprc": "open", "stck_hgpr": "high", "stck_lwpr": "low", "stck_clpr": "close", "acml_vol": "volume", "acml_tr_pbmn": "transaction_amount", "prdy_vrss": "change"}, inplace=True)
        final_cols = [col for col in ['date', 'open', 'high', 'low', 'close', 'volume', 'transaction_amount', 'change'] if col in df.columns]
        for col in final_cols:
            if col != 'date': df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df = df[final_cols].sort_values("date").reset_index(drop=True)
        _save_data_to_cache(df, cache_file)
        return stock_code, df

    return stock_code, pd.DataFrame()

# [신규] KIS API 상세 재무비율 조회
async def get_kis_financial_ratios_async(session, stock_code: str):
    cache_file = _get_cache_path('kis_ratios', f'{stock_code}.parquet')
    if _is_cache_valid(cache_file, duration_days=7):
        df = _load_data_from_cache(cache_file)
        if df is not None:
            return df

    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/finance/financial-ratio"
    params = {
        "fid_div_cls_code": "0",              # 0:연간, 1:분기 (필수)
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": stock_code,
    }
    data = await _fetch_kis_data(session, url, "FHKST66430300", params)
    if data and data.get("output"):
        df = pd.DataFrame(data["output"])
        cols = {
            'stac_yymm': '결산년월', 'grs_rt': '매출총이익률', 'bsop_prfi_inrt': '영업이익률',
            'thtr_ntin_inrt': '당기순이익률', 'roe_val': 'ROE', 'eps': 'EPS', 'bps': 'BPS',
            'pbr': 'PBR', 'dvd_yd_rt': '배당수익률'
        }
        df = df[[key for key in cols.keys() if key in df.columns]].rename(columns=cols)
        for col in df.columns:
            if col != '결산년월': df[col] = pd.to_numeric(df[col], errors='coerce')
        _save_data_to_cache(df, cache_file)
        return df
    return pd.DataFrame()

# [신규] KIS API 투자의견 조회
async def get_kis_investment_opinion_async(session, stock_code: str):
    cache_file = _get_cache_path('kis_opinion', f'{stock_code}.json')
    if _is_cache_valid(cache_file, duration_days=1):
        data = _load_data_from_cache(cache_file)
        if data:
            return data

    # ✅ 문서 기준 최신 경로 / TR_ID 사용
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/invest-opinion"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",        # 시장구분
        "FID_COND_SCR_DIV_CODE": "16633",     # 고정값(문서 PK)
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_DATE_1": (datetime.today() - timedelta(days=365)).strftime("%Y%m%d"),
        "FID_INPUT_DATE_2": datetime.today().strftime("%Y%m%d"),
    }
    data = await _fetch_kis_data(session, url, "FHKST663300C0", params)

    if data and data.get("output"):
        output = data["output"][0]
        
        opinion_data = {
            "opinion": output.get("invt_opnn"),                           # ex) 매수, 중립
            "target_price": float(output.get("hts_goal_prc") or 0),       # numpy → float
            "analyst_count": int(output.get("nm_of_analyst") or 0),       # 빈 값 → 0
        }
        _save_data_to_cache(opinion_data, cache_file)
        return opinion_data
    return {}

# --- 여러 기업 데이터 동시 조회 ---
async def fetch_multiple_financials(corp_codes, year):
    async with aiohttp.ClientSession() as session:
        tasks = [get_financial_statement_async(session, code, year) for code in corp_codes]
        results = await asyncio.gather(*tasks)
        return {code: data for code, data in results}

async def fetch_multiple_prices(stock_codes, start_date, end_date):
    async with aiohttp.ClientSession() as session:
        tasks = [get_kis_daily_price_async(session, code, start_date, end_date) for code in stock_codes]
        results = await asyncio.gather(*tasks)
        return {code: df for code, df in results if df is not None}