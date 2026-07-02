# Troubleshooting

## `npx not found`

Install Node.js, then run:

```bash
npm install
```

The renderer first tries local binaries from `node_modules/.bin`; if unavailable, it falls back to pinned `npx` packages.

## Mermaid rendering fails

Try validation first:

```bash
python3 scripts/mono_diagram.py validate charts/fig.mmd
```

Common causes:

- invalid Mermaid syntax
- unescaped special characters
- node text too long
- unsupported Mermaid version syntax

## SVG rendering fails

Check that the SVG is valid XML and has a root `<svg>` element.

```bash
python3 scripts/mono_diagram.py validate charts/fig.svg
```

## `--dry-run` did not create a manifest

This is expected in v1.2.0. Use:

```bash
python3 scripts/mono_diagram.py render charts --dry-run --dry-run-manifest
```

## Windows PowerShell execution policy blocks scripts

Use the Python command directly:

```powershell
py scripts\mono_diagram.py validate charts --recursive
py scripts\mono_diagram.py render charts -o assets\figures --recursive
```
