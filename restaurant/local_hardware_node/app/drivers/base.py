from abc import ABC, abstractmethod

from app.models import ReversalRequest, SaleRequest, SaleResponse


class BasePaymentDriver(ABC):
    @abstractmethod
    def sale(self, payload: SaleRequest) -> SaleResponse:
        raise NotImplementedError

    @abstractmethod
    def reversal(self, payload: ReversalRequest) -> dict:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict:
        raise NotImplementedError
