from fastapi import APIRouter
import pandas as pd
from core.clients.dart import DARTClient
from core.services.analysis import (
    calculate_financial_health,
    calculate_custom_ratios,
    extract_fs_summary,
    dcf_intrinsic_price,
    rim_intrinsic_price,
)
from ..models.analysis import FSRow, PricePoint, HealthOut, RatiosOut, DCFIn, RIMIn

router = APIRouter()


async def get_dart() -> DARTClient:
    import os

    return DARTClient(api_key=os.environ["API_KEY"])


@router.post("/financial-health", response_model=HealthOut)
async def financial_health(fs_rows: list[FSRow]):
    fs_df = pd.DataFrame([r.model_dump(by_alias=True) for r in fs_rows])
    result = calculate_financial_health(fs_df)
    return HealthOut(**result)


@router.post("/ratios", response_model=RatiosOut)
async def ratios(fs_rows: list[FSRow], prices: list[PricePoint]):
    fs_df = pd.DataFrame([r.model_dump(by_alias=True) for r in fs_rows])
    price_df = pd.DataFrame([p.model_dump() for p in prices])
    out = calculate_custom_ratios(fs_df, price_df)
    # handle alias for Korean field name
    return RatiosOut(
        PER=out.get("PER"),
        PBR=out.get("PBR"),
        **{"배당수익률(%)": out.get("배당수익률(%)")},
    )


@router.post("/fs-summary")
async def fs_summary(fs_rows: list[FSRow]):
    fs_df = pd.DataFrame([r.model_dump(by_alias=True) for r in fs_rows])
    return extract_fs_summary(fs_df)


@router.post("/dcf")
async def dcf(body: DCFIn):
    price = dcf_intrinsic_price(**body.model_dump())
    return {"intrinsic_price": price}


@router.post("/rim")
async def rim(body: RIMIn):
    price = rim_intrinsic_price(**body.model_dump())
    return {"intrinsic_price": price}
