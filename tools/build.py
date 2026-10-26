#!/usr/bin/env python3
"""Render index.html from content.json + templates/index.template.html.

No third-party dependencies. Run:

    python tools/build.py          # build once
    python tools/build.py --check  # validate content.json, write nothing
"""

from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "index.template.html"
CONTENT = ROOT / "content.json"
OUTPUT = ROOT / "index.html"


# --------------------------------------------------------------------------
# text helpers
# --------------------------------------------------------------------------
def esc(value) -> str:
    """HTML-escape a value for use in text or a quoted attribute."""
    return html.escape("" if value is None else str(value), quote=True)


def rich(value) -> str:
    """Escape, then apply a tiny inline markup:

        **bold**            -> <strong>
        *italic*            -> <em>
        [text](https://...) -> <a target="_blank">

    Everything else stays literal, so content.json can never inject markup
    that the renderer did not explicitly allow.
    """
    text = esc(value)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text, flags=re.S)
    return text


def paragraphs(value) -> str:
    """A list of strings -> <p> blocks."""
    return "\n".join("            <p>%s</p>" % rich(p) for p in value if str(p).strip())


def asset_version() -> str:
    """Small cache-buster so a replaced portrait shows up immediately."""
    portrait = ROOT / "assets" / "img" / "portrait.jpg"
    try:
        return str(int(portrait.stat().st_mtime))
    except OSError:
        return "0"


ICONS = {
    "wave": '<path d="M3 12h3l2.2-6.5L12 18l2.4-8.5 1.6 4.5H21"/>',
    "graph": (
        '<circle cx="6" cy="6" r="2.4"/><circle cx="18" cy="6" r="2.4"/>'
        '<circle cx="12" cy="18" r="2.4"/>'
        '<path d="M8.1 7.3 10.9 16M15.9 7.3 13.1 16M8.4 6h7.2"/>'
    ),
    "transfer": (
        '<path d="M4 7h7M4 12h5M4 17h7"/><path d="M14 5.5v6M14 8.5h5.5V11"/>'
        '<circle cx="19.5" cy="17" r="2.5"/>'
    ),
    "mesh": (
        '<circle cx="5" cy="6" r="1.8"/><circle cx="12" cy="4.5" r="1.8"/>'
        '<circle cx="19" cy="6" r="1.8"/><circle cx="5" cy="18" r="1.8"/>'
        '<circle cx="12" cy="19.5" r="1.8"/><circle cx="19" cy="18" r="1.8"/>'
        '<path d="M5 6v12M12 4.5v15M19 6v12M5 6l14 12M19 6 5 18"/>'
    ),
    "book": (
        '<path d="M6.5 3.5h6.8L18 8.2V20a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 20V4a.5.5 0 0 1 .5-.5Z"/>'
        '<path d="M13.2 3.6v4.7h4.6"/><path d="M9 12.4h6M9 15.9h4.2"/>'
    ),
    "chip": '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M10 3v3.5M14 3v3.5M10 17.5V21M14 17.5V21M3 10h3.5M3 14h3.5M17.5 10H21M17.5 14H21"/>',
}

ICON_KEYS = list(ICONS.keys())


