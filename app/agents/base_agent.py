from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base interface that all agents must implement."""
    
    @property
    @abstractmethod
    def agent_type(self):
        """Return the type identifier for this agent."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self):
        """Return a list of capabilities provided by this agent."""
        pass
    
    @property
    def auto_terminate(self):
        """Whether the agent should terminate after processing."""
        return False
    
    @abstractmethod
    async def initialize(self):
        """Initialize the agent and prepare resources."""
        pass
    
    @abstractmethod
    async def process(self, context):
        """Process the input and generate a response."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up resources used by the agent."""
        pass
    
    @abstractmethod
    def get_ui_components(self):
        """Get UI components for this agent."""
        pass
    
    @abstractmethod
    async def handle_ui_event(self, event_type, payload):
        """Handle UI events specific to this agent."""
        pass