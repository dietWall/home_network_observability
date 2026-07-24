# Ansible Foundation

A reference project demonstrating how to build portable, reproducible, and production-oriented Ansible development environments with Molecule.

Unlike typical Molecule examples that only validate playbooks against disposable containers, this project models the lifecycle of a freshly provisioned Linux server and verifies that Ansible roles operate correctly over a real SSH connection.

The goal is to make local development resemble production as closely as possible while keeping infrastructure, inventories, and secrets strictly separated from the automation code.

---

# Design Goals

This project is built around the following principles:

- Separate infrastructure definitions from automation code.
- Keep inventories and secrets outside of the automation repository.
- Reuse production inventory structures during local development.
- Simulate a realistic server provisioning workflow.
- Validate Ansible roles over actual SSH connections instead of only Docker APIs.
- Keep the project portable across developer machines and CI/CD pipelines.

---

# Design Decisions

## Separation of Infrastructure and Automation

Infrastructure, inventories, and secrets evolve independently from automation code. Therefore, they are intentionally stored outside this repository.

The inventory is integrated as a Git submodule, while credentials are provided through Ansible Vault and local environment variables.

This separation offers several advantages:

- Automation code remains reusable.
- Inventories can evolve independently.
- Secrets never need to be committed to the automation repository.
- Different environments can reuse the same automation without modifications.

---

## Simulating a Real Provisioning Workflow

Many Molecule examples assume that a server is already configured and immediately accessible using SSH keys.

In reality, provisioning a new server usually follows a different sequence:

1. Install the operating system.
2. Create the administrative user.
3. Install and configure OpenSSH.
4. Perform the initial login using bootstrap credentials.
5. Deploy the user's SSH public key.
6. Continue administration exclusively through SSH key authentication.

This repository mirrors that workflow.

The first Molecule scenario represents the provisioning stage.

The second scenario assumes that provisioning has already completed and validates the system by connecting exclusively through SSH.

Testing these stages independently provides confidence that not only the Ansible role itself works correctly, but also that the resulting machine behaves exactly as expected for ongoing administration.

---

## Variable Isolation

Production inventories often contain connection parameters that differ from the local Molecule environment.

Loading these variables directly into Ansible's global namespace can unintentionally overwrite Molecule's connection settings because of Ansible's variable precedence rules.

To avoid this, production host variables are loaded into the dedicated namespace `real_host_vars`.

This allows production inventories to be reused safely during testing without risking accidental connections to production systems.

---

# Features

## Portable Repository

The project contains no hardcoded absolute paths.

All paths are resolved dynamically relative to the Git repository root using

```bash
git rev-parse --show-toplevel
```

This makes the project portable across developer workstations and CI/CD environments.

---

## Inventory Repository as Git Submodule

Infrastructure definitions intentionally remain outside the automation repository.

Benefits include:

- independent versioning
- reusable automation code
- private production inventories
- clear separation of responsibilities

---

## Multi-Environment Support

Different environments can be selected simply by sourcing another environment file.

Examples include:

- `.env`
- `.env_staging`
- `.env_production`

Environment files automatically configure project paths and Vault credentials for the current shell session.

---

## Secure Secret Handling

Secrets are evaluated directly from encrypted `vault.yml` files.

The project demonstrates:

- Ansible Vault integration
- Vault passwords supplied through environment variables
- SHA-512 password hashes using `password_hash('sha512')`
- authenticated privilege escalation using `ansible_become_password`
- no plaintext credentials inside playbooks

---

## Real SSH Validation

Instead of relying exclusively on Docker transport, the project validates:

- OpenSSH installation
- SSH public key authentication
- sudo configuration
- privilege escalation
- complete Ansible execution over a real SSH connection

---

# Workflow

The demonstration consists of two Molecule scenarios.

## Scenario 1 — `ubuntu`

**Driver:** Docker

This scenario represents the initial provisioning of a freshly installed Ubuntu server.

Tasks include:

- creating the administrative user
- configuring sudo
- installing and enabling OpenSSH
- deploying the SSH public key

---

## Scenario 2 — `ubuntu26_ssh`

**Driver:** Default / Delegated

After provisioning has completed, Molecule no longer communicates with Docker directly.

