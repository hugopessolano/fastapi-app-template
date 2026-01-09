import argparse
from pathlib import Path

from tools.scaffold.scaffold import create_resource, modify_resource, remove_resource, sync_resource


def main() -> None:
    parser = argparse.ArgumentParser(prog="scaffold")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("create", "modify", "sync", "remove"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--spec", required=True)
        sub.add_argument("--root", default=".")
        if name == "remove":
            sub.add_argument("--delete-spec", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    spec_path = Path(args.spec).resolve()

    if args.command == "create":
        create_resource(root, spec_path)
    elif args.command == "modify":
        modify_resource(root, spec_path)
    elif args.command == "sync":
        sync_resource(root, spec_path)
    else:
        remove_resource(root, spec_path, delete_spec=args.delete_spec)
