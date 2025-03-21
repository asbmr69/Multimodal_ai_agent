import logging
import asyncio
from typing import Dict, List, Callable, Any, Coroutine, Union

class EventManager:
    """Manages application-wide events and provides publish-subscribe functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.logger.info("Event Manager initialized")
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: Function or coroutine to call when event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        self.logger.debug(f"Handler subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            self.logger.debug(f"Handler unsubscribed from event: {event_type}")
    
    async def emit(self, event_type: str, data: Any = None) -> None:
        """
        Emit an event to all subscribed handlers.
        
        Args:
            event_type: The type of event to emit
            data: Data to pass to event handlers
        """
        if event_type not in self.event_handlers:
            return
        
        self.logger.debug(f"Emitting event: {event_type}")
        for handler in self.event_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {str(e)}")
    
    def emit_sync(self, event_type: str, data: Any = None) -> None:
        """
        Synchronously emit an event. Use for UI thread safety.
        
        Args:
            event_type: The type of event to emit
            data: Data to pass to event handlers
        """
        if event_type not in self.event_handlers:
            return
        
        self.logger.debug(f"Emitting sync event: {event_type}")
        for handler in self.event_handlers[event_type]:
            try:
                if not asyncio.iscoroutinefunction(handler):
                    handler(event_type, data)
                else:
                    self.logger.warning(f"Async handler called synchronously for {event_type}")
                    # Create a future and schedule it on the event loop
                    asyncio.create_task(handler(event_type, data))
            except Exception as e:
                self.logger.error(f"Error in sync event handler for {event_type}: {str(e)}")
