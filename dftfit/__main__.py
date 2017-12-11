import sys

from .cli import init_parser


def main():
    parser = init_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
