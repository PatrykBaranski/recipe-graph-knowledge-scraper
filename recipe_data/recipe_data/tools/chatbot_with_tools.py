from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage

from recipe_data.recipe_data.tools.common import llm
from recipe_data.recipe_data.tools.prompts import prompt
from recipe_data.recipe_data.tools.fridge_tools import read_fridge, add_ingredient_to_fridge, remove_ingredient_from_fridge
from recipe_data.recipe_data.tools.shopping_list_tools import add_ingredient_to_shopping_list, add_missing_ingredients_for_recipe, create_shopping_list_file_for_recipe
from recipe_data.recipe_data.tools.rag_tools import get_graph_rag_tool, get_vector_rag_tool

base_tools = [read_fridge, add_ingredient_to_fridge, remove_ingredient_from_fridge, add_ingredient_to_shopping_list, add_missing_ingredients_for_recipe, create_shopping_list_file_for_recipe]

class FridgeChatbot:
    def __init__(self, tools=None):
        self.tools = tools if tools else base_tools
        agent = create_tool_calling_agent(llm, self.tools, prompt=prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        self.chat_history = []

    def chat(self, message: str) -> str:
        result = self.agent_executor.invoke({
            "input": message,
            "chat_history": self.chat_history
        })
        self.chat_history.extend([HumanMessage(content=message), AIMessage(content=result["output"])])
        return result["output"]

    def update_tools(self, use_neo4j=False, rag_type="Graph RAG"):
        current_tools = base_tools.copy()
        if use_neo4j:
            if rag_type == "Graph RAG":
                tool = get_graph_rag_tool()
                if tool:
                    current_tools.append(tool)
            elif rag_type == "RAG":
                tool = get_vector_rag_tool()
                if tool:
                    current_tools.append(tool)
        
        print(f"Active tools: {[t.name for t in current_tools]}")
        self.tools = current_tools
        agent = create_tool_calling_agent(llm, self.tools, prompt=prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def clear_history(self):
        self.chat_history = []


if __name__ == "__main__":
    ## Przykładowe użycie
    fridge_chatbot = FridgeChatbot()
    response = fridge_chatbot.chat("Jakie składniki są w lodówce?")
    print(response)
