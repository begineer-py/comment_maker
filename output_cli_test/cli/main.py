from .args import parse_args
from core.orchestrator import ProjectOrchestrator


def main():
    """
    Entry point for the CLI.
    Parses arguments and calls the core processing engine.
    """
    args = parse_args()
    print("[INFO] CLI mode initiated.")
    # 將 args 轉換為字典
    settings = vars(args)
    print("[INFO] Settings: ", settings)
    # 創建協調器並運行
    orchestrator = ProjectOrchestrator(settings)
    orchestrator.run()
    print("[INFO] CLI execution finished.")
