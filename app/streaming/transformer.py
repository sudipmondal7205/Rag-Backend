from app.streaming.registry import EVENT_HANDLERS


def transform_events(event):

    handler = EVENT_HANDLERS.get(event['event'])

    if handler:
        return handler(event)
    
    return None