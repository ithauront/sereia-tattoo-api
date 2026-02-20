from app.core.exceptions.users import AllClientCodesTakenError
from app.domain.users.entities.value_objects.client_code import ClientCode
from app.domain.users.services.client_code_generator import ClientCodeGenerator


class GenerateVipClientCodeUseCase:
    MAX_CODES = 3
    MAX_ATTEMPTS = 20

    def __init__(self, generator: ClientCodeGenerator):
        self.generator = generator

    def execute(self, name: str) -> list[ClientCode]:
        codes: list[ClientCode] = []
        attempts = 0

        while len(codes) < self.MAX_CODES and attempts < self.MAX_ATTEMPTS:
            attempts += 1
            try:
                code = self.generator.generate(name)
            except AllClientCodesTakenError:
                break

            existing = {str(code) for code in codes}
            if str(code) not in existing:
                codes.append(code)

        if not codes:
            raise AllClientCodesTakenError(
                "please_try_creating_client_code_with_last_name"
            )

        return codes
