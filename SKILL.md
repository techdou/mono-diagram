---
name: mono-diagram
description: Generate, lint, and render pure black-on-white academic diagrams for papers, reports, theses, Word/PDF documents, and software-engineering documentation. Use whenever the user needs a figure for a thesis, opening report, course paper, Word/PDF report, or any document — and whenever they mention black-and-white diagrams, report figures, Mermaid or SVG diagrams, architecture/process/research-framework/sequence/matrix/UI-wireframe diagrams, flow charts, system diagrams, or printable academic figures, even if they only say “draw a diagram” or “make a figure” in the middle of a writing task.
---

# mono-diagram

Generate reproducible **pure black text on pure white background** academic diagrams from editable Mermaid or SVG sources, then lint and render them as high-resolution PNG files.

The defining rule is simple and strict: **every fill is `#ffffff`, every stroke and line is `#000000`**. Emphasis is expressed with border thickness, not gray fills. This avoids two chronic print artifacts — Mermaid's subgraph containers picking up a tinted/gray backing, and a faint gray box appearing behind edge-label text.

## Use when

- The user needs a figure for a thesis, opening report, course paper, Word/PDF report, software-engineering report, or technical document.
- The user asks for black-and-white, grayscale, printable, academic, Songti/SimSun, Mermaid, SVG, UML-like, architecture, process, sequence, matrix, research-framework, or UI-wireframe diagrams.
- The surrounding task is document/report writing and the user says only “draw a diagram” or “make a figure”.

## Do not use when

- The user wants realistic illustration, logo, poster, brand visual, colorful dashboard, or cyberpunk/large-screen visualization.
- The user needs charts from numeric data. Use the charting tool first, then apply the style guide if needed.

## Route

| Need | Source | Template |
|---|---|---|
| System layers / module relation | Mermaid | `architecture` |
| Input-process-output loop | Mermaid | `process` |
| Thesis or action-research structure | Mermaid | `research-framework` |
| Scheme comparison / decision branch | Mermaid | `compare` |
| Challenge-strategy mapping | Mermaid | `matrix` |
| Actor/tool/file interaction | Mermaid | `sequence` |
| Precise UI layout | SVG | `ui-wireframe` |
| Quadrant or card layout | SVG | `card-grid` |

Default: use Mermaid unless the layout requires pixel-level control.

## Workflow

1. Select one template with `list-templates`.
2. Create a source file with `new` or write `.mmd` / `.svg` directly. Prefer copying a bundled template — its `%%{init:...}%%` block already carries `clusterBkg`/`clusterBorder`/`edgeLabelBackground`, which keeps subgraphs and edge labels white at the theme level.
3. Validate before rendering.
4. Render to PNG.
5. Return both source and rendered PNG when possible.

## Commands

```bash
python3 scripts/mono_diagram.py list-templates
python3 scripts/mono_diagram.py new research-framework charts/fig3-1.mmd
python3 scripts/mono_diagram.py validate charts/fig3-1.mmd
python3 scripts/mono_diagram.py render charts/fig3-1.mmd -o assets/figures
```

Windows:

```powershell
py scripts\mono_diagram.py validate charts --recursive
.\scripts\render.ps1 charts -o assets\figures --recursive
```

## Quality gate

Strict mode rejects color, gray fills, and unstable effects. Keep:

- background and all fills `#ffffff` — **no gray fills** (`#f0f0f0`/`#e0e0e0`); they bleed into Mermaid's subgraph containers and edge-label backgrounds as muddy panels
- text/lines `#000000`
- emphasis via `stroke-width` (e.g. `2.5px`), never via fill
- no gradients, shadows, filters, or opacity below `1`
- short node text; use `<br/>` for Chinese labels longer than one line
- **no title or caption inside the image** — the diagram source contains only the diagram; the figure caption (`图 X-Y　图题`) is typed in Word below the image, so it stays editable and renumberable
- source file must be preserved with the PNG output

For detailed rules, read only when needed:

- `README.md` for quick start
- `docs/style-guide.md` for visual rules
- `docs/quality-gate.md` for checks
- `docs/troubleshooting.md` for render failures
- `docs/agent-routing.md` for task-to-template examples
