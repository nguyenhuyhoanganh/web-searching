# web-research — web search & read Agent Skill (no MCP)

A skill that lets Claude/Cline **search the web** and **read web pages** without MCP — useful when a
forked Cline build blocks MCP and ships no web tools. The agent calls two Python scripts through the
terminal (`execute_command`), and `SKILL.md` teaches the agent to **search precisely, not blindly**.

This skill follows Anthropic's **Agent Skills** standard (a directory with `SKILL.md` + frontmatter +
progressive disclosure). Can you use MCP? See branch `claude/cline-search-web-skills-yc36cf` (the MCP server).

## Structure (Agent Skill standard)

```
web-research/                 # the shareable unit — copy this whole folder to use it
├── SKILL.md                  # frontmatter (name, description) + concise main instructions
├── reference/
│   └── search-strategy.md    # detail: query design, good/bad examples, verification, privacy
├── scripts/
│   ├── web_search.py         # search (DuckDuckGo, Google fallback) — no API key
│   └── web_read.py           # extract main content (trafilatura + BeautifulSoup)
├── requirements.txt
└── setup.sh
.clinerules                   # pointer so Cline reads SKILL.md when needed
```

Progressive disclosure: only `name` + `description` are preloaded; `SKILL.md` is read when the skill
activates; `reference/search-strategy.md` is read only when needed — keeping context lean.

## Install

```bash
cd web-research
bash setup.sh        # create .venv and install deps (run once)

# Test
.venv/bin/python scripts/web_search.py "python 3.13 release date" -n 3
.venv/bin/python scripts/web_read.py "https://example.com"
```

Requires Python 3.10+, internet access, **no API key**.

## Using it per environment

**Cline:** copy the `web-research/` folder and the `.clinerules` file into your workspace root, then
run `bash web-research/setup.sh`. Cline reads `.clinerules` → opens `SKILL.md` when it needs to
search/read/verify. Or paste `.clinerules` into **Global Rules** (Cline → Settings → Rules) to apply
it across all projects.

**Claude Code:** copy the `web-research/` folder into `.claude/skills/` (project) or
`~/.claude/skills/` (personal). Claude Code discovers the skill via its frontmatter.

**Claude API / claude.ai:** upload the skill per Anthropic's Agent Skills guide.

## How it behaves (after install)

No manual calls needed — chat normally and the agent uses it per `SKILL.md`:

- *"What's the latest stable version of library X?"* → search the Releases page, read it, answer with a link.
- *"Verify this: React 19 removed forwardRef…"* → split into claims, search official docs, label TRUE/FALSE + URL.
- *"Read & summarize this page: <URL>"* → `web_read` then summarize.

## Running the scripts directly (reference)

```bash
cd web-research
python3 scripts/web_search.py "<query>" -n 5
python3 scripts/web_search.py "<query>" --news            # news
python3 scripts/web_search.py "<query>" --region vn-vi    # Vietnam region
python3 scripts/web_read.py "<url>"
python3 scripts/web_read.py "<url>" --selector "article"  # specific part via CSS
python3 scripts/web_read.py "<url>" --links               # list links
```

## The "don't search blindly" mechanism

`SKILL.md` enforces a workflow: decompose the request → decide *whether a search is even needed* →
one goal per query with precise terms + operators (`"..."`, `site:`) → read the **original source**,
not the snippet → cross-check 2+ sources when it matters → conclude with the URL and a
**TRUE/FALSE/OUTDATED** verdict. Details + good/bad examples + query-privacy notes: `reference/search-strategy.md`.

## Dependencies
`ddgs`, `requests`, `beautifulsoup4`, `trafilatura`, `lxml`. No `mcp` needed.
