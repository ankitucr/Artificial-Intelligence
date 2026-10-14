#!/usr/bin/env python3

import ast
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ACTIVE_SKILLS = ROOT / "skills" / "active"
REGISTRY = ROOT / "memory" / "registry.json"
STATS = ROOT / "memory" / "skill_stats.json"
GRAPH = ROOT / "memory" / "capability_graph.json"
INDEX = ROOT / "memory" / "capability_index.json"


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "how", "i", "in", "is", "it", "me", "of", "on",
    "or", "that", "the", "to", "use", "with", "you", "your",
    "this", "can", "do", "does", "what", "please"
}


def load_json(path, default):
    if not path.exists():
        return default

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )
        return data
    except Exception:
        return default


def save_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def tokens(text):
    words = re.findall(
        r"[a-zA-Z0-9_]+",
        str(text).lower()
    )

    return {
        word
        for word in words
        if word not in STOPWORDS
        and len(word) > 1
    }


def read_skill_metadata(path):
    data = {
        "description": "",
        "sample_args": {},
        "functions": [],
        "imports": []
    }

    try:
        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return data

    for node in tree.body:

        if isinstance(node, ast.Assign):
            for target in node.targets:

                if not isinstance(
                    target,
                    ast.Name
                ):
                    continue

                if target.id == "SKILL_DESCRIPTION":
                    try:
                        value = ast.literal_eval(
                            node.value
                        )

                        if isinstance(value, str):
                            data["description"] = value
                    except Exception:
                        pass

                elif target.id == "SAMPLE_ARGS":
                    try:
                        value = ast.literal_eval(
                            node.value
                        )

                        if isinstance(value, dict):
                            data["sample_args"] = value
                    except Exception:
                        pass

        elif isinstance(node, ast.FunctionDef):
            if node.name != "__main__":
                data["functions"].append(
                    node.name
                )

        elif isinstance(node, ast.Import):
            for item in node.names:
                data["imports"].append(
                    item.name
                )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                data["imports"].append(
                    node.module
                )

    return data


def build_index():
    registry = load_json(
        REGISTRY,
        {}
    )

    stats = load_json(
        STATS,
        {}
    )

    skills = {}

    for path in sorted(
        ACTIVE_SKILLS.glob("*.py")
    ):
        if path.name.startswith("_"):
            continue

        name = path.stem

        metadata = read_skill_metadata(
            path
        )

        reg = registry.get(
            name,
            {}
        )

        stat = stats.get(
            name,
            {}
        )

        description = (
            metadata["description"]
            or reg.get(
                "description",
                ""
            )
        )

        sample_args = metadata[
            "sample_args"
        ]

        functions = sorted(
            set(
                metadata["functions"]
                or reg.get(
                    "functions",
                    []
                )
            )
        )

        imports = sorted(
            set(
                metadata["imports"]
                or reg.get(
                    "imports",
                    []
                )
            )
        )

        searchable = " ".join([
            name,
            description,
            " ".join(functions),
            " ".join(imports),
            json.dumps(
                sample_args,
                ensure_ascii=False
            ),
            path.read_text(
                encoding="utf-8"
            )[:12000]
        ])

        skills[name] = {
            "name": name,
            "description": description,
            "functions": functions,
            "imports": imports,
            "sample_args": sample_args,
            "source": str(
                path.relative_to(ROOT)
            ),
            "version": reg.get(
                "version",
                "unknown"
            ),
            "sha256": reg.get(
                "sha256",
                ""
            ),
            "dangerous": bool(
                reg.get("dangerous")
            ),
            "usage": {
                "runs": stat.get(
                    "runs",
                    0
                ),
                "successes": stat.get(
                    "successes",
                    0
                ),
                "failures": stat.get(
                    "failures",
                    0
                )
            },
            "searchable": searchable
        }

    index = {
        "version": 2,
        "skills": skills
    }

    save_json(
        INDEX,
        index
    )

    return index


def similarity(query, text):
    a = " ".join(
        sorted(tokens(query))
    )
    b = " ".join(
        sorted(tokens(text))
    )

    if not a or not b:
        return 0.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def score_skill(query, skill):
    q = tokens(query)

    name_tokens = tokens(
        skill["name"]
    )

    description_tokens = tokens(
        skill["description"]
    )

    function_tokens = tokens(
        " ".join(
            skill["functions"]
        )
    )

    import_tokens = tokens(
        " ".join(
            skill["imports"]
        )
    )

    sample_tokens = tokens(
        json.dumps(
            skill["sample_args"],
            ensure_ascii=False
        )
    )

    source_tokens = tokens(
        skill["searchable"]
    )

    exact = (
        len(q & name_tokens) * 8
        + len(q & description_tokens) * 6
        + len(q & function_tokens) * 4
        + len(q & sample_tokens) * 3
        + len(q & import_tokens) * 1
        + len(q & source_tokens) * 1
    )

    fuzzy = similarity(
        query,
        skill["searchable"]
    )

    usage = skill.get(
        "usage",
        {}
    )

    successes = usage.get(
        "successes",
        0
    )

    failures = usage.get(
        "failures",
        0
    )

    total = successes + failures

    reliability = (
        successes / total
        if total
        else 0.0
    )

    return {
        "score": round(
            exact + fuzzy * 5,
            4
        ),
        "reliability": round(
            reliability,
            4
        ),
        "matched_terms": sorted(
            q & source_tokens
        )
    }


