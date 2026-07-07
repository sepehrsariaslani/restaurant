from fastapi import Depends, FastAPI

from .config import load_settings
from .drivers.registry import resolve_payment_driver
from .models import HealthResponse, ReversalRequest, SaleRequest, SaleResponse
from .security import verify_access

app = FastAPI(title="Restaurant Local Hardware Node", version="0.1.0")


@app.get("/v1/device/health", response_model=HealthResponse, dependencies=[Depends(verify_access)])
def health():
    settings = load_settings()
    driver = resolve_payment_driver(settings.payment_driver)
    return HealthResponse(
        ok=True,
        message="Local hardware node is running",
        payment_driver=settings.payment_driver,
        version=settings.version,
        devices=driver.health(),
    )


@app.post("/v1/payment/sale", response_model=SaleResponse, dependencies=[Depends(verify_access)])
def sale(payload: SaleRequest):
    settings = load_settings()
    driver = resolve_payment_driver(settings.payment_driver)
    return driver.sale(payload)


@app.post("/v1/payment/reversal", dependencies=[Depends(verify_access)])
def reversal(payload: ReversalRequest):
    settings = load_settings()
    driver = resolve_payment_driver(settings.payment_driver)
    return driver.reversal(payload)
