# Ollama Integration Instructions

## Prerequisites

- A Docker installation on your machine.
- Ensure Docker is running.
- A terminal or command-line interface accessible on your machine.

## Setup Steps

1. **Start the Ollama service**

   Run the following command in your terminal:

   ```bash
   ollama serve
   ```

2. **Pull a model**

   Download and prepare a language model for local use:

   ```bash
   ollama pull <model>
   ```

3. **Start the model**

   Run the following command in your terminal:

   ```bash
   ollama run qwen3.6:65k
   ```

## Increase Model Context Window

1. **Create a new model with increased context window**

   ```bash
   cat > Modelfile << 'EOF'
   FROM qwen3.6:latest
   PARAMETER num_ctx 65536
   EOF
   ```

2. **Create the new model**

   ```bash
   ollama create qwen3.6:65k -f Modelfile
   ```

3. **Show the new model**

   ```bash
   ollama show qwen3.6:65k --modelfile
   ```

## Notes

- Replace `<model>` with the exact repository name, such as `llama3` or `mistral`.
- Replace `qwen3.6:latest` and `qwen3.6:65k` with the actual model names you want to use.
- Keep the terminal open while the service is running to maintain connectivity.
