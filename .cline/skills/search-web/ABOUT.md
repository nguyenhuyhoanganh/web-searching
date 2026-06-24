# Search Web — teach your AI to Google (properly)

Ever asked your AI assistant about the latest version of a library — and got a confident,
completely wrong answer? Or watched it hallucinate a URL that doesn't exist?

**That's what happens when an AI answers from memory instead of checking.**

This skill gives your Cline agent the ability to search the web and read any page, right from
the chat. No browser tab switching, no copy-pasting, no "let me check that for you." Just ask
naturally:

- *"What's the latest stable version of Spring Boot?"* — it searches, reads the release page,
  and answers with a link.
- *"Read this and summarize it: https://..."* — it fetches the page, extracts the content, and
  gives you the key points.
- *"Is it true that React 19 removed forwardRef?"* — it searches the official docs, checks the
  claim, and tells you TRUE or FALSE with a source.

### What makes it different

Most web tools just dump raw search results. This skill teaches the agent **how to research** —
not just search blindly. It knows to:

- Pick precise keywords instead of vague phrases
- Go to the original source, not trust a snippet
- Cross-check when sources disagree
- Always cite where the answer came from
- Say "I don't know" when nothing is found, instead of making something up

### Zero setup, zero cost

No API keys. No paid services. No MCP server. Just drop the skill folder into your workspace,
and the agent handles the rest — including installing its own dependencies on first use.

Works behind corporate proxies. Works without admin access. Works offline-first (the agent only
searches when it actually needs to).

**Stop trusting AI memory. Start trusting AI research.**
