from enum import Enum
from typing import Any

from pydantic import BaseModel


class StreamEvent(Enum):
    STREAM_BEGIN = "stream_begin"
    NODE_PROCESSING = "node_processing"
    NODE_RENDER = "node_render"
    STREAM_END = "stream_end"


class SSE(BaseModel):
    """
    :param str data: The data field for the message.
    :param str id: The event ID to set the EventSource object's last
        event ID value to.
    :param str event: The event's type. If this is specified, an event will
        be dispatched on the browser to the listener for the specified
        event name; the web site would use addEventListener() to listen
        for named events. The default event type is "message".
    :param int retry: The reconnection time. If the connection to the server is
        lost, the browser will wait for the specified time before attempting to
        reconnect. This must be an integer, specifying the reconnection time in
        milliseconds. If a non-integer value is specified, the field is ignored.
    """
    data: Any
    id: str
    event: StreamEvent
    retry: int = 15000  # ms
