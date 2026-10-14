from __future__ import annotations
"""Data-driven retrieval of public source knowledge with provenance and outcome logs.

Downloaded source is indexed as data and is never imported or executed. Retrieval uses
lexical TF-IDF/BM25-like ranking; it is advisory, not proof of correctness.
"""
import ast, hashlib, json, math, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".dart", ".rb", ".php", ".cs", ".cpp", ".h", ".hpp", ".html", ".css", ".sql", ".md", ".rst", ".txt", ".toml", ".yaml", ".yml"}
SKIP_PARTS = {".git", "node_modules", "vendor", "dist", "build", "__pycache__", ".venv", "venv", "target", "coverage"}
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,}|[0-9]{2,}")
STOP = {"the", "and", "for", "with", "from", "that", "this", "then", "when", "what", "where", "which", "into", "your", "you", "are", "can", "will", "use", "using", "used", "have", "has", "was", "were", "not", "but", "all", "any", "how", "why", "does", "did", "its", "their", "they", "our", "out", "per", "via", "also", "only", "each", "than", "more", "less"}

def _now(): return datetime.now(timezone.utc).isoformat()
def _tokens(text):
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(text))
    return [t.lower() for t in TOKEN_RE.findall(spaced) if t.lower() not in STOP]
def _sha(data): return hashlib.sha256(data).hexdigest()

class PikaCodeLearning:
    def __init__(self, root=None, max_file_bytes=300_000):
        self.root = Path(root) if root else ROOT
        self.corpus = self.root / "data" / "github_code_corpus"
        self.index_path = self.root / "data" / "pika_learning_index.json"
        self.events_path = self.root / "data" / "pika_learning_events.jsonl"
        self.max_file_bytes = max_file_bytes
        self.records = []
        self._load_index()

    def _load_index(self):
        try:
            p = json.loads(self.index_path.read_text(encoding="utf-8"))
            if p.get("schema") == 1 and isinstance(p.get("records"), list): self.records = p["records"]
        except (OSError, ValueError, TypeError): self.records = []

    def _save_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"schema": 1, "built_at": _now(), "records": self.records}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.index_path)

    def _event(self, event):
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": _now(), **event}, ensure_ascii=False) + "\n")

    def _describe(self, path, raw, text):
        rel = str(path.relative_to(self.corpus)); parts = Path(rel).parts
        repo = "/".join(parts[:2]) if len(parts) > 1 else parts[0]
        lang = path.suffix.lower().lstrip("."); symbols=[]; docs=[]; parse="not_applicable"
        if lang == "py":
            try:
                tree = ast.parse(text, filename=rel); parse="parsed"
                doc = ast.get_docstring(tree)
                if doc: docs.append(doc[:1800])
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        symbols.append(node.name); doc=ast.get_docstring(node)
                        if doc: docs.append(f"{node.name}: {doc[:1000]}")
            except (SyntaxError, ValueError): parse="syntax_error"
        identifiers = re.findall(r"\b[A-Za-z_$][A-Za-z0-9_$]{2,}\b", text[:100000])
        words = _tokens(" ".join([rel, repo, " ".join(symbols), " ".join(docs), " ".join(identifiers[:5000]), text[:100000]]))
        return {"path":rel,"repository":repo,"language":lang,"bytes":len(raw),"sha256":_sha(raw),"python_parse":parse,"symbols":symbols[:100],"summary":" ".join(docs)[:2400],"term_counts":dict(Counter(words)),"snippet":text[:5000]}

    def index_corpus(self, force=False):
        if not self.corpus.exists(): return {"indexed":0,"reason":"corpus_missing"}
        old={r.get("path"):r for r in self.records}; found={}; changed=0; errors=[]
        for p in self.corpus.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in TEXT_EXTENSIONS or any(x in SKIP_PARTS for x in p.parts): continue
            try:
                size=p.stat().st_size
                if size <= 0 or size > self.max_file_bytes: continue
                raw=p.read_bytes(); rel=str(p.relative_to(self.corpus)); digest=_sha(raw)
                if not force and rel in old and old[rel].get("sha256")==digest: found[rel]=old[rel]; continue
                found[rel]=self._describe(p,raw,raw.decode("utf-8",errors="replace")); changed+=1
            except (OSError,ValueError) as e: errors.append(str(e))
        self.records=list(found.values()); self._save_index()
        self._event({"type":"corpus_indexed","files":len(self.records),"changed":changed,"errors":errors[:20]})
        return {"indexed":len(self.records),"changed":changed,"errors":len(errors)}

    def retrieve(self, task, limit=4, max_snippet_chars=2200):
        if not self.records: self.index_corpus()
        q=Counter(_tokens(task))
        if not q or not self.records:
            self._event({"type":"retrieval","query":str(task)[:500],"hits":0})
            return {"query":str(task),"items":[],"reason":"no_query_terms_or_index"}
        n=len(self.records); df=Counter()
        for r in self.records: df.update(set(r.get("term_counts",{})))
        scored=[]
        for r in self.records:
            terms=r.get("term_counts",{}); total=sum(terms.values()) or 1; score=0.; matched=[]
            for term,qcount in q.items():
                tf=terms.get(term,0)
                if not tf: continue
                matched.append(term); idf=math.log(1+(n-df.get(term,0)+.5)/(df.get(term,0)+.5))
                norm=(tf*2.2)/(tf+1.2*(.25+.75*total/500))
                score += idf*norm*(1+math.log(qcount))
            if matched:
                if r.get("python_parse")=="parsed": score*=1.03
                if r.get("summary"): score*=1.08
                scored.append((score,r,matched))
        scored.sort(key=lambda x:(x[0],len(x[2])),reverse=True); items=[]
        for score,r,matched in scored[:max(0,min(int(limit),10))]:
            items.append({"source":r["path"],"repository":r.get("repository"),"language":r.get("language"),"sha256":r.get("sha256"),"relevance":round(score,5),"matched_terms":matched[:20],"summary":r.get("summary","")[:900],"snippet":r.get("snippet","")[:max_snippet_chars],"warning":"Untrusted public source; inspect/adapt, do not execute as-is."})
        self._event({"type":"retrieval","query":str(task)[:500],"hits":len(items),"sources":[x["source"] for x in items]})
        return {"query":str(task),"items":items,"method":"lexical_tfidf_bm25_like","is_semantic_model":False}

    def record_outcome(self, task, retrieval, *, success, evaluation=None, used=False, attempt=None):
        e=evaluation if isinstance(evaluation,dict) else {}
        self._event({"type":"task_outcome","task":str(task)[:700],"success":bool(success),"evaluation_passed":e.get("passed"),"evaluation_score":e.get("score"),"knowledge_retrieved":bool((retrieval or {}).get("items")),"knowledge_context_attached":bool(used),"sources":[x.get("source") for x in (retrieval or {}).get("items",[])],"attempt":attempt})

    def stats(self): return {"indexed_files":len(self.records),"index_path":str(self.index_path),"events_path":str(self.events_path)}
