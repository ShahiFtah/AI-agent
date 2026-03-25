from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import OllamaChatModel
from agentscope.memory import InMemoryMemory
from agentscope.formatter import DeepSeekChatFormatter
import asyncio
import os
import requests
from bs4 import BeautifulSoup

# 🧼 CLEAN AI OUTPUT
def clean_code(text):
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()

        # fjern vanlig chat
        if any(word in line.lower() for word in [
            "here is", "what would", "i'm", "let me", "sure"
        ]):
            continue

        # fjern markdown
        if "```" in line:
            continue

        if line:
            cleaned.append(line)

    return "\n".join(cleaned)

def should_force_search(text):
    keywords = ["nyeste", "latest", "2025", "2026", "nå", "current"]
    return any(k in text.lower() for k in keywords)

# 🧠 sjekk om det er kode
def is_python_code(text):
    keywords = ["print", "=", "for ", "while ", "import ", "def "]
    return any(k in text for k in keywords)

# 🌐 sjekk om info
def is_info_request(text):
    keywords = ["hva er", "what is", "who is", "forklar", "pris", "weather"]
    return any(k in text.lower() for k in keywords)

# 🌐 WEB SEARCH

def search_web(query):
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        res = requests.get(url)

        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.find_all("a", class_="result__a", limit=3)

        output = []
        for r in results:
            output.append(r.get_text())

        return "\n".join(output) if output else "Ingen resultat"

    except Exception as e:
        return f"Error: {e}"

# 💻 KJØR PYTHON
def run_python(code: str):
    try:
        local_vars = {}
        exec(code, {}, local_vars)
        return str(local_vars)
    except Exception as e:
        return f"Error: {e}"

# 💾 LAGRE FIL
def save_file(filename: str, content: str):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Fil lagret som {filename}"
    except Exception as e:
        return f"Error: {e}"

async def main():
    agent = ReActAgent(
        name="Assistent",
        sys_prompt="""DU ER EN SMART AI AGENT.

DU KAN:
- svare på spørsmål
- skrive Python kode
- søke på internett

REGLER:
- Hvis du ikke vet svaret → skriv:
SEARCH: <spørsmål>

- Hvis kode → skriv KUN Python kode
- IKKE bruk markdown ```
- IKKE forklar i kode
""",
        model=OllamaChatModel(
            model_name="llama3:latest",
        ),
        memory=InMemoryMemory(),
        formatter=DeepSeekChatFormatter(),
    )

    user = UserAgent(name="bruker")
    msg = None

    while True:
        # 👤 bruker først
        msg = await user(msg)

        if msg and msg.get_text_content().lower() == "exit":
            break

        # 🤖 agent svarer
        msg = await agent(msg)

        raw_output = msg.get_text_content()
        agent_output = clean_code(raw_output)

        #print("\n🤖 AI:\n")
        #print(agent_output)

        # 🌐 hvis AI vil søke selv
        if agent_output.startswith("SEARCH:"):
            query = agent_output.replace("SEARCH:", "").strip()

            print("\n🌐 Søker på nett...\n")
            result = search_web(query)

            print("📡 Result:", result)

            # send resultat tilbake til AI
            msg = await agent({
                "role": "user",
                "content": result
            })

            final_output = clean_code(msg.get_text_content())

            print("\n🧠 Endelig svar:\n")
            print(final_output)

        # 💻 hvis kode
        elif is_python_code(agent_output):
            filename = os.path.join(os.path.expanduser("~"), "Desktop", "generated_code.py")

            print("\n💾 Lagrer fil...")
            print(save_file(filename, agent_output))

            print("\n🔧 Kjører kode...\n")
            result = run_python(agent_output)
            print("📤 Result:", result)

        else:
            print("\n⚠️ Vanlig svar")

        print("\n" + "-"*50 + "\n")
asyncio.run(main())