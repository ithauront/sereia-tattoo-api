# This email is only to notificate the client of an action done in the system
# It does not need any confirmation from the client
class SendActionMadeEmailRequested:
    def __init__(self, email: str):
        self.email = email
