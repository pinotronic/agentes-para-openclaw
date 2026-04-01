#!/usr/bin/env python3
"""
Pipeline Red Team / Blue Team para revisión de código

Flujo:
  CODE_CRITIC (Red) → Analiza código, encuentra problemas
        ↓
  DEFENDER (Blue) → Propone soluciones a los problemas
        ↓
  IMPLEMENTER → Aplica las soluciones
        ↓
  DIAGNOSER → Verifica si los tests pasan

Uso:
  python run_redblue.py --code "print('hello')" --plan "..."

Argumentos:
  --code: Código a revisar (o path a archivo)
  --plan: Plan/deliverable del PLANNER
  --agent: qwen3.5:9b (modelo a usar)
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner.ollama_agent import OllamaAgent


def run_red_team(code: str, plan: str) -> str:
    """Ejecuta CODE_CRITIC (Red Team)"""
    print("[RED] Iniciando CODE_CRITIC...")
    
    prompt = f"""Eres CODE_CRITIC, un hacker ético que revisa código.

## PLAN DEL PROYECTO:
{plan}

## CÓDIGO A REVISAR:
```{code}
```

## TAREA:
Revisa este código buscando:
1. Problemas de SEGURIDAD (inyección, auth, validación)
2. EDGE CASES (null, vacío, valores extremos)
3. Problemas de LÓGICA (condiciones, off-by-one)
4. Problemas de PERFORMANCE (N+1, memory leaks)
5. Problemas de ARQUITECTURA (acoplamiento, God classes)

Sigue el formato de salida obligatorio."""

    agent = OllamaAgent('code_critic')
    result = agent.run(prompt)
    print(f"[RED] CODE_CRITIC completó. {len(result)} caracteres")
    return result


def run_blue_team(critic_output: str, code: str, plan: str) -> str:
    """Ejecuta DEFENDER (Blue Team)"""
    print("[BLUE] Iniciando DEFENDER...")
    
    prompt = f"""Eres DEFENDER, un ingeniero defensivo que propone soluciones a problemas de código.

## PLAN DEL PROYECTO:
{plan}

## CÓDIGO ORIGINAL:
```{code}
```

## CRÍTICAS DEL CODE_CRITIC:
{critic_output}

## TAREA:
Para cada crítica del CODE_CRITIC, propón:
1. Solución exacta (código o pseudocódigo)
2. Archivo a modificar
3. Tests a agregar
4. Verificación

Sigue el formato de salida obligatorio."""

    agent = OllamaAgent('defender')
    result = agent.run(prompt)
    print(f"[BLUE] DEFENDER completó. {len(result)} caracteres")
    return result


def main():
    parser = argparse.ArgumentParser(description='Red Team / Blue Team pipeline')
    parser.add_argument('--code', required=True, help='Código a revisar')
    parser.add_argument('--plan', required=True, help='Plan del PLANNER')
    parser.add_argument('--output', help='Archivo de salida (opcional)')
    parser.add_argument('--skip-blue', action='store_true', help='Solo ejecutar Red Team')
    args = parser.parse_args()

    # Run Red Team
    red_output = run_red_team(args.code, args.plan)
    
    if args.skip_blue:
        output = red_output
    else:
        # Run Blue Team
        blue_output = run_blue_team(red_output, args.code, args.plan)
        output = f"# REVISIÓN RED TEAM / BLUE TEAM\n\n## RED TEAM (CODE_CRITIC)\n{red_output}\n\n---\n\n## BLUE TEAM (DEFENDER)\n{blue_output}"

    # Save or print
    if args.output:
        Path(args.output).write_text(output)
        print(f"Resultado guardado en: {args.output}")
    else:
        print("\n" + "="*60)
        print(output)
        print("="*60)

    # Summary
    print("\n📊 RESUMEN:")
    print("  Red Team: ✓ Completado")
    if not args.skip_blue:
        print("  Blue Team: ✓ Completado")
    print("  Listo para IMPLEMENTER")


if __name__ == '__main__':
    main()
