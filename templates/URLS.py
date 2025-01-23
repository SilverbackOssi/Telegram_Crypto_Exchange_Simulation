
class Coingecko:
    API_BASE: str = "https://api.coingecko.com/api/v3"
    COIN_PRICE: str = f"{API_BASE}/simple/price"
    SUPPORTED_VS_CURRENCIES: str = f"{API_BASE}/simple/supported_vs_currencies"
