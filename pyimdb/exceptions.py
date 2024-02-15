class TitleNotFoundException(Exception):
    """Raised when a title is not found in the IMDb database."""
    def __init__(self, title: str) -> None:
        self.title = title
        self.message = f"Title not found: '{title}'"
        super().__init__(self.message)

class GraphQLException(Exception):
    """Raised when an error occurs while querying the IMDb GraphQL API."""
    def __init__(self, message: str) -> None:
        self.message = f"GraphQL Error: {message}"
        super().__init__(self.message)
