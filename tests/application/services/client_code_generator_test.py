import re
import pytest
from app.application.studio.services.client_code_generator import ClientCodeGenerator
from app.core.exceptions.users import AllClientCodesTakenError
from app.domain.studio.users.constants.client_code_colors import VIP_CLIENT_CODE_COLORS
from app.domain.studio.users.entities.value_objects.client_code import ClientCode


def test_client_code_generation(read_uow):
    service = ClientCodeGenerator(read_uow)
    name = "  Jhon   "  # name not normalized
    code = service.generate(name)

    color_in_code = code.value.split("-")[1]

    assert code is not None
    assert isinstance(code, ClientCode)
    assert code.value.startswith("JHON-")
    assert code.value == code.value.upper()
    assert color_in_code in VIP_CLIENT_CODE_COLORS


def test_client_code_generate_number_if_colors_taken(read_uow, mocker):
    service = ClientCodeGenerator(read_uow)

    def fake_exists(code: str) -> bool:
        return len(code.split("-")) == 2

    mocker.patch.object(
        read_uow.vip_clients, "find_by_client_code", side_effect=fake_exists
    )

    code = service.generate("JHON")
    # regex para começa com o name depois uma string e depois dois digitos
    assert re.match(r"JHON-[A-Z]+-\d{2}", code.value)


def test_client_code_all_taken(read_uow, mocker):
    service = ClientCodeGenerator(read_uow)

    mocker.patch.object(read_uow.vip_clients, "find_by_client_code", return_value=True)

    with pytest.raises(AllClientCodesTakenError):
        service.generate("JHON")
