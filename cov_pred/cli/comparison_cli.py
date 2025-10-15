from controller.logcoco_controller import LogcocoController
from controller.static_analysis_controller import StaticAnalysisController

def setup_compare_parser(subparsers):
    parser = subparsers.add_parser('compare', help='Compare data for training/validation')
    parser.add_argument('mode', choices=['prepare_logcoco', 'static_analysis'],
                       help='Compare mode')
    parser.add_argument('project', help='Project name')
    parser.add_argument('registry', help='Registry path')
    parser.set_defaults(func=handle_compare)

def handle_compare(args):
    if args.mode not in ['prepare_logcoco', 'static_analysis']:
        raise ValueError(f"mode is required")

    if args.mode == 'prepare_logcoco':
        controller = LogcocoController(args.project, args.registry)
        controller.prepare_log_data()
    
    if args.mode == 'static_analysis':
        module = 'module'
        if args.project == "zookeeper":
            module = "zookeeper-server"
        controller = StaticAnalysisController(args.project, args.registry, module)
        controller.analyze()