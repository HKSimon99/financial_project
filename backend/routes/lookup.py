from fastapi import APIRouter, Depends, HTTPException
import os
from core.services.lookup import company_info_by_stock
from core.services.logo import get_logo_cached
from core.clients.naver import NaverImageSearch

router = APIRouter()


def get_api_key() -> str:
    key = os.environ.get("API_KEY")
    if not key:
        raise HTTPException(
            status_code=500, detail="API_KEY is not set in the API process environment"
        )
    return key


def get_naver() -> NaverImageSearch:
    cid = os.environ.get("NAVER_SEARCH_CLIENT_ID")
    sec = os.environ.get("NAVER_SEARCH_CLIENT_SECRET")
    # 자격이 없어도 500 내지 말고, None credential로 동작(=null 리턴)
    return NaverImageSearch(client_id=cid, client_secret=sec)


@router.get("/company/{stock_code}")
async def company(stock_code: str, api_key: str = Depends(get_api_key)):
    info = await company_info_by_stock(stock_code, api_key=api_key)
    if not info:
        raise HTTPException(status_code=404, detail=f"Unknown stock_code: {stock_code}")
    return info


@router.get("/logo/{stock_code}")
async def logo(
    stock_code: str,
    company_name: str | None = None,
    api_key: str = Depends(get_api_key),
    naver: NaverImageSearch = Depends(get_naver),
):
    # 회사명이 없으면 DART로 조회해 이름 확보
    name = company_name
    if not name:
        info = await company_info_by_stock(stock_code, api_key=api_key)
        if not info:
            raise HTTPException(
                status_code=404, detail=f"Unknown stock_code: {stock_code}"
            )
        name = info["corp_name"]

    # 캐시 + 네이버 이미지 검색
    result = await get_logo_cached(naver, company_name=name, stock_code=stock_code)
    return result
