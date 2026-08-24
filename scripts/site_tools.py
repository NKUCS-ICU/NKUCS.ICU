#!/usr/bin/env python3
"""Synchronize and validate the Docsify content tree.

The root ``_sidebar.md`` is the canonical navigation and course catalog.
Course README files are generated from it; CI uses the same parser to prevent
navigation, files, and generated lists from drifting apart.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SIDEBAR = ROOT / "_sidebar.md"

LINK_LINE_RE = re.compile(
    r"^(?P<indent>\s*)-\s+\[(?P<label>[^]]+)]\((?P<route>/[^)]+)\)\s*$"
)
MARKDOWN_TARGET_RE = re.compile(
    r"!?\[[^]]*]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)"
)
HTML_TARGET_RE = re.compile(r"(?:href|src)=['\"](?P<target>[^'\"]+)['\"]")
COURSE_GROUP_RE = re.compile(
    r"^/(?:courses|courses_law)/grade-[1-4]/$|^/courses_maphd/1/$"
)
GENERATED_START = "<!-- course-list:start -->"
GENERATED_END = "<!-- course-list:end -->"


@dataclass(frozen=True)
class CourseEntry:
    label: str
    route: str

    @property
    def course_id(self) -> str:
        return self.label.split(maxsplit=1)[0]


def parse_course_groups() -> dict[str, list[CourseEntry]]:
    groups: dict[str, list[CourseEntry]] = {}
    current_route: str | None = None
    current_indent = -1

    for line in SIDEBAR.read_text(encoding="utf-8").splitlines():
        match = LINK_LINE_RE.match(line)
        if not match:
            continue

        indent = len(match.group("indent"))
        route = match.group("route")
        label = match.group("label")

        if COURSE_GROUP_RE.fullmatch(route):
            current_route = route
            current_indent = indent
            groups.setdefault(route, [])
            continue

        if current_route is not None and indent <= current_indent:
            current_route = None

        if current_route is not None and route.startswith(current_route):
            groups[current_route].append(CourseEntry(label=label, route=route))

    return groups


def expected_readme(entries: list[CourseEntry]) -> str:
    return "".join(f"- [{entry.label}]({entry.route})\n" for entry in entries)


def render_readme(existing: str, route: str, entries: list[CourseEntry]) -> str:
    generated = f"{GENERATED_START}\n{expected_readme(entries)}{GENERATED_END}\n"
    if GENERATED_START in existing and GENERATED_END in existing:
        before, remainder = existing.split(GENERATED_START, maxsplit=1)
        _, after = remainder.split(GENERATED_END, maxsplit=1)
        prefix = f"{before.rstrip()}\n\n" if before.strip() else ""
        suffix = f"\n{after.lstrip()}" if after.strip() else ""
        return f"{prefix}{generated}{suffix}"

    lines = existing.splitlines(keepends=True)
    first_course = len(lines)
    for index, line in enumerate(lines):
        match = LINK_LINE_RE.match(line.rstrip("\r\n"))
        if match and match.group("route").startswith(route):
            first_course = index
            break
    preamble = "".join(lines[:first_course]).rstrip()
    return f"{preamble}\n\n{generated}" if preamble else generated


def route_path(route: str) -> Path:
    return ROOT / unquote(urlsplit(route).path).lstrip("/")


def sync_readmes() -> None:
    for route, entries in parse_course_groups().items():
        readme = route_path(route) / "README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        existing = readme.read_text(encoding="utf-8") if readme.exists() else ""
        readme.write_text(render_readme(existing, route, entries), encoding="utf-8")
        print(f"synced {readme.relative_to(ROOT)} ({len(entries)} courses)")


def resolve_local_target(source: Path, target: str) -> bool:
    if not target or target.startswith(("#", "mailto:", "tel:", "javascript:")):
        return True

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return True

    decoded = unquote(parsed.path)
    if not decoded:
        return True

    base = ROOT / decoded.lstrip("/") if decoded.startswith("/") else source.parent / decoded
    candidates = (base, Path(f"{base}.md"), base / "README.md")
    return any(candidate.exists() for candidate in candidates)


def validate() -> list[str]:
    errors: list[str] = []
    groups = parse_course_groups()

    if not groups:
        errors.append("_sidebar.md: no course groups found")

    for route, entries in groups.items():
        readme = route_path(route) / "README.md"
        expected = expected_readme(entries)
        if not readme.exists():
            errors.append(f"{readme.relative_to(ROOT)}: generated README is missing")
        else:
            readme_text = readme.read_text(encoding="utf-8")
            if GENERATED_START not in readme_text or GENERATED_END not in readme_text:
                errors.append(
                    f"{readme.relative_to(ROOT)}: generated course-list markers are missing; "
                    "run python scripts/site_tools.py sync"
                )
            else:
                generated = readme_text.split(GENERATED_START, maxsplit=1)[1]
                generated = generated.split(GENERATED_END, maxsplit=1)[0].strip("\r\n")
                actual = f"{generated}\n" if generated else ""
                if actual != expected:
                    errors.append(
                        f"{readme.relative_to(ROOT)}: out of sync; run "
                        "python scripts/site_tools.py sync"
                    )

        seen_routes: set[str] = set()
        referenced_pages: set[Path] = set()
        for entry in entries:
            if entry.route in seen_routes:
                errors.append(f"_sidebar.md: duplicate route {entry.route}")
            seen_routes.add(entry.route)
            referenced_pages.add(Path(f"{route_path(entry.route)}.md"))
            if not resolve_local_target(SIDEBAR, entry.route):
                errors.append(f"_sidebar.md: missing course page {entry.route}")

        for page in route_path(route).glob("*.md"):
            if page.name != "README.md" and page not in referenced_pages:
                errors.append(
                    f"{page.relative_to(ROOT)}: course page is not linked from _sidebar.md"
                )

    content_files = sorted(ROOT.rglob("*.md")) + [ROOT / "index.html"]
    for source in content_files:
        text = source.read_text(encoding="utf-8")
        patterns = (
            [MARKDOWN_TARGET_RE, HTML_TARGET_RE]
            if source.suffix == ".md"
            else [HTML_TARGET_RE]
        )
        for pattern in patterns:
            for match in pattern.finditer(text):
                target = match.group("target").strip("<>")
                if "\\" in target:
                    line = text.count("\n", 0, match.start()) + 1
                    errors.append(
                        f"{source.relative_to(ROOT)}:{line}: local links must use /, not \\: "
                        f"{target}"
                    )
                    continue
                if not resolve_local_target(source, target):
                    line = text.count("\n", 0, match.start()) + 1
                    errors.append(
                        f"{source.relative_to(ROOT)}:{line}: missing local target {target}"
                    )

    index_text = (ROOT / "index.html").read_text(encoding="utf-8")
    if re.search(r"clientSecret\s*:", index_text, flags=re.IGNORECASE):
        errors.append("index.html: OAuth client secrets must not be shipped to browsers")
    if "owner: 'emanual20'" in index_text or 'owner: "emanual20"' in index_text:
        errors.append("index.html: legacy repository owner is still configured")

    return errors


def create_missing_pages() -> None:
    template = (
        "# {label}\n\n"
        "本课程页面暂无内容，期待大家的共同建设\\~🔥\n\n"
        "如果你愿意提供任何信息与观点，请在下方评论区留言，"
        "网站维护者会及时查看并酌情补充到课程页面中。\n"
    )
    created = 0
    for entries in parse_course_groups().values():
        for entry in entries:
            page = Path(f"{route_path(entry.route)}.md")
            if page.exists():
                continue
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(template.format(label=entry.label), encoding="utf-8")
            print(f"created {page.relative_to(ROOT)}")
            created += 1
    print(f"created {created} course page(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "sync", "init"))
    args = parser.parse_args()

    if args.command == "sync":
        sync_readmes()
        return 0
    if args.command == "init":
        create_missing_pages()
        return 0

    errors = validate()
    if errors:
        print("site validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("site validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
