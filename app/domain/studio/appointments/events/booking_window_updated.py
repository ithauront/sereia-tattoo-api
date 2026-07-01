from datetime import date
from uuid import UUID


class BookingWindowUpdated:
    def __init__(self, *, user_id: UUID, new_booking_window: date):
        self.user_id = user_id
        self.new_booking_window = new_booking_window
