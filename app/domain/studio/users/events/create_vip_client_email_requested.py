# This email is only to notificate the client that his account was created
# It does not need any confirmation from the client
class CreateVipClientEmailRequested:
    def __init__(self, email: str, client_code: str):
        self.email = email
        self.client_code = client_code
