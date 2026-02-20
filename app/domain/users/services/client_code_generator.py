import random
from app.core.exceptions.users import AllClientCodesTakenError
from app.domain.users.constants.client_code_colors import VIP_CLIENT_CODE_COLORS
from app.domain.users.entities.value_objects.client_code import ClientCode
from app.domain.users.repositories.vip_clients_repository import VipClientsRepository


class ClientCodeGenerator:
    def __init__(self, repo: VipClientsRepository):
        self.repo = repo

    def generate(self, first_name: str) -> ClientCode:
        first_name = first_name.strip().upper()

        colors_shuffled = VIP_CLIENT_CODE_COLORS.copy()
        random.shuffle(colors_shuffled)

        for color in colors_shuffled:
            candidate = f"{first_name}-{color}"

            if not self.repo.find_by_client_code(candidate):
                return ClientCode(candidate)

        for color in colors_shuffled:
            for i in range(1, 100):
                candidate = f"{first_name}-{color}-{i:02d}"
                if not self.repo.find_by_client_code(candidate):
                    return ClientCode(candidate)

        raise AllClientCodesTakenError("please_try_creating_client_code_with_last_name")