Instead, it connects to the already running instance exclusively through SSH (`127.0.0.1:2222`) and executes the role exactly as it would against a remote production host.

This validates:

- SSH connectivity
- public-key authentication
- privilege escalation
- successful Ansible execution over a real network connection

---

# Project Structure

```text
ansible_foundation/
├── inventories/              # Git submodule
├── roles/
│   └── demo/
├── molecule/
│   ├── ubuntu/
│   └── ubuntu26_ssh/
├── setup_venv.sh
├── run_molecule_scenarios.py
├── .env
└── README.md
```

---

# Requirements

The project has been tested with:

- Python 3.11+
- Docker
- Git
- OpenSSH
- Ansible Core 2.21+
- Molecule 6+

---

# Getting Started

## Clone the Repository

The project itself is located in the `ansible_foundation/` subdirectory of the repository.

```bash
git clone --recurse-submodules https://github.com/dietWall/ansible_template.git
cd ansible_template/ansible_foundation
```

If you have already cloned the repository without submodules, initialize them manually:

```bash
git submodule update --init --recursive
```

---

## Create the Python Environment

The project uses a dedicated Python virtual environment to ensure consistent versions of Ansible, Molecule, and all required plugins.

Run:

```bash
./setup_venv.sh
```

This script creates a local virtual environment (`venv`) and installs all required dependencies.

---

## Generate the Test SSH Key

The SSH validation scenario uses a dedicated ED25519 key pair named `local_net_key`.

Generate it once using:

```bash
ssh-keygen -t ed25519 \
-f ~/.ssh/local_net_key \
-N ""
```

This creates:

```text
~/.ssh/local_net_key
~/.ssh/local_net_key.pub
```

Your existing SSH identities remain untouched.

The public key is deployed automatically during the provisioning scenario.

---

## Load the Environment

The repository provides a local environment configuration that configures project paths and Vault credentials.

Load it into your current shell session:

```bash
source .env
```

---

# Running the Demonstration

## Step 1 – Change to the Project Directory

All commands below are executed from the project root:

```bash
cd ansible_template
```

---

## Step 2 – Provision the Reference Host

Execute the provisioning scenario:

```bash
molecule converge -s ubuntu
```

This creates the reference host `your_server` and performs the initial server configuration:

- creates the administrative user
- installs and configures OpenSSH
- deploys the SSH public key
- configures privilege escalation

```bash
docker ps
```

The container exposes SSH on host port **2222**.

---

## Step 3 – Validate the SSH Workflow

```bash
molecule converge -s ubuntu26_ssh
```

Unlike the first scenario, Molecule no longer manages the container.

Instead, it connects exclusively through SSH:

```
127.0.0.1:2222
```

This validates that:

- SSH authentication works
- privilege escalation works
- the deployed role executes successfully
- the server behaves like a provisioned production machine

---

# Running All Scenarios

From the project root, execute:

```bash
python run_molecule_scenarios.py all
```

The runner performs the complete workflow in the correct order:

1. Destroy any previous test environment.
2. Create a fresh Ubuntu instance.
3. Execute the provisioning scenario.
4. Execute the SSH validation scenario.

This verifies both the provisioning stage and the operational SSH stage in a single execution.

---

# Cleaning Up

Destroy the test environment:

```bash
molecule destroy -s ubuntu
```

Or remove all generated resources:

```bash
python run_molecule_scenarios.py clean
```

---

# Why This Repository Exists

Many Molecule examples demonstrate how to test an Ansible role inside a disposable Docker container.

While this is useful for unit testing, production environments usually involve additional concerns:

- inventories live in separate repositories
- secrets are managed independently
- servers require an initial bootstrap phase
- administration happens through SSH
- multiple environments share the same automation

This repository demonstrates one possible architecture for addressing these challenges while keeping the development workflow reproducible and portable.

The focus is not on replacing production infrastructure but on making local testing resemble real-world deployments as closely as practical.

---

# Future Improvements

Potential extensions include:

- additional Linux distributions
- cloud provider scenarios
- GitHub Actions integration
- linting and security pipelines
- automatic documentation generation
- support for additional inventory layouts

Contributions and ideas are always welcome.