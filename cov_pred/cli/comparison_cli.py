from controller.comparison_controller import ComparisonController

def setup_compare_parser(subparsers):
    parser = subparsers.add_parser('compare', help='Compare data for training/validation')
    parser.add_argument('mode', choices=['prepare_logcoco'],
                       help='Compare mode')
    parser.add_argument('project', help='Project name')
    parser.add_argument('registry', help='Registry path')
    parser.set_defaults(func=handle_compare)

def handle_compare(args):
    if args.mode not in ['prepare_logcoco'] :
        raise ValueError(f"mode is required")

    controller = ComparisonController(args.project, args.registry)

    if args.mode == 'prepare_logcoco':
        controller.prepare_log_data_for_logcoco()