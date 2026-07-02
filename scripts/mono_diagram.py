#!/usr/bin/env python3
"""mono_diagram.py

Validate, scaffold, and render monochrome academic diagrams.

Supported sources:
  - Mermaid: .mmd
  - SVG: .svg

Design goals:
  - no Python third-party dependency
  - deterministic CLI routing
  - strict mono quality gate before rendering
  - small surface area suitable for Agent skills
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET

VERSION = "1.3.0"
SUPPORTED = {".mmd", ".svg"}
MERMAID_CLI_PACKAGE = "@mermaid-js/mermaid-cli@10.9.1"
SHARP_CLI_PACKAGE = "sharp-cli@4.2.0"

RECOMMENDED_GRAYS = {
    "#000000", "#111111", "#222222", "#333333", "#666666", "#999999",
    "#e0e0e0", "#f0f0f0", "#f7f7f7", "#fafafa", "#ffffff",
}
ALLOWED_NAMED_GRAYS = {"black", "white", "gray", "grey", "darkgray", "darkgrey", "lightgray", "lightgrey", "transparent"}
DISALLOWED_COLOR_NAMES = {
    "red", "green", "blue", "yellow", "orange", "purple", "pink", "cyan", "magenta",
    "brown", "lime", "navy", "teal", "aqua", "maroon", "olive", "violet", "gold", "silver",
}
FONT_HINTS = ("SimSun", "Songti", "Noto Serif CJK", "Times New Roman", "serif")
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "assets" / "templates"
CONFIG_DIR = Path(__file__).resolve().parents[1] / "assets" / "config"

HEX_RE = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b")
RGB_RE = re.compile(r"\brgba?\s*\(([^)]+)\)", re.IGNORECASE)
HSL_RE = re.compile(r"\bhsla?\s*\(([^)]+)\)", re.IGNORECASE)
NODE_TEXT_RE = re.compile(r"\[\"?([^\]\"]+)\"?\]")
NAMED_COLOR_PROP_RE = re.compile(
    r"(?:fill|stroke|color|background(?:-color)?|primaryColor|lineColor|BorderColor|TextColor)\s*[:=]\s*['\"]?([A-Za-z]+)\b",
    re.IGNORECASE,
)
OPACITY_RE = re.compile(r"\b(?:opacity|fill-opacity|stroke-opacity)\s*(?:=|:)\s*['\"]?([0-9.]+)", re.IGNORECASE)
CSS_VAR_COLOR_RE = re.compile(r"(?:fill|stroke|color|background(?:-color)?)\s*[:=]\s*['\"]?(var\(|currentColor)", re.IGNORECASE)


@dataclass
class Issue:
    level: str
    file: str
    message: str


@dataclass
class Result:
    source: str
    output: Optional[str]
    kind: str
    status: str
    issues: List[Issue]
    command: Optional[List[str]] = None
    error: Optional[str] = None


def issue(level: str, file: Path, msg: str) -> Issue:
    return Issue(level, str(file), msg)


def warn(file: Path, msg: str) -> Issue:
    return issue("warn", file, msg)


def error(file: Path, msg: str) -> Issue:
    return issue("error", file, msg)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def norm_hex(value: str) -> str:
    v = value.lower()
    if len(v) == 4:
        v = "#" + "".join(ch * 2 for ch in v[1:])
    return v


def is_gray_hex(value: str) -> bool:
    v = norm_hex(value).lstrip("#")
    return len(v) == 6 and v[0:2] == v[2:4] == v[4:6]


def _parse_rgb_piece(piece: str) -> Optional[float]:
    p = piece.strip()
    if p.endswith("%"):
        try:
            return float(p[:-1]) * 2.55
        except ValueError:
            return None
    try:
        return float(p)
    except ValueError:
        return None


def _split_function_args(raw: str) -> List[str]:
    if "/" in raw:  # CSS rgb(0 0 0 / 1) form
        raw = raw.replace("/", " ")
    if "," in raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return [p.strip() for p in raw.split() if p.strip()]


def validate_color_tokens(path: Path, text: str, strict: bool) -> List[Issue]:
    issues: List[Issue] = []
    seen_hex = set()
    for raw in HEX_RE.findall(text):
        h = norm_hex(raw)
        if h in seen_hex:
            continue
        seen_hex.add(h)
        if not is_gray_hex(h):
            msg = f"发现彩色 HEX {raw}；请改为 #000000 / #ffffff / #f0f0f0 / #e0e0e0 等灰阶值"
            issues.append(error(path, msg) if strict else warn(path, msg))
        elif h not in RECOMMENDED_GRAYS:
            issues.append(warn(path, f"发现非推荐灰阶 {raw}；建议优先使用 #ffffff / #f0f0f0 / #e0e0e0 / #000000"))

    for m in RGB_RE.finditer(text):
        args = _split_function_args(m.group(1))
        if len(args) < 3:
            continue
        channels = [_parse_rgb_piece(x) for x in args[:3]]
        alpha = _parse_rgb_piece(args[3]) if len(args) >= 4 else 1
        if any(c is None for c in channels):
            issues.append(warn(path, f"无法静态判断颜色函数 {m.group(0)}；建议改为明确灰阶 HEX"))
            continue
        r, g, b = channels  # type: ignore[misc]
        is_gray = math.isclose(r, g, abs_tol=0.5) and math.isclose(g, b, abs_tol=0.5)
        if not is_gray:
            msg = f"发现彩色 RGB/RGBA {m.group(0)}；报告图只允许灰阶"
            issues.append(error(path, msg) if strict else warn(path, msg))
        if alpha is not None and not math.isclose(alpha, 1.0, abs_tol=0.001):
            msg = f"发现透明颜色 {m.group(0)}；严格黑白报告图不使用半透明"
            issues.append(error(path, msg) if strict else warn(path, msg))

    for m in HSL_RE.finditer(text):
        raw = m.group(0)
        args = _split_function_args(m.group(1))
        alpha = _parse_rgb_piece(args[3]) if len(args) >= 4 else 1
        # HSL is hard to resolve safely; saturation 0% is grayscale.
        saturation = args[1].strip() if len(args) >= 2 else ""
        if saturation not in {"0", "0%", "0.0", "0.0%"}:
            msg = f"发现 HSL/HSLA 颜色 {raw}；建议改为明确灰阶 HEX"
            issues.append(error(path, msg) if strict else warn(path, msg))
        if alpha is not None and not math.isclose(alpha, 1.0, abs_tol=0.001):
            msg = f"发现透明 HSL/HSLA {raw}；严格黑白报告图不使用半透明"
            issues.append(error(path, msg) if strict else warn(path, msg))

    for m in NAMED_COLOR_PROP_RE.finditer(text):
        name = m.group(1)
        lname = name.lower()
        if lname in DISALLOWED_COLOR_NAMES:
            msg = f"发现命名彩色 {name}；请改用灰阶 HEX"
            issues.append(error(path, msg) if strict else warn(path, msg))
        elif lname not in ALLOWED_NAMED_GRAYS and lname not in {"none"}:
            issues.append(warn(path, f"发现未解析命名颜色 {name}；建议改为明确灰阶 HEX"))

    for m in CSS_VAR_COLOR_RE.finditer(text):
        msg = f"发现动态颜色 {m.group(1)}；静态校验无法保证黑白打印效果，建议改为明确灰阶 HEX"
        issues.append(error(path, msg) if strict else warn(path, msg))

    for m in OPACITY_RE.finditer(text):
        try:
            value = float(m.group(1))
        except ValueError:
            continue
        if value < 1:
            msg = f"发现透明度 {m.group(0)}；严格黑白报告图不使用半透明"
            issues.append(error(path, msg) if strict else warn(path, msg))

    return issues


def validate_mermaid(path: Path, strict: bool = True) -> List[Issue]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: List[Issue] = []
    head = text[:2000]
    if "%%{init:" not in head and "themeVariables" not in head:
        issues.append(warn(path, "缺少 Mermaid init/themeVariables；建议使用 mono 黑白主题头"))
    if "fontFamily" not in head:
        issues.append(warn(path, "缺少 fontFamily；建议声明 SimSun/Songti SC/Noto Serif CJK SC + Times New Roman"))
    if re.search(r"\bgraph\s+", text) and not re.search(r"\bflowchart\s+", text):
        issues.append(warn(path, "建议使用 flowchart 而不是 graph，排版控制更稳定"))
    if "sequenceDiagram" not in text and "stateDiagram" not in text:
        if not re.search(r"style\s+\w+\s+.*(?:fill|stroke|color):", text):
            issues.append(warn(path, "未发现节点 style；复杂图建议显式设置 fill/color/stroke"))
    for m in NODE_TEXT_RE.finditer(text):
        label = re.sub(r"<br\s*/?>", "", m.group(1))
        cn_count = len(re.findall(r"[\u4e00-\u9fff]", label))
        if cn_count >= 18 and "<br" not in m.group(1):
            issues.append(warn(path, f"节点文字较长且未手动换行：{label[:22]}...；建议每行不超过 10–14 个中文字"))
            break
    # Do not strip Mermaid comments: %%{init: ...}%% can contain real render colors.
    issues.extend(validate_color_tokens(path, text, strict))
    return issues


def validate_svg(path: Path, strict: bool = True) -> List[Issue]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: List[Issue] = []
    try:
        root = ET.fromstring(text)
        tag = root.tag.split("}")[-1]
        if tag.lower() != "svg":
            issues.append(error(path, "根元素不是 <svg>"))
        if not root.get("viewBox"):
            issues.append(warn(path, "缺少 viewBox；建议 width/height 与 viewBox 同步，便于缩放"))
        if not (root.get("width") and root.get("height")):
            issues.append(warn(path, "缺少固定 width/height；建议使用固定画布尺寸"))
    except ET.ParseError as exc:
        issues.append(error(path, f"SVG XML 解析失败：{exc}"))
        return issues

    lowered = text.lower()
    if "#ffffff" not in lowered and "#fff" not in lowered and "fill=\"white\"" not in lowered and "fill='white'" not in lowered:
        issues.append(warn(path, "未检测到白色背景；报告图建议显式添加 <rect ... fill=\"#ffffff\"/>"))
    if "font-family" not in text and "font_family" not in text:
        issues.append(warn(path, "缺少 font-family；建议声明 SimSun/Songti SC/Noto Serif CJK SC + Times New Roman"))
    elif not any(hint in text for hint in FONT_HINTS):
        issues.append(warn(path, "font-family 未包含中文/论文常用字体兜底"))

    for token in ("linearGradient", "radialGradient", "filter", "drop-shadow", "box-shadow", "text-shadow"):
        if token.lower() in lowered:
            msg = f"发现 {token}；严格黑白报告图不建议使用渐变、滤镜或阴影"
            issues.append(error(path, msg) if strict else warn(path, msg))

    issues.extend(validate_color_tokens(path, text, strict))
    return issues


def validate_file(path: Path, strict: bool = True) -> List[Issue]:
    suffix = path.suffix.lower()
    if suffix == ".mmd":
        return validate_mermaid(path, strict)
    if suffix == ".svg":
        return validate_svg(path, strict)
    return [error(path, f"不支持的文件类型：{suffix}")]


def discover(paths: Sequence[str], recursive: bool = False) -> List[Path]:
    found: List[Path] = []
    for item in paths:
        if any(ch in item for ch in "*?["):
            for p in glob.glob(item, recursive=recursive):
                pp = Path(p)
                if pp.is_file() and pp.suffix.lower() in SUPPORTED:
                    found.append(pp)
            continue
        p = Path(item)
        if p.is_file() and p.suffix.lower() in SUPPORTED:
            found.append(p)
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            for pp in p.glob(pattern):
                if pp.is_file() and pp.suffix.lower() in SUPPORTED:
                    found.append(pp)
        elif p.exists():
            print(f"[skip] unsupported: {p}", file=sys.stderr)
        else:
            print(f"[warn] path not found: {p}", file=sys.stderr)
    unique: List[Path] = []
    seen = set()
    for p in sorted(found, key=lambda x: str(x)):
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def out_for(src: Path, output_arg: Optional[str], out_dir: Optional[str], input_roots: Sequence[str]) -> Path:
    if out_dir:
        base = Path(out_dir)
        rel = src.name
        dir_roots = [Path(r) for r in input_roots if Path(r).is_dir()]
        if len(dir_roots) == 1:
            try:
                rel = str(src.relative_to(dir_roots[0])).replace(src.suffix, ".png")
                return base / rel
            except ValueError:
                pass
        return base / f"{src.stem}.png"
    if output_arg:
        out = Path(output_arg)
        if len(input_roots) == 1 and src.is_file() and out.suffix.lower() in {".png", ".svg", ".pdf"}:
            return out
        return out / f"{src.stem}.png"
    return src.with_suffix(".png")


def local_bin(name: str) -> Optional[str]:
    suffix = ".cmd" if os.name == "nt" else ""
    candidate = Path(__file__).resolve().parents[1] / "node_modules" / ".bin" / f"{name}{suffix}"
    if candidate.exists():
        return str(candidate)
    # On Windows, bare "npx" is not directly executable from Python's
    # subprocess (it lives as npx.cmd). Resolve it explicitly via shutil.which
    # so FileNotFoundError [WinError 2] is not raised. Try both bare and
    # .cmd/.exe suffixes to be safe across shells (Git Bash, PowerShell, cmd).
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        for ext in (".cmd", ".exe", ".bat"):
            found = shutil.which(f"{name}{ext}") or shutil.which(name, path=os.environ.get("PATH", ""))
            if found:
                return found
    return None


def _resolve_npx() -> Optional[str]:
    """Return a directly-executable path to npx, or None.

    On Windows the bare token "npx" is not executable from Python's subprocess
    (it is npx.cmd). We resolve it explicitly so we never emit the bare token
    that triggers FileNotFoundError [WinError 2].
    """
    return shutil.which("npx") or shutil.which("npx.cmd")


def command_for(src: Path, out: Path, scale: int, density: int, background: str, config_dir: Optional[Path]) -> List[str]:
    suffix = src.suffix.lower()
    if suffix == ".mmd":
        mmdc = local_bin("mmdc")
        if mmdc:
            cmd = [mmdc]
        else:
            npx = _resolve_npx()
            if npx:
                cmd = [npx, "--yes", MERMAID_CLI_PACKAGE]
            else:
                cmd = ["npx", "--yes", MERMAID_CLI_PACKAGE]
        cmd += ["-i", str(src), "-o", str(out), "-s", str(scale), "-b", background]
        if config_dir:
            puppeteer = config_dir / "puppeteer-config.json"
            css = config_dir / "mono.css"
            mermaid = config_dir / "mono-mermaid.json"
            if css.exists():
                cmd += ["--cssFile", str(css)]
            if mermaid.exists():
                cmd += ["-c", str(mermaid)]
            # puppeteer-config is optional and can cause launch failures on some
            # systems (e.g. sandbox flags that Chromium rejects). Only pass it
            # when it exists; if rendering still fails, retry without it in run().
            if puppeteer.exists():
                cmd += ["-p", str(puppeteer)]
        return cmd
    if suffix == ".svg":
        sharp = local_bin("sharp")
        if sharp:
            cmd = [sharp]
        else:
            npx = _resolve_npx()
            if npx:
                cmd = [npx, "--yes", SHARP_CLI_PACKAGE]
            else:
                cmd = ["npx", "--yes", SHARP_CLI_PACKAGE]
        return cmd + ["-i", str(src), "-o", str(out), "--density", str(density)]
    raise ValueError(f"unsupported suffix: {suffix}")


def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    # If the launcher (npx/mmdc/sharp) could not be resolved to an absolute
    # path, fall back to shell=True so the OS shell finds it on PATH. This is
    # the common case on Windows where the entry point is a .cmd shim.
    launcher = cmd[0] if cmd else ""
    needs_shell = launcher and not os.path.isabs(launcher) and not Path(launcher).exists()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=bool(needs_shell),
        )
        return proc.returncode, proc.stdout
    except FileNotFoundError as exc:
        return 127, str(exc)


def print_issues(issues: Iterable[Issue]) -> None:
    for i in issues:
        prefix = "ERROR" if i.level == "error" else "WARN"
        print(f"[{prefix}] {i.file}: {i.message}")


def render(args: argparse.Namespace) -> int:
    raw_paths = args.paths or ["."]
    output_arg: Optional[str] = None
    paths = raw_paths

    # Backward compatible with old render.sh: render.sh INPUT OUTPUT
    if args.out_dir is None and len(raw_paths) == 2 and Path(raw_paths[0]).exists() and Path(raw_paths[1]).suffix.lower() not in SUPPORTED:
        paths = [raw_paths[0]]
        output_arg = raw_paths[1]

    inputs = discover(paths, recursive=args.recursive)
    if not inputs:
        print("No .mmd or .svg files found.", file=sys.stderr)
        return 2

    config_dir = Path(args.config_dir) if args.config_dir else CONFIG_DIR
    results: List[Result] = []
    fatal = 0
    need_npx = any(not local_bin("mmdc") if p.suffix.lower() == ".mmd" else not local_bin("sharp") for p in inputs)
    if need_npx and not shutil.which("npx") and not args.check_only and not args.dry_run:
        print("[error] neither local renderer nor npx found. Run npm install or install Node.js.", file=sys.stderr)
        return 127

    for src in inputs:
        kind = src.suffix.lower().lstrip(".")
        issues = validate_file(src, args.strict)
        has_error = any(i.level == "error" for i in issues)
        out = out_for(src, output_arg, args.out_dir, paths)
        cmd = command_for(src, out, args.scale, args.density, args.background, config_dir)
        if issues:
            print_issues(issues)
        if has_error and args.strict and not args.allow_lint_errors:
            results.append(Result(str(src), str(out), kind, "lint_failed", issues, cmd))
            fatal = 1
            if args.fail_fast:
                break
            continue
        if args.check_only:
            status = "ok" if not has_error else "lint_failed"
            results.append(Result(str(src), None, kind, status, issues, None))
            fatal = max(fatal, 1 if status != "ok" else 0)
            continue
        if args.dry_run:
            print("[dry-run] " + " ".join(cmd))
            results.append(Result(str(src), str(out), kind, "dry_run", issues, cmd))
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"[render] {src} -> {out}")
        code, output = run(cmd)
        if code == 0 and out.exists():
            print(f"[ok] {out} sha256={sha256(out)}")
            results.append(Result(str(src), str(out), kind, "ok", issues, cmd))
        else:
            tail = output[-2000:] if output.strip() else "No stderr/stdout returned. Check npm install, network access, or CLI compatibility."
            print(f"[fail] {src}\ncommand: {' '.join(cmd)}\n{tail}", file=sys.stderr)
            results.append(Result(str(src), str(out), kind, "render_failed", issues, cmd, output[-4000:]))
            fatal = 1
            if args.fail_fast:
                break

    # v1.2.0: dry-run does not write manifest unless explicitly requested via --dry-run-manifest.
    write_manifest = args.manifest and (not args.check_only) and ((not args.dry_run) or args.dry_run_manifest)
    if write_manifest:
        manifest_dir = Path(args.manifest_dir or args.out_dir or output_arg or ".")
        if manifest_dir.suffix:
            manifest_dir = manifest_dir.parent
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = manifest_dir / "mono-render-manifest.json"
        payload = {
            "version": VERSION,
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "count": len(results),
            "strict": args.strict,
            "scale": args.scale,
            "density": args.density,
            "dry_run": args.dry_run,
            "results": [asdict(r) for r in results],
        }
        manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[manifest] {manifest}")
    ok_count = sum(1 for r in results if r.status in {"ok", "dry_run"})
    issue_count = sum(len(r.issues) for r in results)
    if args.check_only:
        checked = sum(1 for r in results if r.status == "ok")
        print(f"Summary: {checked}/{len(results)} checked; {issue_count} lint issues.")
    else:
        print(f"Summary: {ok_count}/{len(results)} rendered/planned; {issue_count} lint issues.")
    return fatal


def validate(args: argparse.Namespace) -> int:
    args.check_only = True
    args.dry_run = False
    args.manifest = False
    args.dry_run_manifest = False
    return render(args)


def template_map() -> Dict[str, Path]:
    result: Dict[str, Path] = {}
    if TEMPLATE_DIR.exists():
        for p in sorted(TEMPLATE_DIR.iterdir()):
            if p.is_file() and p.suffix.lower() in SUPPORTED:
                result[p.stem] = p
    return result


def list_templates(args: argparse.Namespace) -> int:
    templates = template_map()
    if not templates:
        print("No templates found.", file=sys.stderr)
        return 2
    print("Available templates:")
    for name, path in templates.items():
        print(f"  {name:<20} {path.relative_to(Path(__file__).resolve().parents[1])}")
    return 0


def new_from_template(args: argparse.Namespace) -> int:
    templates = template_map()
    key = args.template
    if key not in templates:
        print(f"Unknown template: {key}", file=sys.stderr)
        print("Run: python scripts/mono_diagram.py list-templates", file=sys.stderr)
        return 2
    src = templates[key]
    dest = Path(args.output)
    if dest.exists() and not args.force:
        print(f"Refuse to overwrite existing file: {dest}. Use --force to overwrite.", file=sys.stderr)
        return 1
    if dest.suffix == "":
        dest = dest.with_suffix(src.suffix)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[new] {key} -> {dest}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate, scaffold, and render mono academic diagrams (.mmd/.svg).")
    p.add_argument("--version", action="version", version=f"mono-diagram {VERSION}")
    sub = p.add_subparsers(dest="cmd")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("paths", nargs="*", help="Input file(s), directory, or glob. Old style: INPUT OUTPUT is supported.")
    common.add_argument("-o", "--out-dir", help="Output directory. If omitted, writes next to source file.")
    common.add_argument("-r", "--recursive", action="store_true", help="Search input directories recursively.")
    common.add_argument("--strict", dest="strict", action="store_true", default=True, help="Treat non-mono colors/effects as errors. Default.")
    common.add_argument("--no-strict", dest="strict", action="store_false", help="Downgrade style violations to warnings.")
    common.add_argument("--allow-lint-errors", action="store_true", help="Render even if strict lint errors exist.")
    common.add_argument("--fail-fast", action="store_true", help="Stop on first lint/render failure.")
    common.add_argument("--scale", type=int, default=3, help="Mermaid render scale. Default: 3.")
    common.add_argument("--density", type=int, default=300, help="SVG render density. Default: 300.")
    common.add_argument("--background", default="white", help="Mermaid background. Default: white.")
    common.add_argument("--config-dir", help="Directory containing mono-mermaid.json / mono.css / puppeteer-config.json.")
    common.add_argument("--dry-run", action="store_true", help="Print render commands without running them.")
    common.add_argument("--check-only", action="store_true", help="Lint only, do not render.")
    common.add_argument("--manifest", action="store_true", default=True, help="Write mono-render-manifest.json after real rendering. Default: true.")
    common.add_argument("--no-manifest", dest="manifest", action="store_false", help="Do not write manifest.")
    common.add_argument("--dry-run-manifest", action="store_true", help="Also write manifest during --dry-run. Off by default.")
    common.add_argument("--manifest-dir", help="Directory for manifest file.")

    sub.add_parser("render", parents=[common], help="Lint and render diagrams.")
    sub.add_parser("validate", parents=[common], help="Lint diagrams only.")
    sub.add_parser("list-templates", help="List bundled templates.")
    new_p = sub.add_parser("new", help="Create a new diagram from a bundled template.")
    new_p.add_argument("template", help="Template key, e.g. architecture, process, research-framework.")
    new_p.add_argument("output", help="Output source file path. Extension is optional.")
    new_p.add_argument("--force", action="store_true", help="Overwrite output if it already exists.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] not in {"render", "validate", "new", "list-templates", "-h", "--help", "--version"}:
        argv = ["render"] + argv
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0
    if args.cmd == "validate":
        return validate(args)
    if args.cmd == "list-templates":
        return list_templates(args)
    if args.cmd == "new":
        return new_from_template(args)
    return render(args)


if __name__ == "__main__":
    raise SystemExit(main())