# --------------------------------------------------------------------------
# fragments
# --------------------------------------------------------------------------
def render_hero(c: dict) -> str:
    site = c["site"]
    hero = c["hero"]

    stats = "\n".join(
        '            <div class="stat">\n'
        '              <dt>%s</dt>\n'
        '              <dd><span class="count" data-count="%s">%s</span></dd>\n'
        "            </div>" % (esc(s["label"]), esc(s["value"]), esc(s["value"]))
        for s in hero.get("stats", [])
    )

    return """    <!-- ============ HERO ============ -->
    <section class="hero" aria-labelledby="hero-title">
      <div class="wrap hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">
            <span class="dot" aria-hidden="true"></span>
            <span class="eyebrow-text">{eyebrow}</span>
          </p>

          <h1 id="hero-title">
            {name}
            <span class="cjk">{name_cjk}</span>
          </h1>

          <p class="lede">
            {lede}
          </p>

          <div class="hero-actions">
            <a class="btn btn-primary" href="#publications">
              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h6.8L18 8.2V20a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 20V4a.5.5 0 0 1 .5-.5Z"/><path d="M13.2 3.6v4.7h4.6"/><path d="M9 12.4h6M9 15.9h4.2"/></svg>
              Publications
            </a>
            <a class="btn" href="{scholar}" target="_blank" rel="noopener">
              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 1.8 9.1 12 15.2l10.2-6.1L12 3Z"/><path d="M5.4 11.5v4.9c0 2 3 3.6 6.6 3.6s6.6-1.6 6.6-3.6v-4.9"/></svg>
              Google Scholar
            </a>
            <a class="btn btn-ghost" href="mailto:{email}">
              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="2.8" y="5" width="18.4" height="14" rx="2.4"/><path d="m3.4 6.6 8.6 6.2 8.6-6.2"/></svg>
              Email
            </a>
          </div>

          <dl class="stats" aria-label="Research metrics, from Google Scholar">
{stats}
          </dl>
        </div>

        <div class="hero-figure">
          <div class="portrait-ring">
            <div class="portrait-card">
              <img src="assets/img/portrait.jpg?v={asset_v}" alt="Portrait of {name}" width="512" height="512" fetchpriority="high">
            </div>
          </div>
          <p class="portrait-chip">
            <span class="pulse" aria-hidden="true"></span>
            {location}
          </p>
        </div>
      </div>

      <div class="hero-glow" aria-hidden="true"></div>
    </section>""".format(
        eyebrow=esc(hero.get("eyebrow", "")),
        name=esc(site["name"]),
        name_cjk=esc(site.get("name_cjk", "")),
        lede=rich(hero.get("lede", "")),
        scholar=esc(site.get("scholar", "")),
        email=esc(site.get("email", "")),
        location=esc(hero.get("location", "")),
        stats=stats,
        asset_v=asset_version(),
    )


def render_about(c: dict) -> str:
    about = c["about"]
    rows = "\n".join(
        "              <div><dt>%s</dt><dd>%s</dd></div>" % (esc(g["key"]), rich(g["value"]))
        for g in about.get("glance", [])
    )
    link = about.get("glance_link") or {}
    link_html = ""
    if link.get("label"):
        link_html = (
            '            <a class="glance-link" href="%s" target="_blank" rel="noopener">\n'
            "              %s\n"
            '              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 18 18 6M9 6h9v9"/></svg>\n'
            "            </a>"
        ) % (esc(link.get("href", "#")), esc(link["label"]))

    return """    <!-- ============ ABOUT ============ -->
    <section class="section" id="about" aria-labelledby="about-title">
      <div class="wrap">
        <header class="section-head">
          <p class="section-kicker">{kicker}</p>
          <h2 id="about-title">{heading}</h2>
        </header>

        <div class="about-grid">
          <div class="about-text">
{paragraphs}
          </div>

          <aside class="glance" aria-label="At a glance">
            <h3>At a glance</h3>
            <dl>
{rows}
            </dl>
{link}
          </aside>
        </div>
      </div>
    </section>""".format(
        kicker=esc(about.get("kicker", "01 — About")),
        heading=esc(about.get("heading", "A little context")),
        paragraphs=paragraphs(about.get("paragraphs", [])),
        rows=rows,
        link=link_html,
    )


