class FakeActivationTokenService:
    def create(self, user_id: str, version: int) -> str:
        return f"fake-token-{user_id}-{version}"
