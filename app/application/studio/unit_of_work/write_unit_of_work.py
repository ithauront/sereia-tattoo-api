from abc import abstractmethod
from app.application.studio.unit_of_work.base_unit_of_work import BaseUnitOfWork


class WriteUnitOfWork(BaseUnitOfWork):

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def __enter__(self) -> "WriteUnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb): ...