def render_research(c: dict) -> str:
    r = c["research"]
    cards = []
    for item in r.get("items", []):
        icon = ICONS.get(item.get("icon", "wave"), ICONS["wave"])
        tags = "".join("<li>%s</li>" % esc(t) for t in item.get("tags", []))
        tags_html = '\n            <ul class="card-tags">%s</ul>' % tags if tags else ""
        cls = "card feature" if item.get("feature", True) else "card"
        cards.append(
            '          <article class="%s" data-reveal>\n'
            '            <span class="card-icon" aria-hidden="true">\n'
            '              <svg viewBox="0 0 24 24">%s</svg>\n'
            "            </span>\n"
            "            <h3>%s</h3>\n"
            "            <p>\n              %s\n            </p>%s\n"
            "          </article>"
            % (cls, icon, esc(item["title"]), rich(item.get("text", "")), tags_html)
        )

    return """    <!-- ============ RESEARCH ============ -->
    <section class="section section-alt" id="research" aria-labelledby="research-title">
      <div class="wrap">
        <header class="section-head">
          <p class="section-kicker">{kicker}</p>
          <h2 id="research-title">{heading}</h2>
          <p class="section-sub">
            {sub}
          </p>
        </header>

        <div class="card-grid">
{cards}
        </div>
      </div>
    </section>""".format(
        kicker=esc(r.get("kicker", "")),
        heading=esc(r.get("heading", "")),
        sub=rich(r.get("sub", "")),
        cards="\n\n".join(cards),
    )


def render_news(c: dict) -> str:
    n = c["news"]
    items = "\n".join(
        '          <li data-reveal>\n'
        '            <span class="when">%s</span>\n'
        '            <div class="what">\n'
        "              <p>%s</p>\n"
        "            </div>\n"
        "          </li>" % (esc(i["when"]), rich(i.get("text", "")))
        for i in n.get("items", [])
    )
    return """    <!-- ============ NEWS ============ -->
    <section class="section" id="news" aria-labelledby="news-title">
      <div class="wrap">
        <header class="section-head">
          <p class="section-kicker">{kicker}</p>
          <h2 id="news-title">{heading}</h2>
        </header>

        <ol class="timeline">
{items}
        </ol>
      </div>
    </section>""".format(
        kicker=esc(n.get("kicker", "")),
        heading=esc(n.get("heading", "")),
        items=items,
    )


def render_publications(c: dict) -> str:
    p = c["publications"]
    items = p.get("items", [])
    total = len(items)
    by_type = {"journal": 0, "conference": 0}
    for i in items:
        key = i.get("type", "journal")
        by_type[key] = by_type.get(key, 0) + 1

    cards = []
    for item in items:
        kind = item.get("type", "journal")
        title = esc(item["title"])
        href = item.get("href") or ""
        if href:
            title_html = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(href), title)
        else:
            title_html = title

        meta = ['<span class="venue">%s</span>' % esc(item.get("venue", ""))]
        if item.get("year"):
            meta.append('<span class="sep">·</span><span class="year">%s</span>' % esc(item["year"]))
        if item.get("cited"):
            meta.append('<span class="sep">·</span><span class="cited">Cited by %s</span>' % esc(item["cited"]))

        links = "".join(
            '<a href="%s"%s>%s</a>'
            % (esc(l["href"]), ' target="_blank" rel="noopener"' if l["href"].startswith("http") else "", esc(l["label"]))
            for l in item.get("links", [])
            if l.get("href")
        )
        links_html = '\n              <div class="pub-links">%s</div>' % links if links else ""

        cards.append(
            '          <li class="pub" data-type="%s" data-reveal>\n'
            '            <div class="pub-badge" data-kind="%s">%s</div>\n'
            '            <div class="pub-body">\n'
            '              <h3 class="pub-title">\n'
            "                %s\n"
            "              </h3>\n"
            '              <p class="pub-authors">%s</p>\n'
            '              <p class="pub-meta">%s</p>%s\n'
            "            </div>\n"
            "          </li>"
            % (esc(kind), esc(kind), esc(item.get("badge", "")), title_html,
               rich(item.get("authors", "")), "\n                ".join(meta), links_html)
        )

    sub = rich(p.get("sub", ""))
    if p.get("scholar") and p.get("scholar_text"):
        sub = sub.replace(
            esc(p["scholar_text"]),
            '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(p["scholar"]), esc(p["scholar_text"])),
            1,
        )
    note = esc(p.get("note", ""))

    return """    <!-- ============ PUBLICATIONS ============ -->
    <section class="section section-alt" id="publications" aria-labelledby="pub-title">
      <div class="wrap">
        <header class="section-head">
          <div class="head-row">
            <div>
              <p class="section-kicker">{kicker}</p>
              <h2 id="pub-title">{heading}</h2>
              <p class="section-sub">{sub}<span class="self-note">{note}</span></p>
            </div>
            <div class="chips" id="pubFilter" role="group" aria-label="Filter publications by type">
              <button class="chip is-active" type="button" data-filter="all" aria-pressed="true">All <span>{total}</span></button>
              <button class="chip" type="button" data-filter="journal" aria-pressed="false">Journal <span>{journals}</span></button>
              <button class="chip" type="button" data-filter="conference" aria-pressed="false">Conference <span>{confs}</span></button>
            </div>
          </div>
        </header>

        <ol class="pub-list" id="pubList">
{cards}
        </ol>

        <p class="empty-state" id="pubEmpty" hidden>Nothing in this category yet.</p>
      </div>
    </section>""".format(
        kicker=esc(p.get("kicker", "")),
        heading=esc(p.get("heading", "")),
        sub=sub,
        note=note,
        total=total,
        journals=by_type.get("journal", 0),
        confs=by_type.get("conference", 0),
        cards="\n\n".join(cards),
    )


