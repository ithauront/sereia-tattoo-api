from uuid import UUID


class UserCreationRequested:
    def __init__(self, user_id: UUID, email: str, activation_token_version: int):
        self.user_id = user_id
        self.email = email
        self.activation_token_version = activation_token_version
