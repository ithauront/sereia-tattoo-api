from pydantic import ValidationError
import pytest
from app.application.studio.use_cases.DTO.change_email_dto import (
    ChangeVipClientEmailInput,
)
from app.application.studio.use_cases.users_use_cases.change_vip_client_email import (
    ChangeVipClientEmailUseCase,
)
from app.core.exceptions.users import EmailAlreadyTakenError, VipClientNotFoundError


def test_vip_client_change_email_success(vip_clients_repo, make_vip_client):
    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(vip_clients_repo)
    input_data = ChangeVipClientEmailInput(
        new_email="new@email.com", vip_client_id=vip_client.id
    )

    use_case.execute(input_data)

    saved = vip_clients_repo.find_by_id(vip_client.id)
    assert saved.email == "new@email.com"
    assert vip_clients_repo.find_by_email("jhon@doe.com") is None


def test_vip_client_change_to_same_email_should_pass(vip_clients_repo, make_vip_client):
    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(vip_clients_repo)
    input_data = ChangeVipClientEmailInput(
        new_email="jhon@doe.com", vip_client_id=vip_client.id
    )

    use_case.execute(input_data)

    saved = vip_clients_repo.find_by_id(vip_client.id)
    assert saved.email == "jhon@doe.com"


def test_email_is_normalized(vip_clients_repo, make_vip_client):
    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(vip_clients_repo)
    input_data = ChangeVipClientEmailInput(
        new_email="  New@Email.COM  ",
        vip_client_id=vip_client.id,
    )

    use_case.execute(input_data)

    saved = vip_clients_repo.find_by_id(vip_client.id)
    assert saved.email == "new@email.com"


def test_vip_client_not_exists_change_email(vip_clients_repo, make_vip_client):
    vip_client = make_vip_client(email="jhon@doe.com")
    # vip_client not created in repo

    use_case = ChangeVipClientEmailUseCase(vip_clients_repo)
    input_data = ChangeVipClientEmailInput(
        new_email="jhon@doe.com", vip_client_id=vip_client.id
    )

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(input_data)


def test_vip_client_email_already_in_use(vip_clients_repo, make_vip_client):
    vip_client_1 = make_vip_client(email="jhon@doe.com")
    vip_client_2 = make_vip_client(email="jane@doe.com")
    vip_clients_repo.create(vip_client_1)
    vip_clients_repo.create(vip_client_2)

    use_case = ChangeVipClientEmailUseCase(vip_clients_repo)
    input_data = ChangeVipClientEmailInput(
        new_email="jane@doe.com", vip_client_id=vip_client_1.id
    )
    with pytest.raises(EmailAlreadyTakenError):
        use_case.execute(input_data)

    saved = vip_clients_repo.find_by_id(vip_client_1.id)
    assert saved.email == "jhon@doe.com"


def test_change_email_email_not_valid(make_vip_client):
    # dto test
    vip_client = make_vip_client(email="jhon@doe.com")
    with pytest.raises(ValidationError):
        ChangeVipClientEmailInput(
            new_email="wrong_email_format", vip_client_id=vip_client.id
        )
