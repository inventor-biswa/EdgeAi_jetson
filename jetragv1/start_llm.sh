#!/bin/bash
echo 'Starting Nemotron LLM Server in the background...'

# Stop any existing instance just in case
sudo docker stop llm-server >/dev/null 2>&1

sudo docker run -d --rm \
  --name llm-server \
  --runtime=nvidia \
  --network host \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin \
  llama-server \
  --hf-repo nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF \
  --hf-file NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf \
  --ctx-size 8196 \
  --alias my_model \
  --n-gpu-layers 999

echo 'Server is running! You can now use the RAG query scripts.'
