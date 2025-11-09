from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool, initialize_agent
from langchain.agents import AgentType
from langchain.tools import BaseTool

# Example tool: Calculator
class CalculatorTool(BaseTool):
    name = "Calculator"
    description = "Useful for when you need to do math calculations."
    def _run(self, query: str):
        try:
            return str(eval(query, {"__builtins__": {}}))
        except Exception:
            return "Error in calculation."

llm = OpenAI(temperature=0.2)
memory = ConversationBufferMemory()
tools = [CalculatorTool()]
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

def run_agent_conversation(user_message: str, context: dict = None) -> str:
    # Enrich context for agent
    context_str = f"Context: {context}" if context else ""
    prompt = f"{context_str}\n{user_message}" if context else user_message
    response = agent.run(prompt)
    return response
