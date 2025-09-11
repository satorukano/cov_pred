from controller.evaluation_controller import EvaluationController

def setup_evaluate_parser(subparsers):
    parser = subparsers.add_parser('evaluate', help='Evaluate predictions')
    parser.add_argument('project', help='Project name')
    parser.add_argument('registry', help='Registry path')
    parser.set_defaults(func=handle_evaluate)

def setup_evaluate_method_parser(subparsers):
    parser = subparsers.add_parser('evaluate_method_level', help='Evaluate method-level predictions')
    parser.add_argument('project', help='Project name')
    parser.add_argument('registry', help='Registry path')
    parser.set_defaults(func=handle_evaluate_method)

def handle_evaluate(args):
    controller = EvaluationController(args.project, args.registry)
    controller.evaluate()

def handle_evaluate_method(args):
    controller = EvaluationController(args.project, args.registry)
    controller.method_level_evaluate()