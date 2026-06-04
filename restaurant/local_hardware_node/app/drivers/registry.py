from .mock_driver import MockPaymentDriver


def resolve_payment_driver(driver_name: str):
    normalized = (driver_name or "mock").strip().lower()
    if normalized == "mock":
        return MockPaymentDriver()

    # Placeholder for future drivers (Behpardakht, Saman, etc.)
    return MockPaymentDriver()
