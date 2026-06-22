# Search Strategy — query design & verification

Detailed reference for the `web-research` skill. Read this when crafting a good query or verifying content.

## Contents
- Query design
- Search operators
- Good vs Bad examples
- Source priority
- Verifying user-pasted content
- Query privacy

## Query design

- **Extract the core keywords**, drop filler ("how do I", "please", "what do you think").
- **Use exact entities + versions**: `<name> <version> <official term>`.
- **Technical topics → use English** (primary documentation is mostly in English).
- **Add intent qualifiers**: `latest`, `release notes`, `changelog`, `documentation`, `vs`,
  `deprecated`, `migration guide`, plus a year if you need a time anchor.
- **One goal per query.** Need several things → run several separate queries.

## Search operators

Pass these literally inside the `query` string:

- `"exact phrase"` — keep a phrase/name/error message intact.
- `site:domain` — restrict the source, e.g. `site:docs.python.org`, `site:github.com`.
- Error messages: keep them **verbatim in quotes**, but strip the volatile parts (absolute paths,
  line numbers, memory addresses) so the query matches more cases.

## Good vs Bad examples

| User request | ❌ Bad query | ✅ Good query |
|---|---|---|
| "Does the latest Spring Boot support Java 21?" | `spring boot java` | `Spring Boot latest version Java 21 support site:spring.io` → then read the release notes page |
| Error `NoClassDefFoundError: javax/xml/bind/JAXBException` on Java 11 | `java jaxb error` | `"NoClassDefFoundError" "javax/xml/bind/JAXBException" Java 11 fix` |
| "Did React 19 remove forwardRef?" | `react forwardRef` | `React 19 forwardRef deprecated site:react.dev` → read the blog/docs → TRUE/FALSE verdict |
| "Which version of library X is most stable?" | `X library` | `<X> latest stable release` + `site:github.com <X> releases` → read the Releases page |
| "Compare Postgres vs MySQL for analytics" | `postgres mysql` | `PostgreSQL vs MySQL OLAP analytical workload comparison` → read 2 sources, cross-check |

## Source priority

1. Official documentation / website (docs, project home, release notes, RFC, spec).
2. The upstream GitHub repo (README, CHANGELOG, issues, releases).
3. Reputable sources (MDN, highly-upvoted Stack Overflow, the author's/org's own blog).
4. Everything else: treat as a lead, cross-check before trusting.

Beware SEO spam, AI-generated filler, and stale docs. Always check the **publication date**.

## Verifying user-pasted content

1. **Split into individual factual claims** (one asserted fact per statement).
2. For each claim → one `web_search` → `web_read` the original source.
3. Label each claim: **TRUE / FALSE / OUTDATED / INSUFFICIENT EVIDENCE** + source URL.
4. If FALSE → give the correct information with a source. If sources conflict → present both sides.
5. **Do not fabricate.** If nothing is found, say so; do not guess.

## Query privacy

Queries leave the machine and reach an external search engine. Do **not** put secrets, tokens, API
keys, customer names, internal hostnames/service names, or proprietary code into a query. Search
only with public terms. If the information you need to look up is itself confidential, do not search
for it — a web search cannot help with internal data anyway.
