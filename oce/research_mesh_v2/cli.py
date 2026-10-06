from __future__ import annotations

import argparse
import json

from .service import ResearchMesh


def main() -> int:
    p = argparse.ArgumentParser(prog="research-mesh-v2")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--source", default="openalex", choices=["openalex", "arxiv", "semantic_scholar", "all"])
    s.add_argument("--limit", type=int, default=5)
    s.add_argument("--no-persist", action="store_true")

    q = sub.add_parser("query")
    q.add_argument("query")
    q.add_argument("--limit", type=int, default=20)

    args = p.parse_args()
    mesh = ResearchMesh()
    try:
        if args.cmd == "search":
            if args.source == "all":
                payload = [r.to_dict() for r in mesh.search_all(args.query, args.limit, persist=not args.no_persist)]
            else:
                payload = mesh.search(args.query, args.source, args.limit, persist=not args.no_persist).to_dict()
        else:
            payload = {"query": args.query, "records": mesh.query_local(args.query, args.limit)}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    finally:
        mesh.close()


if __name__ == "__main__":
    raise SystemExit(main())
