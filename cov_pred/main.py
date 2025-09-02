from controller.format_controller import FormatController
from controller.gpt_controller import GPTController
from controller.evaluation_controller import EvaluationController
import sys
from dotenv import load_dotenv
load_dotenv()

def main():
    if len(sys.argv) == 0:
        print("need args")
        sys.exit(1)
    method = sys.argv[1]

    # Route to the appropriate controller based on the method argument
    if method == "format":
        if len(sys.argv) != 6:
            print("need args")
            sys.exit(1)
        project = sys.argv[3]
        module = sys.argv[4]
        registry = sys.argv[5]
        format_controller = FormatController(project, registry, module)
        format_controller.setup()
        if sys.argv[2] == "train":
            format_controller.format_for_training()
        elif sys.argv[2] == "validate":
            if len(sys.argv) != 7:
                print("need model arg")
                sys.exit(1)
            model = sys.argv[6] 
            format_controller.format_for_validation(model)
            format_controller.make_validation_oracle()
        else:
            print("unknown method")
            sys.exit(1)
    elif method == "gpt":
        if len(sys.argv) != 5:
            print("need args")
            sys.exit(1)
        project = sys.argv[3]
        registry = sys.argv[4]
        gpt_controller = GPTController(project, registry)
        if sys.argv[2] == "finetune":
            gpt_controller.finetune()
        elif sys.argv[2] == "batch":
            gpt_controller.batch_request()
        else:
            print("unknown method")
            sys.exit(1)
    elif method == "evaluate":
        if len(sys.argv) != 5:
            print("need args")
            sys.exit(1)
        project = sys.argv[2]
        registry = sys.argv[3]
        evaluation_controller = EvaluationController(project, registry)
        evaluation_controller.evaluate()



if __name__ == "__main__":
    main()