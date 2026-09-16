#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador / atualizador do manifest.json do repositorio de Game Data.

Percorre todos os arquivos do repositorio, calcula o tamanho e o SHA-256
de cada arquivo e atualiza o manifest.json de forma INCREMENTAL:

  - arquivo novo               -> adicionado ao manifest com versao 1.0.0
  - arquivo alterado (hash)    -> hash/tamanho atualizados e versao
                                  incrementada (patch por padrao)
  - arquivo inalterado         -> entrada mantida IGUAL (mesma versao,
                                  mesmo hash, mesma data)
  - arquivo removido do repos  -> entrada removida do manifest

O launcher (futuro) pode comparar o SHA-256/versao de cada entrada com o
que ele tem localmente e baixar apenas o que mudou.

Uso basico:
    python scripts/generate_manifest.py

Opcoes principais:
    --root DIR              raiz do repositorio (padrao: pasta acima de scripts/)
    --manifest FILE         caminho do manifest.json (padrao: <root>/manifest.json)
    --repo OWNER/REPO       slug do repositorio usado nas URLs de download
    --branch NOME           branch usado nas URLs (padrao: main)
    --url-prefix PASTA      caminho do gamedata dentro do repositorio (padrao: gamedata)
    --bump patch|minor|major  nivel de incremento de versao (padrao: patch)
    --set-version CAMINHO=1.2.3  define a versao de um arquivo manualmente
    --dry-run               mostra o que mudaria sem gravar nada

Nao requer dependencias externas (somente Python 3 padrao).
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

# ---------------------------------------------------------------
# Configuracao padrao (pode ser sobrescrita por linha de comando)
# ---------------------------------------------------------------
DEFAULT_REPO = "KaizinBZ/NexionOnline-updates"
# Pasta do gamedata dentro do repositorio (usada nas URLs de download);
# use "" (vazio) se o gamedata estiver na raiz do repositorio.
DEFAULT_URL_PREFIX = "gamedata"
DEFAULT_BRANCH = "main"
SCHEMA_VERSION = 1

# Pastas que NUNCA entram no manifest (estrutura do repositorio, nao sao Game Data)
SKIP_DIRS = {".git", ".github", "scripts", "__pycache__", ".vscode",
             "node_modules", ".idea", ".gitattributes"}

# Arquivos que NUNCA entram no manifest
SKIP_FILES = {"manifest.json", "README.md", ".gitignore", ".gitkeep",
              "LICENSE", ".gitattributes", ".DS_Store", "Thumbs.db", "desktop.ini"}


