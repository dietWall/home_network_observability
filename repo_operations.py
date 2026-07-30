#!/usr/bin/env python3

import shlex
import subprocess
import sys

VERBOSE = False

def repo_root():
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    print(result.stdout.decode().strip())
    return result.stdout.decode().strip()

COMMANDS = {
    # if we expect a different returncode than 0 from one of the commands
    # than we can extend the data structure with expected_returncode (default 0)

    "test": {
        "description": "Reruns the ubuntu scenario without a full rebuild",
        "steps": [
            "molecule converge -s ubuntu26_ssh",
            ],
        },

    "rebuild_ubuntu": {
        "description": "Recreate the whole environment",
        "steps": [
            "molecule destroy -s ubuntu",
            "molecule create -s ubuntu",
            "molecule converge -s ubuntu",
            "molecule converge -s ubuntu26_ssh",
            ],
        },

        "quick_test": {
        "description": "Runs some common linux commands",
        "steps": [
            "pwd",
            "ls -la",
            "whoami",
            "non_existing_binary_to_see_error_processing"
            ],
        },
        "setup_grafana" : {
            "description": "creates a service account in grafana",
            "steps" : [
                f"{repo_root()}/gcx_grafana/setup_grafana.py --command create_service_account",
                f"gcx datasources create -f {repo_root()}/gcx_grafana/datasources/datasources.yml",
                f"gcx datasources create -f {repo_root()}/gcx_grafana/datasources/loki.yml",
                f"{repo_root()}/gcx_grafana/setup_grafana.py --command put_repository",
            ]
        }
}

# ==============================================================================
# Runner
# ==============================================================================

def run_command(command):
    print(f">>> {command}")
    try:
        result = subprocess.run(
            shlex.split(command),
        )
    except FileNotFoundError as error:
        executable = shlex.split(command)[0]
        print()
        print("ERROR: Command not found")
        print(f"  Executable: {executable}")
        print(f"  Command:    {command}")
        print(f"  Details:    {error}")
        return False
    except PermissionError as error:
        executable = shlex.split(command)[0]
        print()
        print("ERROR: Permission denied")
        print(f"  Executable: {executable}")
        print(f"  Details:    {error}")
        return False
    except Exception as error:
        executable = shlex.split(command)[0]
        print()
        print("ERROR: Unhandled Exception caught, please implement")
        print(f"  Executable: {executable}")
        print(f"  Details:    {error}")
        print(f"  Type:       {type(error).__name__}")
        return False

    if VERBOSE:
        print(f"  Return code from {command}: {result.returncode}")

    if result.returncode != 0:
        print()
        print("ERROR: Command failed")
        print(f"  Exit code: {result.returncode}")
        print(f"  Command:   {command}")
        return False
    return True

def run_task(task_name):

    task = COMMANDS[task_name]
    print(f"=== {task['description']} ===")
    for command in task["steps"]:
        if not run_command(command):
            return False
    return True

def main():
    
    workflow_help = "Available workflows:"

    for name, workflow in COMMANDS.items():
        description = workflow.get("description", "")
        workflow_help += f"  {name:<20} {description}\n"

    import argparse
    parser = argparse.ArgumentParser(
        description="Run predefined Ansible and Molecule workflows.",
        epilog=workflow_help,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "workflow",
        metavar="WORKFLOW",
        help="Workflow to execute",
    )

    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    if args.workflow not in COMMANDS:
        parser.error(f"Unknown workflow: {args.workflow}")
    return run_task(args.workflow)

if __name__ == "__main__":
    sys.exit(main())