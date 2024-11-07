from crewai import Agent, LLM
from typing import ClassVar, Optional, List
from crewai_tools import BaseTool
 

class OllamaAgent(Agent):
    #   NAME             SIZE  
    #   llama3.2:3b      2.0 GB  
    #   llama3.2:1b      1.3 GB  
    #   gemma2:latest    5.4 GB  
    #   llama3:latest    4.7 GB 
    default_llm: ClassVar[LLM] = LLM(
        model="llama3.2:3b",
        base_url="http://localhost:11434",
        temperature=0.7,
        timeout=60
    )

    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str = "Default backstory for this agent.",
        tools: Optional[List[BaseTool]] = None,
        max_iter: int = 25,
        verbose: bool = False,
        allow_delegation: bool = False,
        **kwargs
    ):
        if 'llm' not in kwargs:
            kwargs['llm'] = self.default_llm
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools or [],
            max_iter=max_iter,
            verbose=verbose,
            allow_delegation=allow_delegation,
            **kwargs
        )