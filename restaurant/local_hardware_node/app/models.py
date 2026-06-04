from pydantic import BaseModel, Field


class SaleRequest(BaseModel):
    request_id: str = Field(min_length=4)
    order_id: str | None = None
    invoice_no: str | None = None
    terminal_id: str | None = None
    amount: int = Field(ge=0)
    currency: str = "IRR"
    timeout_ms: int = Field(default=8000, ge=1000, le=120000)
    provider: str | None = None


class SaleResponse(BaseModel):
    status: str
    rrn: str = ""
    trace_no: str = ""
    masked_pan: str = ""
    provider: str = ""
    raw_code: str = ""
    message: str = ""


class ReversalRequest(BaseModel):
    request_id: str
    rrn: str | None = None
    trace_no: str | None = None
    terminal_id: str | None = None


class HealthResponse(BaseModel):
    ok: bool
    message: str
    payment_driver: str
    version: str
    devices: dict
