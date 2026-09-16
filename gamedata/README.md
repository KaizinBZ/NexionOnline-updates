# NexionOnline · Game Data

Central de distribuição de **Game Data** do NexionOnline: veículos, modelos DFF, texturas TXD, skins, mapas, sons e modificações.

Esta central vive dentro da pasta **`gamedata/`** do repositório `KaizinBZ/NexionOnline-updates` — separada do sistema de atualização do APK, que continua usando o `update.json` na raiz.

Aqui **não existe lógica de launcher** — este repositório é apenas a central de distribuição de arquivos. Qualquer programa (launcher, updater, app) pode consultar o `manifest.json`, comparar hashes/versões e baixar apenas o que mudou.

---

## 📁 Estrutura do repositório

| Pasta | O que vai dentro | Exemplos |
|---|---|---|
| `vehicles/` | Veículos completos (crie uma subpasta por veículo) | `vehicles/nome-do-carro/modelo.dff` |
| `dff/` | Arquivos DFF avulsos (modelos 3D) | `dff/objeto.dff` |
| `txd/` | Arquivos TXD avulsos (pacotes de textura) | `txd/pacote.txd` |
| `textures/` | Texturas avulsas (imagens) | `textures/parede.png` |
| `skins/` | Skins de personagem | `skins/skin01.dff`, `skins/skin01.txd` |
| `maps/` | Mapas e objetos de mapa | `maps/losantos.ipl`, `maps/objeto.col` |
| `sounds/` | Sons e músicas | `sounds/sirene.wav`, `sounds/radio.mp3` |
| `mods/` | Modificações de qualquer tipo | `mods/cleo/algum-mod.cs` |
| `other/` | Qualquer outro Game Data | `other/config.ini` |
| `scripts/` | **Não mexa** — gerador e verificador do manifest | — |

> Dica: prefira nomes de arquivo/pasta **sem acento e sem espaço** (use `-` ou `_`). Evita problemas de URL e codificação.

---

## 1. Como adicionar um veículo

1. Crie uma pasta dentro de `vehicles/` com o nome do veículo:
   ```
   vehicles/meu-carro/
   ```
2. Coloque o `.dff` e o `.txd` do veículo nessa pasta:
   ```
   vehicles/meu-carro/modelo.dff
   vehicles/meu-carro/textura.txd
   ```
3. Gere o manifest (veja o item **6**).

## 2. Como adicionar DFF / TXD

Coloque o arquivo na pasta correspondente:

```
dff/meu-modelo.dff
txd/minha-textura.txd
```

Se o DFF/TXD pertence a um veículo, coloque na pasta do veículo em `vehicles/` (fica tudo junto).

## 3. Como adicionar texturas

Coloque o arquivo de textura em `textures/`:

```
textures/minha-textura.png
textures/paredes/tijolo.jpg
```

## 4. Como adicionar outros Game Data

Escolha a pasta certa para o tipo de arquivo:

- Skins → `skins/`
- Mapas → `maps/`
- Sons → `sounds/`
- Modificações → `mods/`
- Nenhuma das anteriores → `other/`

## 5. Como atualizar um arquivo existente

1. **Simplesmente substitua o arquivo** no mesmo caminho (ex.: substituiu `vehicles/meu-carro/modelo.dff` por uma versão nova? sobrescreva-o).
2. Rode o gerador (item **6**).
3. O gerador detecta que o SHA-256 mudou **só nesse arquivo**:
   - o hash e o tamanho dele são atualizados;
   - a versão dele é incrementada automaticamente (`1.0.0` → `1.0.1`);
   - **todos os outros arquivos permanecem exatamente iguais** no manifest.

Adicionar um veículo/textura/arquivo novo funciona igual: o gerador encontra o arquivo e o registra no manifest com versão `1.0.0`.

## 6. Como executar o gerador do manifest

**Opção A — automático (recomendado):** basta dar `git push` no repositório. Uma GitHub Action roda o gerador e publica o `manifest.json` atualizado sozinha. Você não precisa fazer nada.

**Opção B — manual, no seu PC** (precisa só de Python 3 instalado):

```bash
python3 scripts/generate_manifest.py
git add manifest.json
git commit -m "Atualiza manifest"
git push
```

Opções úteis do gerador:

```bash
# Só mostrar o que mudaria, sem gravar
python3 scripts/generate_manifest.py --dry-run

# Incrementar versão maior (1.0.0 -> 1.1.0) em vez de patch
python3 scripts/generate_manifest.py --bump minor

# Definir a versão de um arquivo manualmente
python3 scripts/generate_manifest.py --set-version vehicles/meu-carro/modelo.dff=2.0.0
```

## 7. Como verificar os hashes

**Conferir os arquivos locais contra o manifest** (antes de publicar):

```bash
python3 scripts/verify_hashes.py
```

**Conferir o que está publicado no GitHub** (baixa cada arquivo pela URL e confere o SHA-256 real):

```bash
python3 scripts/verify_hashes.py --remote
```

**Verificar só uma categoria:**

```bash
python3 scripts/verify_hashes.py --category vehicles
```

Se algo aparecer como `CHANGED`, rode o gerador (item 6) para sincronizar o manifest.

## 8. Onde encontrar as URLs dos arquivos

Abra o **`manifest.json`** na raiz do repositório. Cada arquivo tem sua URL de download no campo `url`:

```json
{
  "path": "vehicles/meu-carro/modelo.dff",
  "category": "vehicles",
  "size": 245760,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "version": "1.0.1",
  "url": "https://raw.githubusercontent.com/KaizinBZ/NexionOnline-updates/main/gamedata/vehicles/meu-carro/modelo.dff",
  "updated_at": "2026-09-16T20:13:55Z"
}
```

O padrão das URLs é sempre:

```
https://raw.githubusercontent.com/KaizinBZ/NexionOnline-updates/main/gamedata/<caminho-do-arquivo>
```

Onde `<caminho-do-arquivo>` é o valor do campo `path` (relativo a `gamedata/`).

---

## 📄 Sobre o manifest.json

- É a **fonte única de verdade** da central de Game Data.
- Campos de topo: `repository`, `branch`, `generated_at`, `total_files`, `total_size` e `files`.
- Cada entrada guarda: `path` (caminho relativo), `category` (primeira pasta), `size` (bytes), `sha256` (hash SHA-256), `version` (semântica por arquivo), `url` (download direto) e `updated_at`.
- O arquivo é **gerado**: não edite `manifest.json` à mão — rode o gerador.

### Como outro programa detecta mudanças (futuro launcher)

1. Baixa o `manifest.json` do GitHub.
2. Compara o `sha256` (ou `version`) de cada entrada com o que ele tem localmente.
3. Baixa pela `url` apenas os arquivos cujo hash/versão mudou.

Nenhuma lógica disso vive aqui — o repositório só garante que o manifest está sempre correto e atualizado.

---

## ⚠️ Limites e boas práticas

- O GitHub **recusa arquivos acima de 100 MB**. Para Game Data grande, prefira vários arquivos menores.
- Evite arquivos acima de ~50 MB: o download via `raw.githubusercontent.com` pode falhar em conexões instáveis.
- Não coloque aqui nada que não seja Game Data (nem código de launcher, nem APKs).

## 🤖 Automação

O workflow `.github/workflows/update-manifest.yml` roda o gerador a cada push na `main` e publica o manifest atualizado automaticamente (as mudanças entram como commit do bot com `[skip ci]`, evitando loop).
