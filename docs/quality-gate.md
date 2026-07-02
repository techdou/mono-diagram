# Quality gate

Run validation before rendering:

```bash
python3 scripts/mono_diagram.py validate charts --recursive
```

A deliverable passes when:

1. Source file exists: `.mmd` or `.svg`.
2. Rendered PNG exists when rendering was requested.
3. **All fills are pure white `#ffffff`.** No gray fills (`#f0f0f0`/`#e0e0e0`/`#f7f7f7`/…) — these re-introduce the muddy backing behind subgraphs and edge labels that we removed. Emphasize a node with a thicker border (`stroke-width:2.5px`), never with a fill.
4. No colored HEX, RGB, HSL, or named color is used.
5. No gradients, filters, shadows, or opacity below `1` are used.
6. Mermaid files include a mono `%%{init: ...}%%` block **with `clusterBkg`/`clusterBorder`/`edgeLabelBackground`** (the bundled templates already do — keep these variables when copying).
7. SVG files include `viewBox`, fixed width/height, white background, and font-family.
8. Nodes remain readable after scaling into Word/PDF.
9. **No tinted backing on subgraphs and no gray box behind edge-label text.** If you see either, the source is missing the `clusterBkg`/`edgeLabelBackground` variables — copy a bundled template instead of hand-writing the init block.
10. The figure is referenced in the surrounding text, and **the caption is written in Word below the image — not baked into the diagram source**. The source must contain no title or caption text.

Strict errors should be fixed rather than bypassed. Use `--allow-lint-errors` only for debugging.
