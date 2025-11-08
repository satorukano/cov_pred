from controller.gpt_controller import GPTController

def setup_gpt_parser(subparsers):
    parser = subparsers.add_parser('gpt', help='GPT-related operations')
    parser.add_argument('mode', choices=['finetune', 'finetune_method_level', 'finetune_bulk', 'batch', 'batch_method_level', 'batch_bulk'],
                       help='GPT operation mode')
    parser.add_argument('project', help='Project name')
    parser.add_argument('registry', help='Registry path')
    parser.set_defaults(func=handle_gpt)

def handle_gpt(args):
    controller = GPTController(args.project, args.registry)
    
    if args.mode == 'finetune':
        controller.finetune()
    elif args.mode == 'finetune_method_level':
        controller.method_level_finetune()
    elif args.mode == 'finetune_bulk':
        controller.bulk_finetune()
    elif args.mode == 'batch':
        controller.batch_request()
    elif args.mode == 'batch_method_level':
        controller.method_level_batch_request()
    elif args.mode == 'batch_bulk':
        controller.bulk_batch_request()