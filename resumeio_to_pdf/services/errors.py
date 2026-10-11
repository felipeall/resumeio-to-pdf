class RenderError(Exception):
    """Raised when a resume cannot be rendered.

    Parameters
    ----------
    message : str
        Human readable reason, safe to show to the user.
    status_code : int, optional
        HTTP status the web UI answers with, by default 502.
    """

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code
