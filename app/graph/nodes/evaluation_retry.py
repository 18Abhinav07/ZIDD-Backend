"""No-credit route used when a prep answer could not be evaluated reliably."""


async def evaluation_retry_node(_state: dict) -> dict:
    return {
        "pending": None,
        "pending_game": None,
        "last_route": "evaluation_retry",
    }
