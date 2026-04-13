import random
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.core.exceptions.users import AllClientCodesTakenError
from app.domain.studio.users.constants.client_code_colors import VIP_CLIENT_CODE_COLORS
from app.domain.studio.value_objects.client_code import ClientCode


class ClientCodeGenerator:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def generate(self, name: str) -> ClientCode:
        name = name.strip().upper()

        colors_shuffled = VIP_CLIENT_CODE_COLORS.copy()
        random.shuffle(colors_shuffled)

        for color in colors_shuffled:
            candidate = f"{name}-{color}"

            if not self.uow.vip_clients.find_by_client_code(candidate):
                return ClientCode(candidate)

        for color in colors_shuffled:
            for i in range(1, 100):
                candidate = f"{name}-{color}-{i:02d}"
                if not self.uow.vip_clients.find_by_client_code(candidate):
                    return ClientCode(candidate)

        raise AllClientCodesTakenError("please_try_creating_client_code_with_last_name")