def render_code(c: dict) -> str:
    code = c["code"]
    cards = []
    for r in code.get("items", []):
        stars = ""
        if r.get("stars") not in (None, ""):
            stars = ('\n              <span class="stars"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'
                     '<path d="m12 3.6 2.6 5.4 5.9.8-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9L3.5 9.8l5.9-.8Z"/></svg>%s</span>'
                     % esc(r["stars"]))
        cards.append(
            '          <a class="repo" href="%s" target="_blank" rel="noopener" data-reveal>\n'
            '            <div class="repo-top">\n'
            "              <h3>%s</h3>%s\n"
            "            </div>\n"
            "            <p>%s</p>\n"
            '            <span class="repo-lang"><i style="--c:%s"></i>%s</span>\n'
            "          </a>"
            % (esc(r.get("href", "#")), esc(r.get("name", "")), stars,
               rich(r.get("desc", "")), esc(r.get("color", "#3572A5")), esc(r.get("lang", "Python")))
        )

    return """    <!-- ============ CODE ============ -->
    <section class="section" id="code" aria-labelledby="code-title">
      <div class="wrap">
        <header class="section-head">
          <p class="section-kicker">{kicker}</p>
          <h2 id="code-title">{heading}</h2>
          <p class="section-sub">
            {sub}
          </p>
        </header>

        <div class="repo-grid">
{cards}
        </div>
      </div>
    </section>""".format(
        kicker=esc(code.get("kicker", "")),
        heading=esc(code.get("heading", "")),
        sub=rich(code.get("sub", "")),
        cards="\n\n".join(cards),
    )


