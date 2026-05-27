from fastapi import Request


def get_transactional_event_bus(request: Request):
    return request.app.state.transactional_bus


def get_integration_event_bus(request: Request):
    return request.app.state.integration_bus
