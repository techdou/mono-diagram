# Review notes for v1.2.0

## Programmer review

v1.1.0 was usable but not yet engineering-grade. Main issues fixed in v1.2.0:

- renderer dependencies were not pinned;
- Mermaid `%%{init: ...}%%` colors could bypass linting;
- SVG `opacity="0.5"`, `fill-opacity`, and `stroke-opacity` could bypass linting;
- `rgb()/rgba()/hsl()` and named colors were not checked;
- dry-run wrote output metadata unexpectedly;
- no minimal regression tests existed;
- Windows entry points were missing.

## User review

v1.1.0 had a clear purpose but required manual template copying. v1.2.0 adds:

- `list-templates` to discover choices;
- `new` to create a figure source quickly;
- gallery previews;
- shorter `SKILL.md` and clearer `README.md`;
- separate docs for deeper details.

## Remaining intentional limits

The skill intentionally does not include PlantUML, Graphviz, Word automation, or data visualization pipelines. Those should be separate skills or future extensions.
