# VRAM / Modelo único (política)

Objetivo: evitar saturación de VRAM (RTX 5090 32GB) y congelamientos.

## Reglas
1) **Un modelo a la vez** (serial). No correr agentes en paralelo.
2) Preferir modelos ligeros; escalar a modelos pesados solo si es necesario.
3) **Después de un modelo pesado** (qwen3-coder:30b, deepseek-r1:32b, llama3.3), liberar VRAM.

## Liberación de VRAM (práctica)
Opción A (preferida, simple): reiniciar servicio Ollama.

```bash
sudo systemctl restart ollama
```

Opción B: verificar estado

```bash
ollama ps
nvidia-smi
```

## Cuándo reiniciar
- Tras cada ejecución de `qwen3-coder:30b`.
- Tras cada ejecución de `deepseek-r1:32b`.
- Tras indexado de embeddings.
- Si el sistema se pone lento o `nvidia-smi` muestra VRAM alta sostenida.
