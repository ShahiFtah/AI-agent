from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import OllamaChatModel
from agentscope.formatter import OllamaChatFormatter
from agentscope.memory import InMemoryMemory
import asyncio
import os
import requests


# ─────────────────────────────────────────────
# 🌐 WEB SEARCH via DuckDuckGo
# ─────────────────────────────────────────────
def search_web(query: str) -> str:
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": 1}
        res = requests.get(url, params=params, timeout=5).json()

        if res.get("AbstractText"):
            return res["AbstractText"]

        # Prøv relaterte emner hvis AbstractText er tom
        related = res.get("RelatedTopics", [])
        snippets = []
        for item in related[:3]:
            if isinstance(item, dict) and item.get("Text"):
                snippets.append(item["Text"])
        if snippets:
            return "\n".join(snippets)

        return "Ingen resultat funnet for: " + query
    except Exception as e:
        return f"Søkefeil: {e}"


# ─────────────────────────────────────────────
# 💻 KJØR PYTHON (med advarsel)
# ─────────────────────────────────────────────
def run_python(code: str) -> str:
    print("\n⚠️  ADVARSEL: Kjører AI-generert kode. Trykk Enter for å fortsette, Ctrl+C for å avbryte.")
    try:
        input()
    except KeyboardInterrupt:
        return "Avbrutt av bruker."

    try:
        local_vars = {}
        exec(code, {"__builtins__": {}}, local_vars)  # begrenset miljø
        return str(local_vars) if local_vars else "(ingen output)"
    except Exception as e:
        return f"Kjørefeil: {e}"


# ─────────────────────────────────────────────
# 💾 LAGRE FIL
# ─────────────────────────────────────────────
def save_file(filename: str, content: str) -> str:
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Fil lagret: {filename}"
    except Exception as e:
        return f"Lagreingsfeil: {e}"


# ─────────────────────────────────────────────
# 🔍 HJELPEFUNKSJONER
# ─────────────────────────────────────────────
def is_python_code(text: str) -> bool:
    indicators = ["def ", "import ", "for ", "while ", "print(", "class "]
    return sum(1 for k in indicators if k in text) >= 2  # minst 2 treff


def clean_markdown(text: str) -> str:
    """Fjern kun markdown-blokker, ikke innhold."""
    lines = text.split("\n")
    cleaned = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


# ─────────────────────────────────────────────
# 🤖 HOVEDPROGRAM
# ─────────────────────────────────────────────
async def main():
    print("🤖 AgentScope starter... (skriv 'exit' for å avslutte)\n")

    agent = ReActAgent(
        name="Assistent",
        sys_prompt="""Du er en hjelpsom AI-assistent som snakker norsk.

Du kan:
- Svare på spørsmål
- Skrive Python-kode
- Be om nettsøk ved å skrive: SEARCH: <spørsmål>

Regler:
- Svar alltid på norsk med mindre brukeren spør på engelsk
- Hvis du vil søke på nett, skriv kun: SEARCH: <spørsmålet ditt>
- Når du skriver kode, skriv kun ren Python uten forklaringer rundt koden
""",
        model=OllamaChatModel(
            model_name="llama3:latest",
        ),
        memory=InMemoryMemory(),
        formatter=OllamaChatFormatter(),
    )

    user = UserAgent(name="bruker")
    msg = None

    while True:
        # 👤 Bruker skriver
        msg = await user(msg)

        if msg and msg.get_text_content().strip().lower() == "exit":
            print("👋 Avslutter. Ha det!")
            break

        # 🤖 Agent svarer
        msg = await agent(msg)
        raw = msg.get_text_content()
        output = clean_markdown(raw)

        print(f"\n🤖 Assistent:\n{output}")
        print("\n" + "─" * 50)

        # 🌐 Nettsøk
        if output.strip().startswith("SEARCH:"):
            query = output.replace("SEARCH:", "").strip()
            print(f"\n🌐 Søker etter: {query}")
            result = search_web(query)
            print(f"📡 Søkeresultat: {result}\n")

            # Send resultat tilbake til agenten
            msg = await agent(f"Søkeresultat: {result}")
            final = clean_markdown(msg.get_text_content())
            print(f"🧠 Endelig svar:\n{final}")
            print("\n" + "─" * 50)

        # 💻 Python-kode funnet
        elif is_python_code(output):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop", "generated_code.py")
            print(f"\n{save_file(desktop, output)}")
            print("\n🔧 Vil du kjøre koden? (ja/nei)")
            valg = input("> ").strip().lower()
            if valg == "ja":
                result = run_python(output)
                print(f"📤 Resultat: {result}")
            print("\n" + "─" * 50)


asyncio.run(main())
