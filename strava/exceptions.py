class StravaError(Exception):
    pass


class StravaNotAuthenticatedError(StravaError):
    pass


class StravaPaidFeatureError(StravaError):
    pass


class StravaNotFoundError(StravaError):
    def __init__(self, url: str):
        super().__init__(f"Resource not found at URL: {url}")
        self.url = url


class StravaWebhookError(StravaError):
    def __init__(self, message: str):
        super().__init__(f"Webhook error: {message}")
        self.message = message
