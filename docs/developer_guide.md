How They Work Together
1).Initialization Flow:
    main.py creates the AppController

    AppController initializes the EventManager

    AppController passes the EventManager to the LLMController and AgentManager

    Components register event handlers with the EventManager

2).Message Processing Flow:

    User sends message through UI

    Message goes to AppController

    AppController forwards to LLMController

    LLMController sends to appropriate LLM provider

    Response is analyzed to determine which agent should handle it

    AgentManager activates the appropriate agent

    Agent processes the request and returns results

    UI is updated via events through the EventManager

3).Event Flow Example:

    When an LLM request starts:
    LLMController emits "llm_request_start" event
    UI components that subscribed to this event update to show loading state

    When the request completes:
    LLMController emits "llm_request_complete" event
    UI components update to show the response