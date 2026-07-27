# mono-diagram | 黑白学术图

[English](#english) | [中文](#中文)

---

<a id="中文"></a>
## 中文

轻量 Agent Skill，用于生成**纯黑白学术图**：创建 Mermaid/SVG 源码，lint 检查黑白打印安全性，渲染高分辨率 PNG 供 Word/PDF 报告使用。

### 触发场景

- 论文、开题报告、课程论文、Word/PDF 报告配图
- 黑白图、报告图、架构/流程/研究框架/时序/矩阵/UI 线框图
- Mermaid、SVG 流程图、系统图
- 写作过程中需要"画个图"、"做张示意图"

下方英文为完整文档。

---

<a id="english"></a>
## English

A compact skill for **monochrome academic diagrams**: create Mermaid/SVG sources, lint them for black-and-white print safety, and render high-resolution PNG files for Word/PDF reports.

Current version: **v1.2.0**.

## Quick start

```bash
# optional but recommended: install pinned render dependencies
npm install

# see available templates
python3 scripts/mono_diagram.py list-templates

# create a figure source
python3 scripts/mono_diagram.py new architecture charts/fig2-1.mmd

# edit charts/fig2-1.mmd, then validate
python3 scripts/mono_diagram.py validate charts/fig2-1.mmd

# render to PNG
python3 scripts/mono_diagram.py render charts/fig2-1.mmd -o assets/figures
```

Shell shortcuts:

```bash
bash scripts/validate.sh charts --recursive
bash scripts/render.sh charts -o assets/figures --recursive
```

Windows PowerShell:

```powershell
py scripts\mono_diagram.py new research-framework charts\fig3-1.mmd
.\scripts\validate.ps1 charts --recursive
.\scripts\render.ps1 charts -o assets\figures --recursive
```

## Template list

| Template | Best for | Source |
|---|---|---|
| `architecture` | system layers, module architecture | Mermaid |
| `process` | workflow, closed-loop process | Mermaid |
| `research-framework` | thesis framework, action research | Mermaid |
| `compare` | branch comparison, scheme comparison | Mermaid |
| `matrix` | challenge-strategy mapping | Mermaid |
| `sequence` | actor/tool/file interaction | Mermaid |
| `ui-wireframe` | UI prototype and panel layout | SVG |
| `card-grid` | quadrant/card matrix | SVG |

Preview images are stored in `gallery/`.

## What v1.2.0 improves

- Pinned Node render packages in `package.json`.
- `new` and `list-templates` commands.
- Stronger linting for Mermaid init colors, SVG opacity attributes, `rgb()/rgba()/hsl()`, named colors, and dynamic CSS colors.
- `--dry-run` no longer writes a manifest unless `--dry-run-manifest` is explicitly provided.
- Windows PowerShell entry scripts.
- Minimal test suite for core lint failures.
- Leaner `SKILL.md` with progressive disclosure through `docs/`.

## Commands

```bash
# list templates
python3 scripts/mono_diagram.py list-templates

# create from template
python3 scripts/mono_diagram.py new matrix charts/fig4-2.mmd

# overwrite existing source intentionally
python3 scripts/mono_diagram.py new process charts/fig2-2.mmd --force

# validate only
python3 scripts/mono_diagram.py validate charts --recursive

# dry-run rendering plan; writes no output files and no manifest
python3 scripts/mono_diagram.py render charts -o assets/figures --recursive --dry-run

# force render even with lint errors
python3 scripts/mono_diagram.py render charts --allow-lint-errors

# downgrade strict errors to warnings
python3 scripts/mono_diagram.py render charts --no-strict
```

## Suggested project layout

```text
project/
├── charts/              # editable .mmd / .svg sources
├── assets/figures/      # rendered PNG files
└── report.docx
```

## Directory layout

```text
mono-diagram/
├── SKILL.md
├── README.md
├── package.json
├── package-lock.json
├── docs/
├── assets/
│   ├── templates/
│   └── config/
├── gallery/
├── scripts/
└── tests/
```

## More detail

- Style rules: `docs/style-guide.md`
- Quality gate: `docs/quality-gate.md`
- Troubleshooting: `docs/troubleshooting.md`
- Word/PDF use: `docs/word-integration.md`
- Agent routing examples: `docs/agent-routing.md`
