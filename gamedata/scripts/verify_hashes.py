#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de integridade dos arquivos contra o manifest.json.

Dois modos de uso:

1) LOCAL (padrao) - confere os arquivos que estao no repositorio:
    python scripts/verify_hashes.py
   Recalcula tamanho e SHA-256 de cada arquivo e compara com o manifest.
   Se voce acabou de substituir um arquivo e ainda nao rodou o gerador,
   ele vai apontar como CHANGED (e voce deve rodar generate_manifest.py).

2) REMOTO - confere o que esta publicado no GitHub (o que o Launcher
   vera no futuro):
    python scripts/verify_hashes.py --remote
   Baixa cada arquivo pela URL do manifest e confere o SHA-256 real.

Nao requer dependencias externas (somente Python 3 padrao).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

CHUNK = 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_url(url: str, timeout: int = 120) -> str:
    h = hashlib.sha256()
    req = Request(url, headers={"User-Agent": "gamedata-verifier/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    default_root = Path(__file__).resolve().parent.parent

    ap = argparse.ArgumentParser(description="Verifica hashes do manifest.json.")
    ap.add_argument("--root", type=Path, default=default_root,
                    help="raiz do repositorio (padrao: %(default)s)")
    ap.add_argument("--manifest", type=Path, default=None,
                    help="caminho do manifest.json (padrao: <root>/manifest.json)")
    ap.add_argument("--remote", action="store_true",
                    help="verifica os arquivos pela URL publica (GitHub)")
    ap.add_argument("--category", default=None,
                    help="verifica apenas uma categoria (ex.: vehicles)")
    args = ap.parse_args()

    root = args.root.resolve()
    manifest_path = (args.manifest or root / "manifest.json").resolve()

    if not manifest_path.is_file():
        print("Erro: manifest.json nao encontrado em %s" % manifest_path)
        return 1

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = data.get("files", [])
    if args.category:
        entries = [e for e in entries if e.get("category") == args.category]

    if not entries:
        print("Manifest nao contem arquivos%s." %
              (" dessa categoria" if args.category else ""))
        return 0

    ok = changed = missing = 0
    errors = []

    print("Modo: %s | %d arquivo(s) para verificar" %
          ("REMOTO (GitHub)" if args.remote else "LOCAL", len(entries)))
    print("-" * 72)

    for e in entries:
        path, expected = e["path"], e["sha256"]
        try:
            if args.remote:
                actual = sha256_url(e["url"])
            else:
                local = root / path
                if not local.is_file():
                    print("  [MISSING] %s" % path)
                    missing += 1
                    errors.append(path)
                    continue
                actual = sha256_file(local)
            if actual == expected:
                ok += 1
                print("  [OK]      %s" % path)
            else:
                changed += 1
                errors.append(path)
                print("  [CHANGED] %s" % path)
                print("            manifest: %s" % expected)
                print("            real    : %s" % actual)
        except Exception as exc:  # noqa: BLE001
            missing += 1
            errors.append(path)
            print("  [ERROR]   %s -> %s" % (path, exc))

    print("-" * 72)
    print("Resultado: %d OK | %d divergentes | %d ausentes/erro" % (ok, changed, missing))
    if errors:
        print("Acao: rode 'python scripts/generate_manifest.py' para sincronizar o manifest")
        print("      (ou verifique os arquivos listados acima).")
        return 1
    print("Tudo certo: manifest e arquivos estao consistentes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
