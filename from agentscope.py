from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import OllamaChatModel
from agentscope.memory import InMemoryMemory
from agentscope.formatter import DeepSeekChatFormatter
import asyncio

async def main():
    agent = ReActAgent(
        name="Assistent",
        sys_prompt="Du er en hjelpsom assistent.",
        model=OllamaChatModel(
            model_name="llama3.2:latest",
        ),
        memory=InMemoryMemory(),
        formatter=DeepSeekChatFormatter(),  # ✅ dette funker hos deg
    )
    

    user = UserAgent(name="bruker")

    msg = None
    while True:
        msg = await agent(msg)
        msg = await user(msg)

        if msg and msg.get_text_content().lower() == "exit":
            break

asyncio.run(main())