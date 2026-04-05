#!/usr/bin/env python3
"""
Pipeline Red Team / Blue Team para revisión de código

Flujo:
  CODE_CRITIC (Red) → Analiza código, encuentra problemas
        ↓
  DEFENDER (Blue) → Propone soluciones a los problemas

Uso:
  python run_redblue.py --code "print('hello')" --plan "..."
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner.ollama_agent import build_prompt, load_profile, run_with_tool_support, validate_agent_policy


STRUCTURED_FINDINGS_SPEC = """
Además de tu salida normal, DEBES terminar con este bloque exacto:
<REVIEW_FINDINGS>
{"findings":[
    {"severity":"BLOCKER|IMPORTANT|NICE","title":"...","location":"archivo:linea","details":"..."}
]}
</REVIEW_FINDINGS>

Reglas:
- Si no hay findings, usa {"findings":[]}.
- El bloque final debe ser JSON válido.
- No uses otras severidades.
""".strip()


def run_red_team(code: str, plan: str, *, workspace: Path | None = None) -> str:
    """Ejecuta CODE_CRITIC (Red Team)"""
    print("[RED] Iniciando CODE_CRITIC...")
    
    validate_agent_policy('code_critic', workspace)
    profile = load_profile('code_critic', workspace)
    model = profile.get('model', 'qwen3.5:9b')

    prompt = build_prompt(
        agent_id='code_critic',
        system=profile['system'],
        context=f"## PLAN DEL PROYECTO:\n{plan}\n\n## CÓDIGO A REVISAR:\n```\n{code}\n```",
        task="""Revisa este código buscando:
1. Problemas de SEGURIDAD (inyección, auth, validación)
2. EDGE CASES (null, vacío, valores extremos)
3. Problemas de LÓGICA (condiciones, off-by-one)
4. Problemas de PERFORMANCE (N+1, memory leaks)
5. Problemas de ARQUITECTURA (acoplamiento, God classes)

    Sigue el formato de salida obligatorio.

    """ + STRUCTURED_FINDINGS_SPEC,
        workspace=workspace,
    )

    result = run_with_tool_support(
        agent_id='code_critic',
        model=model,
        prompt=prompt,
        workspace=workspace,
        retries=2,
        timeout=1200,
    )
    print(f"[RED] CODE_CRITIC completó. {len(result)} caracteres")
    return result


def run_blue_team(critic_output: str, code: str, plan: str, *, workspace: Path | None = None) -> str:
    """Ejecuta DEFENDER (Blue Team)"""
    print("[BLUE] Iniciando DEFENDER...")
    
    validate_agent_policy('defender', workspace)
    profile = load_profile('defender', workspace)
    model = profile.get('model', 'qwen3.5:9b')

    prompt = build_prompt(
        agent_id='defender',
        system=profile['system'],
        context=(
            f"## PLAN DEL PROYECTO:\n{plan}\n\n"
            f"## CÓDIGO ORIGINAL:\n```\n{code}\n```\n\n"
            f"## CRÍTICAS DEL CODE_CRITIC:\n{critic_output}"
        ),
        task="""Para cada crítica del CODE_CRITIC, propón:
1. Solución exacta (código o pseudocódigo)
2. Archivo a modificar
3. Tests a agregar
4. Verificación

    Sigue el formato de salida obligatorio.

    """ + STRUCTURED_FINDINGS_SPEC,
        workspace=workspace,
    )

    result = run_with_tool_support(
        agent_id='defender',
        model=model,
        prompt=prompt,
        workspace=workspace,
        retries=2,
        timeout=1200,
    )
    print(f"[BLUE] DEFENDER completó. {len(result)} caracteres")
    return result


def main():
    parser = argparse.ArgumentParser(description='Red Team / Blue Team pipeline')
    parser.add_argument('--code', required=True, help='Código a revisar')
    parser.add_argument('--plan', required=True, help='Plan del PLANNER')
    parser.add_argument('--output', help='Archivo de salida (opcional)')
    parser.add_argument('--workspace', help='Workspace root para ejecutar tools en runtime')
    parser.add_argument('--skip-blue', action='store_true', help='Solo ejecutar Red Team')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else None

    # Run Red Team
    red_output = run_red_team(args.code, args.plan, workspace=workspace)
    
    if args.skip_blue:
        output = red_output
    else:
        # Run Blue Team
        blue_output = run_blue_team(red_output, args.code, args.plan, workspace=workspace)
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
