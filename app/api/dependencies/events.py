from fastapi import Request


def get_event_bus(request: Request):
    return request.app.state.event_bus
