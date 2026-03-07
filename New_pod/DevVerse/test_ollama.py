#!/usr/bin/env python
"""Quick test script"""
print("Starting test...")

try:
    from langchain_ollama import ChatOllama
    print("Imported ChatOllama")
    
    llm = ChatOllama(model="llama3.2:1b", temperature=0.3)
    print("Created LLM")
    
    response = llm.invoke("Hello")
    print("Got response:", response.content[:100])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

