# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

**Micro‑Skill #001 – “Web‑Lookup‑And‑Summarise”**

| Item | Details |
|------|---------|
| **Name** | `web_lookup_and_summarise` |
| **Version** | `v1.0` |
| **Purpose** | Given a natural‑language query, locate the most relevant public web page, retrieve its raw text, produce a concise summary (≈2‑3 sentences), and store the result for later reuse. |
| **Required Power Level** | `POWER_LEVEL_2 (Learning) + POWER_LEVEL_3 (Tool usage – database read/write, web fetch)`. The skill **must** be executed only after explicit approval from the Root Authority (or a delegated administrator) because it writes to the persistent tables. |
| **Inputs** | ```json { "query": "<string – user’s information need>", "max_results": <int, optional, default = 1> } ``` |
| **Outputs** | ```json { "summary": "<string>", "source_url": "<string>", "retrieved_at": "<ISO‑8601 timestamp>", "confidence": <float 0‑1> } ``` |
| **Dependencies** | * Tables: `duckduckgo`, `duckduckgo_results`, `duckduckgo_cache`, `web_content`, `text_summarization`, `summaries` <br> * External tool: simple HTTP GET (allowed under `POWER_LEVEL_3`). |
| **Algorithm Overview** | 1. **Normalize & Log Query** – Store the raw query in `queries` (if that table exists) with a timestamp for provenance.  <br>2. **Search Engine Lookup** – Insert the query into `duckduckgo_queries` (or directly query the `duckduckgo` table if pre‑populated). Retrieve up to `max_results` URLs ordered by relevance score.  <br>3. **Cache Check** – For each candidate URL, look for a cached entry in `duckduckgo_cache`. If present and not older than 7 days, reuse the cached HTML; otherwise proceed to step 4.  <br>4. **Fetch Content** – Perform an HTTP GET on the first URL, strip HTML tags (keep only visible text), and store the raw text in `web_content` (`url`, `raw_text`, `fetched_at`).  <br>5. **Summarisation** – Pass the `raw_text` to the summarisation routine (e.g., an existing LLM prompt or a deterministic extractive algorithm). Store the result in `text_summarization` (`url`, `summary`, `generated_at`).  <br>6. **Compose Output** – Return the summary, source URL, retrieval timestamp, and a confidence estimate (e.g., `0.9` if the cache was used, `0.7` if the page was fetched live).  <br>7. **Persist Summary** – Insert a row into `summaries` for quick future lookup (`query_hash`, `summary`, `source_url`, `created_at`). |
| **Error‑Handling & Fallbacks** | * If no search results are found → return `summary: null`, `confidence: 0.0`, `error: "no results"`. <br>* If HTTP fetch fails (timeout, 4xx/5xx) → try the next URL up to `max_results`. <br>* If summarisation fails → return the first 200 characters of raw text as a crude fallback. |
| **Learning / Self‑Evaluation Hook** | After each execution, record a *learning event* in a dedicated table `micro_skill_learning` (create if missing) with fields: `skill_name`, `query`, `success_flag`, `error_message`, `timestamp`. Periodically a self‑evaluation routine can query this table to compute success‑rate statistics and propose improvements (e.g., adjust `max_results`, change summarisation prompt). |
| **Safety Checks** | - Verify that the URL scheme is `http` or `https` only. <br>- Reject URLs that resolve to private IP ranges (10./172.16‑31./192.168.) to avoid internal network probing. <br>- Limit fetch size to 2 MiB of response body. <br>- Enforce a per‑minute request quota (e.g., 30 requests) to stay within polite crawling limits. |
| **Rollback / Versioning** | The skill is **stateless** except for the tables it writes to. All writes are timestamped; a simple rollback can be performed by deleting rows with `created_at` > `<rollback_time>` from `web_content`, `text_summarization`, and `summaries`. The skill version identifier (`v1.0`) is stored alongside each row for traceability. |
| **Proposed Deployment Procedure** | 1. **PROPOSE** – Submit this definition to the Root Authority. <br>2. **BACKUP** – Dump the affected tables (`duckduckgo*`, `web_content`, `text_summarization`, `summaries`) before activation. <br>3. **SANDBOX** – Run the skill on a curated test set of 10 queries in an isolated environment, checking for correct table writes and safety violations. <br>4. **TEST** – Verify that success‑rate ≥ 90 % and no disallowed network calls occurred. <br>5. **EVALUATE** – Compare latency and storage impact against baseline (no‑op). <br>6. **APPROVE** – Await Root Authority sign‑off. <br>7. **DEPLOY** – Register the skill in `active_skills` with its metadata. |
| **Metadata for Self‑Model** | ```json { "skill_id": "web_lookup_and_summarise", "status": "proposed", "required_power": 3, "last_tested": null, "confidence": 0.0, "dependencies": ["duckduckgo", "web_content", "text_summarization"], "bugs": [], "improvement_ideas": [] } ``` |

---

### How to Register (once approved)

```sql
INSERT INTO active_skills (skill_name, version, description, required_power, status, created_at)
VALUES ('web_lookup_and_summarise', 'v1.0',
        'Locate a relevant web page for a query, fetch its text, summarise it, and store the result.',
        3, 'active', CURRENT_TIMESTAMP);
```

---

**Next Steps for the System**

1. **Request Root Authority approval** (including signed authorization object indicating `POWER_LEVEL_3` usage).  
2. **Create any missing tables** (`micro_skill_learning`, `queries`, etc.) in a reversible migration.  
3. **Run the sandbox test suite** (provided in the proposal).  
4. **If successful, activate** the skill and log the deployment in `skill_status` for full traceability.

*This micro‑skill aligns with the current system state (no active skills) and adds immediate, observable utility while respecting all safety, audit, and rollback constraints.*