# Booru-Pictag-Get-MCP

> **⚠️ 纯 AI 生成声明 | Pure AI-Generated Notice** — 详见 [`AIGC_NOTICE.md`](./AIGC_NOTICE.md)

An [MCP](https://modelcontextprotocol.io) server that searches booru image boards (Danbooru / AIBooru / e621 / Gelbooru / Rule34) and cleans their tags into **ready-to-use AI-art prompts** for Stable Diffusion / Illustrious / Pony / SDXL and any booru-tag-driven model.

This is a **Python port + MCP integration** of [`booru-prompt-gallery`](https://github.com/Mexes-GM/booru-prompt-gallery) by **Mexes-GM** (MIT). The prompt-cleaning pipeline — tag extraction, multi-subject guard, smart tag combination, redundancy folding, category splitting, background modes — is a 1:1 port of the original TypeScript modules. Wrapped as 4 callable MCP tools, no Web UI, no Supabase/Redis/Cloudflare deps. See [`AIGC_NOTICE.md`](./AIGC_NOTICE.md) for the full derivation & attribution.

| | |
|---|---|
| **Upstream** | [Mexes-GM/booru-prompt-gallery](https://github.com/Mexes-GM/booru-prompt-gallery) — TypeScript + Next.js 15 web app (MIT) |
| **This repo** | [echo-xianyu/Booru-Pictag-Get-MCP](https://github.com/echo-xianyu/Booru-Pictag-Get-MCP) — Python 3 + FastMCP server |
| **License** | MIT — original credit preserved, dual attribution. See [`LICENSE`](./LICENSE) |

---

## Install

### Option A — local path (zero publishing required)

Clone, then point `uvx` at the local checkout:

```bash
git clone https://github.com/echo-xianyu/Booru-Pictag-Get-MCP.git
cd Booru-Pictag-Get-MCP
uvx --from . booru-pictag-get-mcp
```

### Option B — cloud / direct from GitHub (no PyPI needed)

```bash
uvx --from "git+https://github.com/echo-xianyu/Booru-Pictag-Get-MCP" booru-pictag-get-mcp
```


### HTTP/2 extra (recommended — required for e621)

```bash
uvx --from . --with h2 booru-pictag-get-mcp
```
e621's TLS stack frequently errors out on HTTP/1.1 keep-alive. The HTTP client auto-detects `h2` and falls back to HTTP/1.1 if absent.

---

## Configure (opencode / any MCP client)

```jsonc
{
  "mcp": {
    "booru-pictag-get": {
      "command": "uvx",
      // Option A — local:
      "args": ["--from", "E:\\MCP\\booru-pictag-get-mcp", "booru-pictag-get-mcp"],
      // Option B — cloud (no checkout on disk):
      // "args": ["--from", "git+https://github.com/echo-xianyu/Booru-Pictag-Get-MCP", "booru-pictag-get-mcp"],
      // HTTP/2 for e621 — prepend "--with", "h2" to args above.
      "environment": {
        "BOORU_DEFAULT_PROVIDER": "danbooru",
        "DANBOORU_USERNAME_APIKEY": "youruser:yourkey",    // optional, raises rate limit
        "GELBOORU_USER_ID": "<your_user_id>",             // required by Gelbooru since 2025-08
        "GELBOORU_API_KEY": "<your_api_key>",
        "RULE34_USER_ID": "<your_user_id>",               // required by Rule34 since 2025-08
        "RULE34_API_KEY": "<your_api_key>"
      }
    }
  }
}
```

> **API key policy (Aug 2025):** Danbooru, AIBooru, and e621 work with **no key**. Gelbooru and Rule34 tightened auth and now require keys. Without them, those two providers return 401; the others keep working.

---

## Tools

| Tool | Use it for |
|---|---|
| `search_prompts` | **Recommended.** Search a booru tag → ready-to-use cleaned prompt + category split. One step. |
| `build_prompt` | Clean an already-known tag set (no network). Accepts raw booru format or comma-list. |
| `search_posts` | Raw post list (no cleaning). Inspect original tags before deciding how to process them. |
| `autocomplete_tags` | Turn a natural word into the canonical booru tag form. Call this BEFORE search if unsure of a tag's spelling. |

Each tool's description in `tools/list` carries full search-semantics guidance:
- Booru search is **tag-based AND**, not keyword search. Prefer a single tag (`hatsune_miku`) over stacking (`hatsune_miku blue_hair smile`), which usually returns 0 posts.
- Multi-word tags use underscore: `blue_hair`, never `blue hair`.
- Don't write natural-language queries ("a girl with blue hair sitting in a classroom"); translate to booru tags first via `autocomplete_tags`.

---

## Scope & design choices

- **Pure Python** — no Supabase / Redis / Cloudflare / Vercel. Endpoints are public booru APIs; no proprietary backend.
- **Tag-conflict rules are off by default** in the prompt pipeline (mirrors the original `cleanPrompt.ts`, which never called `tag-conflicts.ts`). The 180+ rules were authored assuming a single subject — enabling them by default would mangle legitimate multi-character prompts (e.g. `1girl+1boy` sex scenes, `smile+crying` bittersweet scenes, `long_hair+short_hair` two-character shots). The resolver remains callable via `booru_mcp.core.tag_conflicts.resolve_conflicts()` for explicit opt-in.
- **`optimize_tags` has a multi-subject guard**: when the prompt contains multi-character markers (`2girls` / `2boys` / `multiple_*` / `couple` / `group` / `duo` …), it skips the hair-length / breast-size / eye-color "keep best per hierarchy" pick and the shared-noun tag combination — so two characters with different features survive intact.
- **Tag categories for Gelbooru/Rule34** come from a static `data/tag_categories.json` dictionary (one-shot dump from Danbooru's public `tags.json`, generated by `scripts/dump_tag_categories.py`) with a keyword-classifier fallback. No external database at runtime.
- **Tag-conflict rules are overridable** via `data/tag_conflicts_overrides.json` (additive — overrides can only widen a built-in rule, never narrow it). See `data/tag_conflicts_overrides.example.json`. Audit current rules with `python scripts/inspect_tag_conflicts.py --builtin`.

---

## Credits

Prompt-cleaning pipeline ported (1:1 line-for-line where possible) from [`booru-prompt-gallery`](https://github.com/Mexes-GM/booru-prompt-gallery) by **Mexes-GM** (MIT). Original copyright preserved in [`LICENSE`](./LICENSE).

Python port + MCP server by [**echo-xianyu**](https://github.com/echo-xianyu). The vast majority of the code was generated by AI (opencode + GLM-5.2); see [`AIGC_NOTICE.md`](./AIGC_NOTICE.md) for the full statement.
