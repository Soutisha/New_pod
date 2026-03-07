"""
Simple LLM wrapper using LangChain with Ollama
For fast, reliable local LLM execution
"""
from langchain_ollama import ChatOllama

# Initialize the LLM
llm = ChatOllama(
    model="llama3.2:1b",
    temperature=0.3,
    verbose=False
)

def generate(prompt):
    """Generate response from LLM"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"

# Test
if __name__ == "__main__":
    print("Testing Ollama...")
    result = generate("Hello, how are you?")
    print("Result:", result)

