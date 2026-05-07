import argparse
import sys
from hookshot.server import create_app


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="hookshot",
        description="Lightweight webhook relay server for local development.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to listen on (default: 5000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Target URL to forward requests to",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug mode",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    app = create_app(target_url=args.target)
    print(f"hookshot listening on http://{args.host}:{args.port}")
    if args.target:
        print(f"  forwarding to: {args.target}")
    print("  inspect requests at: /_hookshot/requests")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