def render_contact(c: dict) -> str:
    ct = c["contact"]
    site = c["site"]
    email = site.get("email", "")
    links = "\n".join(
        '            <a href="%s" target="_blank" rel="noopener">\n'
        '              <span class="cl-name">%s</span>\n'
        '              <span class="cl-handle">%s</span>\n'
        "            </a>" % (esc(l.get("href", "#")), esc(l.get("name", "")), esc(l.get("handle", "")))
        for l in ct.get("links", [])
    )
    return """    <!-- ============ CONTACT ============ -->
    <section class="section section-alt" id="contact" aria-labelledby="contact-title">
      <div class="wrap">
        <header class="section-head">
          <p class="section-kicker">{kicker}</p>
          <h2 id="contact-title">{heading}</h2>
          <p class="section-sub">
            {sub}
          </p>
        </header>

        <div class="contact-card" data-reveal>
          <div class="contact-main">
            <span class="contact-label">Email</span>
            <a class="contact-mail" id="mailLink" href="mailto:{email}">{email}</a>
            <button class="btn btn-ghost copy-btn" id="copyEmail" type="button" data-email="{email}">
              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M15 5.5A1.5 1.5 0 0 0 13.5 4H5.5A1.5 1.5 0 0 0 4 5.5v8A1.5 1.5 0 0 0 5.5 15"/></svg>
              <span class="copy-label">Copy</span>
            </button>
          </div>

          <div class="contact-links">
{links}
          </div>
        </div>
      </div>
    </section>""".format(
        kicker=esc(ct.get("kicker", "")),
        heading=esc(ct.get("heading", "")),
        sub=rich(ct.get("sub", "")),
        email=esc(email),
        links=links,
    )


def render_jsonld(c: dict) -> str:
    site = c["site"]
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": site["name"],
        "alternateName": site.get("name_cjk", ""),
        "url": site.get("url", ""),
        "image": site.get("url", "").rstrip("/") + "/assets/img/portrait.jpg",
        "jobTitle": c["hero"].get("eyebrow", "").split("·")[0].strip() or "M.S. Student",
        "affiliation": {
            "@type": "CollegeOrUniversity",
            "name": site.get("university", "Southeast University"),
            "department": site.get("department", ""),
        },
        "knowsAbout": [i["title"] for i in c["research"].get("items", [])],
        "sameAs": [site.get("scholar", ""), site.get("github", "")],
    }
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return text.replace("</", "<\\/")


# --------------------------------------------------------------------------
# entry points
# --------------------------------------------------------------------------
def render(content: dict) -> str:
    if not TEMPLATE.exists():
        raise FileNotFoundError("missing template: %s" % TEMPLATE)
    out = TEMPLATE.read_text(encoding="utf-8")

    site = content["site"]
    year = datetime.now().year
    replacements = {
        "TITLE": esc(site.get("title", site["name"])),
        "DESCRIPTION": esc(site.get("description", "")),
        "URL": esc(site.get("url", "")),
        "OG_IMAGE": esc(site.get("url", "").rstrip("/") + "/assets/img/portrait.jpg"),
        "NAME": esc(site["name"]),
        "NAME_CJK": esc(site.get("name_cjk", "")),
        "JSONLD": render_jsonld(content),
        "YEAR": str(year),
        "ASSET_V": asset_version(),
        "HERO": render_hero(content),
        "ABOUT": render_about(content),
        "RESEARCH": render_research(content),
        "NEWS": render_news(content),
        "PUBLICATIONS": render_publications(content),
        "CODE": render_code(content),
        "CONTACT": render_contact(content),
    }
    for key, value in replacements.items():
        out = out.replace("<!--#%s#-->" % key, value)

    leftover = re.findall(r"<!--#([A-Z_]+)#-->", out)
    if leftover:
        raise ValueError("unfilled placeholders: %s" % ", ".join(sorted(set(leftover))))
    return out


def load_content(path: Path = CONTENT) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    for section in ("site", "hero", "about", "research", "news", "publications", "code", "contact"):
        if section not in data:
            raise ValueError("content.json is missing the '%s' section" % section)
    return data


def build(write: bool = True) -> str:
    content = load_content()
    out = render(content)
    if write:
        OUTPUT.write_text(out, encoding="utf-8", newline="\n")
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--check" in argv:
        html_text = build(write=False)
        print("content.json ok, %d bytes of html would be written" % len(html_text))
        return 0
    out = build(write=True)
    print("wrote %s (%d bytes)" % (OUTPUT, len(out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
