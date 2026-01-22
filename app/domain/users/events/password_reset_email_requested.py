from uuid import UUID


class PasswordResetEmailRequested:
    def __init__(self, user_id: UUID, email: str, password_token_version: int):
        self.user_id = user_id
        self.email = email
        self.password_token_version = password_token_version
