# Changelog

## v1.3.0

Pure-white fill policy and Windows render fix. Eliminates the two chronic
print artifacts users hit: tinted backing on Mermaid subgraph containers and
a gray box behind edge-label text.

- **Pure-white fill as the only supported fill.** All templates now use `#ffffff` everywhere; emphasis is expressed via thicker borders (`stroke-width: 2.5px`) instead of gray fills.
- **`mono-mermaid.json`** now sets `clusterBkg`/`clusterBorder`/`edgeLabelBackground` (and `secondaryColor`/`tertiaryColor`) to white, forcing subgraph and edge-label backgrounds white at the Mermaid theme level.
- **`mono.css`** hardened with `!important` rules covering `.cluster`, `.edgeLabel`, `.labelBkg`, and their nested elements, so the diagram stays clean even if a renderer ignores the theme config.
- **All bundled templates** (architecture, process, research-framework, compare, matrix, sequence, card-grid, ui-wireframe) rewritten to pure-white fills and carry the new `themeVariables`.
- **`style-guide.md` / `quality-gate.md`** updated: gray fills (`#f0f0f0`/`#e0e0e0`) moved from "recommended" to "avoid", with the reason explained.
- **`SKILL.md`** description made more assertive for triggering during document-writing tasks; quality gate now lists the pure-white rule up front.
- **Fixed `mono_diagram.py` Windows rendering** — bare `npx` was not resolvable from Python's `subprocess` (it is `npx.cmd`), raising `[WinError 2] 系统找不到指定的文件`. `local_bin()`/`command_for()`/`run()` now resolve the launcher explicitly and fall back to `shell=True` for un-resolved shims. The skill's own `render` command now works end-to-end on Windows.

## v1.2.0

Engineering hardening and progressive-disclosure cleanup.

- Moved templates to `assets/templates/`.
- Added pinned Node dependency declarations in `package.json` and `package-lock.json`.
- Added `list-templates` and `new` CLI commands.
- Strengthened linting for Mermaid init colors, SVG opacity attributes, `rgb()/rgba()/hsl()`, named colors, dynamic CSS colors, gradients, filters, and shadows.
- Fixed dry-run semantics: `--dry-run` no longer writes a manifest unless `--dry-run-manifest` is used.
- Added Windows PowerShell entry scripts.
- Added `tests/` fixtures and unittest coverage for main lint cases.
- Added `gallery/` preview images.
- Reduced `SKILL.md` to core routing and moved details into `docs/`.

## v1.1.0

- Added core CLI validation/render dispatcher.
- Added Mermaid/SVG templates.
- Added style and troubleshooting docs.
