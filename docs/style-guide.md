# Style guide

Keep academic diagrams readable after grayscale printing and Word/PDF scaling.

## Palette

Pure-white fill with black strokes/lines is the only supported fill style.
Gray fills were removed because Mermaid's subgraph containers and edge-label
backgrounds also inherit the theme's secondary/tertiary gray, which prints as
muddy panels and gray boxes behind arrow text. A single consistent rule —
**white fill, black stroke** — keeps every rendered element clean.

```text
background:        #ffffff   (强制，唯一允许的填充)
text / line:       #000000
emphasis:          用更粗的边框 stroke-width:2.5px 表达，而非灰底
```

Color tokens to **avoid** (they re-introduce the gray/grayed backing we removed):

```text
#f0f0f0, #e0e0e0, #f7f7f7, #fafafa, #dddddd, #cccccc   ← 不要用作 fill
```

If you need to emphasize a node (e.g. the "recommended" branch), raise its
`stroke-width` to `2.5px` instead of changing the fill. Templates already do
this. Colored HEX, named colors, RGB, HSL, gradients, shadows, filters, and
opacity below `1` are still rejected in strict mode.

## Typography

Recommended fallback chain:

```text
SimSun, Songti SC, Noto Serif CJK SC, Times New Roman, serif
```

Use short labels. For Chinese node labels, prefer 10–14 characters per line and insert `<br/>` manually.

## Layout

- One diagram should communicate one conclusion.
- Use Mermaid for relationship/process diagrams.
- Use SVG only for pixel-level UI or quadrant layouts.
- Avoid dense all-in-one diagrams; split when the figure exceeds one Word page width.

## Why the templates carry extra themeVariables

Every Mermaid template now injects `clusterBkg`, `clusterBorder`, and
`edgeLabelBackground` into its `%%{init:...}%%` block. These force subgraph
backings and edge-label boxes to pure white at the Mermaid theme level, so the
diagram is correct even if a renderer ignores the bundled CSS. Keep these
variables when you copy a template.

## Word/PDF use

- Keep figure width around 70%–90% of body width.
- **Do not put any title or caption inside the image.** The diagram source must contain only the diagram content. Captions like `图 X-Y　图题` are typed in Word below the image so they stay editable and renumberable.
- Explain the figure in the paragraph before or after it.
