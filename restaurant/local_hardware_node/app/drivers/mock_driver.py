import random

from app.models import ReversalRequest, SaleRequest, SaleResponse

from .base import BasePaymentDriver


class MockPaymentDriver(BasePaymentDriver):
    def sale(self, payload: SaleRequest) -> SaleResponse:
        rrn = f"{random.randint(100000000000, 999999999999)}"
        trace_no = f"{random.randint(100000, 999999)}"
        return SaleResponse(
            status="approved",
            rrn=rrn,
            trace_no=trace_no,
            masked_pan="6037********1234",
            provider="mock",
            raw_code="00",
            message="Approved by mock driver",
        )

    def reversal(self, payload: ReversalRequest) -> dict:
        return {
            "status": "reversed",
            "message": "Reversal accepted by mock driver",
            "rrn": payload.rrn or "",
            "trace_no": payload.trace_no or "",
        }

    def health(self) -> dict:
        return {
            "card_pos": "connected",
            "scale": "unknown",
        }
