from controller.evaluation_controller import EvaluationController

def setup_evaluate_parser(subparsers):
    parser = subparsers.add_parser('evaluate', help='Evaluate predictions')
    parser.add_argument('mode', choices=['line', 'method', 'logcoco_method'],
                       help='Format mode')
    parser.add_argument('project', help='Project name')
    parser.add_argument('registry', help='Registry path')
    parser.set_defaults(func=handle_evaluate)

def handle_evaluate(args):
    if args.mode not in ['line', 'method', 'logcoco_method']:
        raise ValueError(f"{args.mode} mode is not supported")
    controller = EvaluationController(args.project, args.registry)

    if args.mode == 'line':
        controller.evaluate()
    elif args.mode == 'logcoco_line':
        controller.logcoco_evaluate()
    elif args.mode == 'method':
        controller.method_level_evaluate()
    elif args.mode == 'logcoco_method':
        controller.logcoco_method_level_evaluate()