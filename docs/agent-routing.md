# Agent routing examples

Use this file only when `SKILL.md` is not enough.

## Opening report research framework

User: “帮我画一个开题报告研究框架图。”

Route:

```bash
python3 scripts/mono_diagram.py new research-framework charts/fig3-1.mmd
python3 scripts/mono_diagram.py validate charts/fig3-1.mmd
python3 scripts/mono_diagram.py render charts/fig3-1.mmd -o assets/figures
```

Return `.mmd` and `.png`.

## Software architecture figure

User: “给这个系统做一张黑白架构图。”

Route: `architecture` template. Use Mermaid. Keep layers clear and avoid adding decorative nodes.

## Challenge-strategy matrix

User: “把问题和优化方案整理成图。”

Route: `matrix` template. Use one challenge row/branch per problem, then merge into the final goal.

## UI prototype

User: “画一个报告里的系统原型图，黑字白底。”

Route: `ui-wireframe` template. Use SVG because layout precision matters.

## Do not over-expand

Do not add PlantUML, Graphviz, Word automation, or data-chart generation unless the user explicitly requests that extension. Keep the core flow small: template → validate → render.