def find_candidates(
    query,
    limit=5
):
    index = load_json(
        INDEX,
        {}
    )

    skills = index.get(
        "skills",
        {}
    )

    if not skills:
        index = build_index()
        skills = index.get(
            "skills",
            {}
        )

    ranked = []

    for name, skill in skills.items():

        if skill.get("dangerous"):
            continue

        result = score_skill(
            query,
            skill
        )

        ranked.append({
            "skill": name,
            "score": result["score"],
            "reliability": result["reliability"],
            "matched_terms": result[
                "matched_terms"
            ],
            "description": skill[
                "description"
            ],
            "functions": skill[
                "functions"
            ],
            "sample_args": skill[
                "sample_args"
            ]
        })

    ranked.sort(
        key=lambda item: (
            item["score"],
            item["reliability"]
        ),
        reverse=True
    )

    return ranked[:limit]


def build_graph():
    index = build_index()

    skills = index.get(
        "skills",
        {}
    )

    names = list(skills)
    edges = []

    for i, first in enumerate(names):

        first_tokens = tokens(
            skills[first]["searchable"]
        )

        for second in names[i + 1:]:

            second_tokens = tokens(
                skills[second]["searchable"]
            )

            shared = sorted(
                first_tokens &
                second_tokens
            )

            if shared:
                edges.append({
                    "from": first,
                    "to": second,
                    "type": "semantic_related",
                    "shared_terms": shared
                })

    graph = {
        "version": 2,
        "nodes": skills,
        "edges": edges
    }

    save_json(
        GRAPH,
        graph
    )

    return graph


def create_plan(query, limit=5):
    candidates = find_candidates(
        query,
        limit=limit
    )

    usable = [
        item
        for item in candidates
        if item["score"] > 0
    ]

    steps = []

    for order, item in enumerate(
        usable,
        start=1
    ):
        steps.append({
            "order": order,
            "skill": item["skill"],
            "reason": item["description"],
            "confidence": item["score"],
            "reliability": item["reliability"],
            "args_template": item[
                "sample_args"
            ]
        })

    return {
        "query": query,
        "steps": steps,
        "skill_count": len(steps),
        "status": (
            "ready"
            if steps
            else "no_verified_skill_found"
        )
    }


def status():
    index = load_json(
        INDEX,
        {}
    )

    graph = load_json(
        GRAPH,
        {}
    )

    skills = index.get(
        "skills",
        {}
    )

    print(
        "========================================"
    )
    print(
        "        BEE5 CAPABILITY SYSTEM"
    )
    print(
        "========================================"
    )
    print(
        f"Indexed skills : {len(skills)}"
    )
    print(
        f"Graph edges    : {len(graph.get('edges', []))}"
    )

    for name, skill in skills.items():
        usage = skill.get(
            "usage",
            {}
        )

        print(
            f"- {name} | "
            f"runs={usage.get('runs', 0)} "
            f"success={usage.get('successes', 0)} "
            f"failure={usage.get('failures', 0)}"
        )

        print(
            f"  description: "
            f"{skill.get('description', '')}"
        )

    print(
        "========================================"
    )


def main():
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python capability_graph.py build\n"
            "  python capability_graph.py status\n"
            '  python capability_graph.py find "query"\n'
            '  python capability_graph.py plan "task"'
        )
        return 1

    command = sys.argv[1]

    if command == "build":
        graph = build_graph()

        print(
            "✅ Capability system rebuilt"
        )
        print(
            f"Skills: {len(graph['nodes'])}"
        )
        print(
            f"Relationships: {len(graph['edges'])}"
        )

        return 0

    if command == "status":
        status()
        return 0

    if command == "find":
        if len(sys.argv) < 3:
            print(
                'Usage: python capability_graph.py find "query"'
            )
            return 1

        build_graph()

        print(
            json.dumps(
                find_candidates(
                    sys.argv[2]
                ),
                ensure_ascii=False,
                indent=2
            )
        )

        return 0

    if command == "plan":
        if len(sys.argv) < 3:
            print(
                'Usage: python capability_graph.py plan "task"'
            )
            return 1

        build_graph()

        print(
            json.dumps(
                create_plan(
                    sys.argv[2]
                ),
                ensure_ascii=False,
                indent=2
            )
        )

        return 0

    print(
        f"Unknown command: {command}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
