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


def validate_args(args):
    """Validate parsed arguments and exit with a helpful message on error."""
    if args.target and not args.target.startswith(("http://", "https://")):
        print(
            f"error: --target must be a valid URL starting with http:// or https://",
            file=sys.stderr,
        )
        sys.exit(1)
    if not (1 <= args.port <= 65535):
        print(
            f"error: --port must be between 1 and 65535, got {args.port}",
            file=sys.stderr,
        )
        sys.exit(1)


def main(argv=None):
    args = parse_args(argv)
    validate_args(args)
    app = create_app(target_url=args.target)
    print(f"hookshot listening on http://{args.host}:{args.port}")
    if args.target:
        print(f"  forwarding to: {args.target}")
    print("  inspect requests at: /_hookshot/requests")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
