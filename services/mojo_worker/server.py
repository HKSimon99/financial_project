from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Mojo Worker")

class Vector(BaseModel):
    data: List[float]

@app.post("/variance")
def variance(v: Vector):
    # TODO: replace with Mojo call
    import statistics
    return {"variance": statistics.pvariance(v.data)}

class OptIn(BaseModel):
    mu: List[float]
    cov: List[List[float]]
    method: str = "sharpe"
    risk_free: float = 0.0

@app.post("/optimize")
def optimize(body: OptIn):
    # TODO: call Mojo; placeholder uses numpy-like logic
    import numpy as np
    mu = np.array(body.mu)
    cov = np.array(body.cov)
    if body.method == "minvar":
        inv = np.linalg.pinv(cov); ones = np.ones_like(mu)
        w = inv @ ones; w = w / w.sum()
    else:
        inv = np.linalg.pinv(cov); ones = np.ones_like(mu)
        w = inv @ (mu - body.risk_free * ones); w = w / w.sum()
    return {"weights": w.tolist()}