# Word/PDF integration

## Figure insertion

- Insert PNG into Word/PDF at 70%–90% body width.
- Keep aspect ratio locked.
- Avoid stretching screenshots manually.

## Caption format

**Captions are written in Word, NOT baked into the image.** The rendered PNG contains only the diagram itself — no title text. Add the caption as a normal paragraph below the inserted image:

```text
图 X-Y　图题
```

Recommended style: centered, SimSun, size 10.5 pt or the document's required caption style.

Why keep the caption outside the image: it stays editable, matches the document font automatically, survives image resizing, and lets you renumber figures without re-rendering.

## Text integration

Before the figure:

```text
系统的总体结构如图 X-Y 所示。
```

After the figure, explain the structure, flow, or conclusion. Do not leave the figure isolated.
