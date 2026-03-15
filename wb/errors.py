class HTTPStatusError(RuntimeError):
    def __init__(self, status: int, url: str, body: str = "") -> None:
        super().__init__(f"HTTP {status} for {url}")
        self.status = status
        self.url = url
        self.body = body
