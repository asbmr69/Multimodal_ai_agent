import logging
from controller.llm_controller import LLMController
from controller.event_manager import EventManager
from agents.agent_manager import AgentManager

class AppController:
    """Main application controller that orchestrates all components."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Application Controller")
        
        # Create event manager for application-wide events
        self.event_manager = EventManager()
        
        # Initialize LLM controller
        self.llm_controller = LLMController(self.event_manager)
        
        # Initialize agent manager
        self.agent_manager = AgentManager(self.event_manager)
        
        # Register default agents
        self._register_default_agents()
        
        self.logger.info("Application Controller initialized")
    
    def _register_default_agents(self):
        """Register the default set of agents."""
        from agents.coder_agent.coder_agent import CoderAgent
        from agents.computer_agent.computer_agent import ComputerAgent
        from agents.assistant_agent.assistant_agent import AssistantAgent
        
        self.agent_manager.register_agent("coder", CoderAgent)
        self.agent_manager.register_agent("computer", ComputerAgent)
        self.agent_manager.register_agent("assistant", AssistantAgent)
    
    async def process_user_input(self, user_input):
        """Process user input and determine appropriate action."""
        self.logger.info(f"Processing user input: {user_input[:50]}...")
        
        # Use LLM to determine intent and which agent to invoke
        analysis = self.llm_controller.analyze_input(user_input)
        
        if analysis["needs_agent"]:
            # Invoke the appropriate agent
            agent_type = analysis["agent_type"]
            response = self.agent_manager.invoke_agent(
                agent_type, 
                {
                    "prompt": user_input,
                    "context": analysis["context"]
                }
            )
            
            return {
                "type": "agent_response",
                "agent_type": agent_type,
                "content": response,
                "follow_up_questions": analysis.get("follow_up_questions", [])
            }
        else:
            # Direct LLM response for simple queries
            response = self.llm_controller.generate_response(user_input)
            return {
                "type": "direct_response",
                "content": response
            }
    
    def terminate_agent(self, agent_type):
        """Terminate a running agent."""
        return self.agent_manager.terminate_agent(agent_type)