def sha256_of(path: Path) -> str:
    """Calcula o SHA-256 de um arquivo lendo em blocos (aguenta arquivos grandes)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def bump_version(version: str, level: str) -> str:
    """Incrementa uma versao semantica x.y.z no nivel pedido."""
    try:
        major, minor, patch = (int(x) for x in version.split("."))
    except (ValueError, TypeError):
        major, minor, patch = 1, 0, 0
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"  # padrao: patch


def category_of(rel_path: Path) -> str:
    """Categoria = primeira pasta do caminho relativo. Arquivo na raiz vira 'other'."""
    parts = rel_path.parts
    return parts[0] if len(parts) > 1 else "other"


def download_url(repo: str, branch: str, url_prefix: str, rel_path: Path) -> str:
    """URL publica de download do arquivo (raw.githubusercontent.com)."""
    parts = [repo, branch] + ([url_prefix.strip("/")] if url_prefix.strip("/") else [])
    return "https://raw.githubusercontent.com/{}/{}".format(
        "/".join(parts), quote(rel_path.as_posix(), safe="/")
    )


def scan_files(root: Path):
    """Percorre o repositorio e devolve a lista de caminhos relativos validos."""
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts[0] in SKIP_DIRS:
            continue
        if path.name in SKIP_FILES:
            continue
        files.append(rel)
    return files


def load_previous_manifest(manifest_path: Path) -> dict:
    """Le o manifest atual (se existir) e devolve {caminho: entrada}."""
    if not manifest_path.is_file():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = data.get("files", [])
        return {e["path"]: e for e in entries if "path" in e}
    except (ValueError, KeyError):
        print("Aviso: manifest.json existente invalido, comecando do zero.")
        return {}


def parse_version_overrides(pairs):
    """Converte argumentos --set-version CAMINHO=VERSAO em um dicionario."""
    overrides = {}
    for item in pairs or []:
        if "=" not in item:
            print("Aviso: --set-version ignorado (formato esperado CAMINHO=VERSAO): %s" % item)
            continue
        path, version = item.split("=", 1)
        overrides[path.strip()] = version.strip()
    return overrides


def main() -> int:
    default_root = Path(__file__).resolve().parent.parent

    ap = argparse.ArgumentParser(
        description="Gera/atualiza o manifest.json do repositorio de Game Data."
    )
    ap.add_argument("--root", type=Path, default=default_root,
                    help="raiz do repositorio (padrao: %(default)s)")
    ap.add_argument("--manifest", type=Path, default=None,
                    help="caminho do manifest.json (padrao: <root>/manifest.json)")
    ap.add_argument("--repo", default=DEFAULT_REPO,
                    help="slug OWNER/REPO usado nas URLs (padrao: %(default)s)")
    ap.add_argument("--branch", default=DEFAULT_BRANCH,
                    help="branch usado nas URLs (padrao: %(default)s)")
    ap.add_argument("--url-prefix", default=DEFAULT_URL_PREFIX,
                    help="caminho do gamedata dentro do repositorio, usado nas URLs (padrao: %(default)s)")
    ap.add_argument("--bump", choices=["patch", "minor", "major"], default="patch",
                    help="nivel de incremento de versao em arquivo alterado (padrao: patch)")
    ap.add_argument("--set-version", action="append", metavar="CAMINHO=VERSAO",
                    help="define versao manual de um arquivo (repetivel)")
    ap.add_argument("--dry-run", action="store_true",
                    help="nao grava nada, apenas mostra o resultado")
    args = ap.parse_args()

    root = args.root.resolve()
    manifest_path = (args.manifest or root / "manifest.json").resolve()
    overrides = parse_version_overrides(args.set_version)

    if not root.is_dir():
        print("Erro: raiz nao encontrada: %s" % root)
        return 1

    previous = load_previous_manifest(manifest_path)
    new_entries = []
    added, updated, unchanged = [], [], []

    for rel in scan_files(root):
        path = root / rel
        rel_posix = rel.as_posix()
        size = path.stat().st_size
        sha = sha256_of(path)

        old = previous.get(rel_posix)
        now = utcnow()

        if old and old.get("sha256") == sha and old.get("size") == size:
            # Nada mudou -> mantem a entrada exatamente igual (versao preservada)
            entry = {
                "path": rel_posix,
                "category": old.get("category", category_of(rel)),
                "size": size,
                "sha256": sha,
                "version": old.get("version", "1.0.0"),
                "url": old.get("url", download_url(args.repo, args.branch, args.url_prefix, rel)),
                "updated_at": old.get("updated_at", now),
            }
            unchanged.append(rel_posix)
        elif old:
            # Arquivo alterado -> atualiza hash/tamanho e bump na versao
            version = overrides.pop(rel_posix, None) or bump_version(old.get("version", "1.0.0"), args.bump)
            entry = {
                "path": rel_posix,
                "category": old.get("category", category_of(rel)),
                "size": size,
                "sha256": sha,
                "version": version,
                "url": download_url(args.repo, args.branch, args.url_prefix, rel),
                "updated_at": now,
            }
            updated.append("%s  (%s -> %s)" % (rel_posix, old.get("version", "1.0.0"), version))
        else:
            # Arquivo novo
            version = overrides.pop(rel_posix, "1.0.0")
            entry = {
                "path": rel_posix,
                "category": category_of(rel),
                "size": size,
                "sha256": sha,
                "version": version,
                "url": download_url(args.repo, args.branch, args.url_prefix, rel),
                "updated_at": now,
            }
            added.append("%s  (v%s)" % (rel_posix, version))

        new_entries.append(entry)

    # Entradas que existiam no manifest mas o arquivo sumiu do repositorio
    removed = [p for p in previous if p not in {e["path"] for e in new_entries}]

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "repository": args.repo,
        "branch": args.branch,
        "generated_at": utcnow(),
        "total_files": len(new_entries),
        "total_size": sum(e["size"] for e in new_entries),
        "files": sorted(new_entries, key=lambda e: e["path"]),
    }

    # ------------------------------------------------------------
    # Relatorio
    # ------------------------------------------------------------
    print("=" * 64)
    print("Manifest: %s" % manifest_path)
    print("=" * 64)
    print("Arquivos no repositorio : %d" % len(new_entries))
    print("  - inalterados         : %d" % len(unchanged))
    print("  - atualizados         : %d" % len(updated))
    print("  - adicionados         : %d" % len(added))
    print("  - removidos           : %d" % len(removed))
    print("-" * 64)
    for line in added:
        print("  [+] %s" % line)
    for line in updated:
        print("  [~] %s" % line)
    for line in removed:
        print("  [-] %s" % line)
    if overrides:
        for p in overrides:
            print("  [!] --set-version sem efeito (arquivo nao encontrado): %s" % p)
    print("=" * 64)

    if args.dry_run:
        print("DRY-RUN: nada foi gravado.")
        return 0

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("manifest.json atualizado com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
