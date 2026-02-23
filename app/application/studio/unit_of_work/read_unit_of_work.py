from app.application.studio.unit_of_work.base_unit_of_work import BaseUnitOfWork


class ReadUnitOfWork(BaseUnitOfWork):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass
