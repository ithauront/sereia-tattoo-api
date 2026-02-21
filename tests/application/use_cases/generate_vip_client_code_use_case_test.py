import pytest
from app.application.studio.services.client_code_generator import ClientCodeGenerator
from app.application.studio.use_cases.users_use_cases.generate_vip_client_code import (
    GenerateVipClientCodeUseCase,
)
from app.core.exceptions.users import AllClientCodesTakenError
from app.domain.studio.users.constants.client_code_colors import VIP_CLIENT_CODE_COLORS
from app.domain.studio.users.entities.value_objects.client_code import ClientCode


def test_generate_vip_client_code(vip_clients_repo):
    generator = ClientCodeGenerator(vip_clients_repo)
    use_case = GenerateVipClientCodeUseCase(generator=generator)

    name_input = "jhon"

    result = use_case.execute(name_input)

    colors_allowed = {color for color in VIP_CLIENT_CODE_COLORS}

    colors_in_result = [code.value.split("-")[1] for code in result]

    assert isinstance(result, list)
    assert len(result) == use_case.MAX_CODES  # repo empty needs to give MAX_CODES lenth

    assert all(isinstance(code, ClientCode) for code in result)

    assert all("JHON" in code.value for code in result)

    assert all(color in colors_allowed for color in colors_in_result)


def test_use_case_raises_when_generator_full(mocker):
    generator = mocker.Mock()
    generator.generate.side_effect = AllClientCodesTakenError(
        "please_try_creating_client_code_with_last_name"
    )

    use_case = GenerateVipClientCodeUseCase(generator=generator)

    with pytest.raises(AllClientCodesTakenError):
        use_case.execute("jhon")


def test_use_case_deduplicates_partial_duplicates(mocker):
    generator = mocker.Mock()
    generator.generate.side_effect = [
        ClientCode("JHON-RED-01"),
        ClientCode("JHON-BLUE-01"),
        ClientCode("JHON-BLUE-01"),  # duplicado
        ClientCode("JHON-GREEN-01"),
    ]

    use_case = GenerateVipClientCodeUseCase(generator=generator)

    result = use_case.execute("JHON")

    assert len(result) == 3
    values = [code.value for code in result]
    assert len(set(values)) == 3


def test_use_case_stops_after_max_attempts(mocker):
    generator = mocker.Mock()
    generator.generate.return_value = ClientCode("JHON-RED-01")

    use_case = GenerateVipClientCodeUseCase(generator)

    use_case.execute("JHON")

    assert generator.generate.call_count == use_case.MAX_ATTEMPTS


def test_use_case_raises_when_no_codes_generated(mocker):
    generator = mocker.Mock()
    generator.generate.side_effect = AllClientCodesTakenError("x")

    use_case = GenerateVipClientCodeUseCase(generator)

    with pytest.raises(AllClientCodesTakenError):
        use_case.execute("JHON")


def test_use_case_limits_number_of_codes(mocker):
    generator = mocker.Mock()

    generator.generate.side_effect = [
        ClientCode("JHON-A"),
        ClientCode("JHON-B"),
        ClientCode("JHON-C"),
        ClientCode("JHON-D"),
    ]

    use_case = GenerateVipClientCodeUseCase(generator=generator)

    result = use_case.execute("JHON")

    assert len(result) == 3
    values = [code.value for code in result]
    assert len(set(values)) == 3
