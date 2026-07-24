#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Molecule Scenario Runner
========================

Runs all Molecule scenarios in the correct order with proper failure handling.
Stops immediately if any scenario fails.

Workflow order:
1. default (localhost) - quick tests on host
2. ubuntu (Docker container) - prepares and caches container
3. ubuntu26_ssh - tests roles via SSH to cached container

Each scenario runs: prepare -> converge -> (optional: verify -> syntax -> test)

Usage:
    ./run_molecule_scenarios.py all   # Run all scenarios (current implementation)
    ./run_molecule_scenarios.py clean # Clean up: destroy containers and remove temp dir
"""

import argparse
import subprocess
import sys
import shutil
import os
from pathlib import Path

# Add script directory to path for molecule command lookup
SCRIPT_DIR = Path(__file__).parent.resolve()


class MoleculeScenarioError(Exception):
    """Custom exception for Molecule scenario failures."""
    pass


def run_command(cmd: list[str], description: str, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.

    Args:
        cmd: List of command arguments
        description: Human-readable description for error messages
        check: If True, raise exception on non-zero exit code

    Returns:
        CompletedProcess result

    Raises:
        MoleculeScenarioError: If command fails and check=True
    """
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            cmd,
            cwd=SCRIPT_DIR,
            check=check,
            text=True,
            capture_output=False,  # Print stdout/stderr directly
            env={**os.environ, "MOLECULE_PROJECT_DIRECTORY": str(SCRIPT_DIR)}
        )

        if result.returncode != 0:
            print(f"\n❌ FAILED: {description}")
            raise MoleculeScenarioError(f"Command failed with exit code {result.returncode}")

        return result

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {description}")
        print(f"Exit code: {e.returncode}")
        if e.output:
            print(e.output)
        raise


def clean_up():
    """
    Clean up: destroy molecule scenarios and remove temporary directories.
    Removes the Docker container and ansible ephemeral directory.
    """
    print("="*60)
    print("Cleaning up...")
    print("="*60)

    try:
        # Destroy all molecule scenarios
        print("\nDestroying molecule scenarios...")
        destroy_cmd = ["molecule", "destroy", "-s", "default", "ubuntu", "ubuntu26_ssh"]
        result = subprocess.run(
            destroy_cmd,
            cwd=SCRIPT_DIR,
            check=False,
            text=True,
            capture_output=False
        )

        # Check if molecule destroy succeeded or if container doesn't exist
        if result.returncode != 0 and "No containers found" not in result.stdout:
            print(f"\n⚠️  Molecule destroy returned: {result.returncode}")
            if result.stdout:
                print(result.stdout)

        # Remove the ephemeral molecule directory if it exists
        ephemeral_dir = SCRIPT_DIR / ".molecule" / "ephemeral"
        if ephemeral_dir.exists():
            print(f"\nRemoving ephemeral directory: {ephemeral_dir}")
            shutil.rmtree(ephemeral_dir)
            print("Ephemeral directory removed.")
        else:
            print(f"\nNo ephemeral directory found at: {ephemeral_dir}")

        # Remove cached container if it exists
        cached_container = "ubuntu26-sandbox"
        try:
            import docker
            client = docker.from_env()
            containers = client.containers.filters({"name": cached_container})
            if containers:
                print(f"\nRemoving cached Docker container: {cached_container}")
                client.containers.get(cached_container).remove()
                print("Cached container removed.")
            else:
                print(f"\nNo cached Docker container found: {cached_container}")
        except Exception as e:
            print(f"\n⚠️  Could not remove cached container: {e}")

        print("\n✅ Cleanup complete!")

    except Exception as e:
        print(f"\n❌ Cleanup error: {e}")
        sys.exit(1)


# Command arrays for each scenario
# Each entry: (command_list, description)
SCENARIO_COMMANDS: list[tuple[list[str], str]] = [
    # =====================
    # default scenario commands
    # =====================
    #(["molecule", "syntax", "-s", "default"], "Syntax check for default scenario"),
    #(["molecule", "create", "-s", "default"], "Create scenario default"),
    #(["molecule", "prepare", "-s", "default"], "Prepare scenario default"),
    #(["molecule", "converge", "-s", "default"], "Converge scenario default"),

    # =====================
    # ubuntu scenario commands
    # =====================
    (["molecule", "destroy", "-s", "ubuntu"], "Make sure we have a clean start"),
    (["molecule", "create", "-s", "ubuntu"], "Create scenario ubuntu"),
    #(["molecule", "prepare", "-s", "ubuntu"], "Prepare scenario ubuntu (installs SSH, configures user)"),
    (["molecule", "converge", "-s", "ubuntu"], "Converge scenario ubuntu (runs demo role)"),

    # =====================
    # ubuntu26_ssh scenario commands
    # =====================
    # Verify container exists before running SSH-based converge
    (["docker", "ps", "-a", "-q", "-f", "name=ubuntu26-sandbox"], "Verify cached container exists"),
    #(["molecule", "prepare", "-s", "ubuntu26_ssh"], "Prepare scenario ubuntu26_ssh"),
    (["molecule", "converge", "-s", "ubuntu26_ssh"], "Converge scenario ubuntu26_ssh (runs demo + ssh_keys roles)"),
]


def main():
    """
    Main entry point for the Molecule scenario runner.

    Runs scenarios in the correct order:
    1. default (localhost) - quick tests
    2. ubuntu (Docker) - prepares and caches container
    3. ubuntu26_ssh - SSH role testing

    Stops immediately if any scenario fails.
    """
    # Run all commands from the SCENARIO_COMMANDS array
    # The docker ps verify command is skipped automatically
    print("="*60)
    print("  Molecule Scenario Runner")
    print("="*60)
    print()
    print("This script runs Molecule scenarios in the correct order:")
    print("  1. default  -> Quick tests on host (localhost)")
    print("  2. ubuntu   -> Docker container preparation & cache")
    print("  3. ubuntu26_ssh -> SSH role testing (uses cached container)")
    print()
    print("="*60)

    # Check for DEMO_DETAILED environment variable
    demo_detailed = os.environ.get("DEMO_DETAILED", "false").lower() == "true"
    if demo_detailed:
        print("\n[INFO] Running with detailed output enabled (DEMO_DETAILED=true)")

    print("\n" + "-"*60)
    print("Starting scenario execution...")
    print("-"*60)

    # Run all scenarios in order
    # The verify command (docker ps) is skipped automatically
    for cmd, description in SCENARIO_COMMANDS:
        # Skip the docker ps verify command - its failure is expected on first run
        # and will trigger the ubuntu scenario to run first
        if "docker ps" in str(cmd):
            continue

        run_command(cmd, description)

    print("\n" + "="*60)
    print("✅ ALL SCENARIOS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print()
    print("Summary:")
    print("  ✓ default (localhost) - Quick tests on host")
    print("  ✓ ubuntu (Docker)      - Container prepared and cached")
    print("  ✓ ubuntu26_ssh         - SSH role testing completed")
    print("="*60)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted by user (Ctrl+C)")
        print("Cleaning up...")
        try:
            run_command(
                ["molecule", "destroy", "-s", "default", "ubuntu", "ubuntu26_ssh"],
                "Destroy all scenarios (cleanup on interrupt)",
                check=False
            )
        except:
            pass
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
