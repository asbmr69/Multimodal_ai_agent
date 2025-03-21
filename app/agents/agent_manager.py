import logging
import asyncio

class AgentManager:
    """Manages the registration, instantiation, and lifecycle of agents."""
    
    def __init__(self, event_manager):
        self.logger = logging.getLogger(__name__)
        self.event_manager = event_manager
        
        # Store registered agent classes
        self.agent_classes = {}
        
        # Store active agent instances
        self.active_agents = {}
    
    def register_agent(self, agent_type, agent_class):
        """Register a new agent type."""
        if agent_type in self.agent_classes:
            self.logger.warning(f"Agent type '{agent_type}' already registered. Overwriting.")
        
        self.agent_classes[agent_type] = agent_class
        self.logger.info(f"Registered agent type: {agent_type}")
    
    async def invoke_agent(self, agent_type, context):
        """Invoke an agent to process the given context."""
        if agent_type not in self.agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Get or create agent instance
        agent = self._get_or_create_agent(agent_type)
        
        # Process the input
        self.logger.info(f"Invoking agent: {agent_type}")
        response = await agent.process(context)
        
        # Check if agent should be terminated
        if agent.auto_terminate:
            await self.terminate_agent(agent_type)
        
        return response
    
    def _get_or_create_agent(self, agent_type):
        """Get an existing agent instance or create a new one."""
        if agent_type in self.active_agents:
            return self.active_agents[agent_type]
        
        # Create new agent instance
        agent_class = self.agent_classes[agent_type]
        agent = agent_class(self.event_manager)
        
        # Initialize the agent
        asyncio.create_task(agent.initialize())
        
        # Store the agent
        self.active_agents[agent_type] = agent
        
        return agent
    
    async def terminate_agent(self, agent_type):
        """Terminate an active agent."""
        if agent_type not in self.active_agents:
            self.logger.warning(f"No active agent of type '{agent_type}' to terminate.")
            return False
        
        agent = self.active_agents[agent_type]
        
        # Cleanup the agent
        await agent.cleanup()
        
        # Remove from active agents
        del self.active_agents[agent_type]
        
        self.logger.info(f"Terminated agent: {agent_type}")
        return True
    
    def get_active_agents(self):
        """Get a list of all active agents."""
        return list(self.active_agents.keys())
    
    def get_registered_agents(self):
        """Get a list of all registered agent types."""
        return list(self.agent_classes.keys())