from controller.format_controller import FormatController

def setup_format_parser(subparsers):
    parser = subparsers.add_parser('format', help='Format data for training/validation')
    parser.add_argument('mode', choices=['train', 'validate', 'train_method_level', 'validate_method_level'],
                       help='Format mode')
    parser.add_argument('project', help='Project name')
    parser.add_argument('module', help='Module name')
    parser.add_argument('registry', help='Registry path')
    parser.add_argument('--model', help='Model name (required for validate modes)')
    parser.set_defaults(func=handle_format)

def handle_format(args):
    if args.mode not in ['validate', 'validate_method_level'] and not args.model:
        raise ValueError(f"--model is required for {args.mode} mode")
    
    controller = FormatController(args.project, args.registry, args.module)
    controller.setup()
    
    if args.mode == 'train':
        controller.setup_line_level()
        controller.format_for_training()
    elif args.mode == 'validate':
        controller.setup_line_level()
        controller.format_for_validation(args.model)
        controller.make_validation_oracle()
    elif args.mode == 'train_method_level':
        controller.setup_method_level()
        controller.format_for_training()
    elif args.mode == 'validate_method_level':
        controller.setup_method_level()
        controller.format_for_validation(args.model)
        controller.make_validation_oracle()