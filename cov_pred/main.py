import argparse
from cli.format_cli import setup_format_parser
from cli.gpt_cli import setup_gpt_parser
from cli.evaluate_cli import setup_evaluate_parser
from cli.comparison_cli import setup_compare_parser

def main():
    parser = argparse.ArgumentParser(description='Coverage prediction tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    setup_format_parser(subparsers)
    setup_gpt_parser(subparsers)
    setup_evaluate_parser(subparsers)
    setup_compare_parser(subparsers)

    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()