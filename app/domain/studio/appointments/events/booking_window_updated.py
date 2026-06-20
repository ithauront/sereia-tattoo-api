from datetime import date
from uuid import UUID


# TODO: fazer handle para esse evento mandar email para o user dizendo que foi atualizada a janela de agendamento.
# TODO: cadastrar esse evento e o handler dele no event bus e espelhar nos testes
# TODO: fazer teste para o handler e para o fluxo
class BookingWindowUpdated:
    def __init__(self, *, user_id: UUID, new_booking_window: date):
        self.user_id = user_id
        self.new_booking_window = new_booking_window
