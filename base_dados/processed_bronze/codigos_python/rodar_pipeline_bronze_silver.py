from __future__ import annotations

import subprocess
import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parent


def run(script_name: str) -> None:
    script_path = CODE_DIR / script_name
    print("\n" + "=" * 80)
    print(f"Rodando {script_name}")
    print("=" * 80)
    subprocess.run([sys.executable, str(script_path)], check=True)


def main() -> None:
    run("rodar_todas_padronizacoes.py")
    run("gerar_silver_todas_fontes.py")
    print("\nPipeline bronze + silver concluido.")


if __name__ == "__main__":
    main()
