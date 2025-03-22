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
        
        # Initialize conversation history
        self.conversation_history = []
        
        # System prompt for the LLM
        self.system_prompt = (
            "You are an AI assistant that helps users with various tasks. "
            "You can provide direct answers to questions, or invoke specialized agents for more complex tasks. "
            "The available agents are:\n"
            "1. 'coder' - For coding, programming, and software development tasks\n"
            "2. 'computer' - For file operations, terminal commands, and system tasks\n"
            "3. 'assistant' - For general information retrieval and explanations\n"
            "Analyze the user's request and determine if you should handle it directly "
            "or invoke one of these specialized agents."
        )
        
        self.logger.info("Application Controller initialized")
    
    def _register_default_agents(self):
        """Register the default set of agents."""
        from app.agents.coder_agent.coder_agent import CoderAgent
        from app.agents.computer_agent.computer_agent import ComputerAgent
        from app.agents.assistant_agent.assistant_agent import AssistantAgent
        
        self.agent_manager.register_agent("coder", CoderAgent)
        self.agent_manager.register_agent("computer", ComputerAgent)
        self.agent_manager.register_agent("assistant", AssistantAgent)
    
    async def process_user_input(self, user_input):
        """Process user input and determine appropriate action."""
        self.logger.info(f"Processing user input: {user_input[:50]}...")
        
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Prepare messages for LLM including system prompt and conversation history
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add the last N messages from conversation history to avoid token limits
        max_history = 10  # Adjust based on your token limits
        messages.extend(self.conversation_history[-max_history:])
        
        # Get a response from the LLM
        try:
            # Get response from LLM
            llm_response = await self.llm_controller.chat_completion(messages)
            response_content = llm_response["content"]
            
            # Add assistant response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response_content})
            
            # Check if we need to invoke an agent
            agent_info = await self.llm_controller.extract_agent_action(response_content)
            
            if agent_info["agent_type"] != "assistant":
                # Invoke a specialized agent
                agent_type = agent_info["agent_type"]
                agent_context = {
                    "action": agent_info.get("action", "process_request"),
                    "content": agent_info.get("content", user_input),
                    "user_input": user_input
                }
                
                agent_response = await self.agent_manager.invoke_agent(agent_type, agent_context)
                
                return {
                    "type": "agent_response",
                    "agent_type": agent_type,
                    "content": response_content,  # LLM's explanation
                    "agent_result": agent_response  # Result from the agent
                }
            else:
                # Direct response from LLM
                return {
                    "type": "direct_response",
                    "content": response_content
                }
                
        except Exception as e:
            self.logger.error(f"Error processing input: {str(e)}")
            return {
                "type": "error",
                "content": f"I encountered an error processing your request: {str(e)}"
            }
    
    async def terminate_agent(self, agent_type):
        """Terminate a running agent."""
        return await self.agent_manager.terminate_agent(agent_type)
        
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []
        
    async def get_agent_status(self, agent_type=None):
        """Get status of all agents or a specific agent."""
        if agent_type:
            return await self.agent_manager.get_agent_status(agent_type)
        else:
            statuses = {}
            for agent_type in ["coder", "computer", "assistant"]:
                statuses[agent_type] = await self.agent_manager.get_agent_status(agent_type)
            return statuses