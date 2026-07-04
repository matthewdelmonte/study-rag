# Ollama + Local Model Setup in PyCharm (AI Assistant)

This guide explains how to connect PyCharm's AI Assistant to a local Ollama model and enable that model in the IDE.

## Prerequisites

- PyCharm installed
- Ollama installed
- Access to JetBrains AI Assistant
- A local model tag to pull, such as `qwen3:8b` or `qwen2.5-coder:7b`

## 1. Install and Run Ollama

- Install Ollama from the official website.
- Start the Ollama server: 
```bash
ollama serve
```

## 2. Pull the Model
```bash
ollama pull <model-tag>   # e.g. qwen3:8b  or  qwen2.5-coder:7b
```
Verify it registered:
```bash
ollama list
```

## 3. Install the JetBrains AI Assistant Plugin
- `Settings → Plugins` → install **AI Assistant**
- Local-model use requires a JetBrains AI subscription (covered by the free tier)

## 4. Connect Ollama as a Provider
- `Settings → Tools → AI Assistant → Providers & API keys`
- In **Third-party AI providers**, select **Ollama**
- Set the URL to `http://localhost:11434` → **Test Connection** → **Apply**

## 5. Enable the specific Model
- `Settings → Tools → AI Assistant → Models`
- Toggle your pulled model on so it appears in the AI Chat / model picker

---

## Troubleshooting: "Connected but No Model Showing"
A successful **Test Connection** only confirms PyCharm can reach the Ollama
server — it does not surface individual models.

1. Run `ollama list` to confirm the model is actually pulled and visible to the
   same Ollama instance PyCharm connects to.
   - **Empty / missing** → the pull didn't complete, or you pulled into a
     different Ollama install.
   - **Listed** → the model exists; the gap is IDE-side (Step 5).
2. In `Settings → Tools → AI Assistant → Models`, toggle the specific model on.
   Reopening this pane also forces a refresh of the model list.

## Known Caveats
- Local models **cannot** invoke tools from MCP servers.
- Default context window for local models is capped at **64,000 tokens**.
- **Agent plugins (Cline, Goose):** since the April 2026 updates, the standalone
  Ollama provider entry was removed from those agents. Route through an
  **OpenAI-compatible custom provider** pointed at `http://localhost:11434`
  instead. Ollama's own API is unchanged — this is a plugin-side change.

## Alternative: Calling Ollama from Python (no subscription needed)

Install the required package into your project interpreter:
```python
import ollama

response = ollama.chat(
    model="qwen2.5-coder:7b",
    messages=[{"role": "user", "content": "Refactor this loop..."}],
)
print(response["message"]["content"])
```
Install into the project interpreter: `pip install ollama`

Then call the model in your script: