# Home Network Observability

Implementation of a home network observability stack based on a reusable Ansible automation template.

The project focuses on reproducible infrastructure provisioning, real SSH-based integration testing with Molecule, and GitOps-friendly infrastructure management.

An external inventory is included as a Git submodule, keeping infrastructure definitions separate from automation code.

# Features

- reproducible infrastructure provisioning
- real SSH integration testing with Molecule
- Full Ansible Vault support
- external inventory managed as a Git submodule
- GitOps-friendly project structure
- reusable deployment helper scripts

# Architecture

The project is structured around four independent components:

- **Automation** — Ansible roles and playbooks
- **Testing** — Molecule scenarios with real SSH connections
- **Infrastructure** — External inventory managed as a Git submodule
- **Secrets** — Ansible Vault for all credentials and sensitive configuration

---

## Deployment

### Create and Prepare the Test Environment

This creates a docker container and performs initial server configuration:

- creates the administrative user
- installs and configures OpenSSH
- installs Docker
- deploys the ED25519 SSH key pair
- configures privilege escalation

```bash
molecule prepare -s ubuntu
molecule converge -s ubuntu
```

### Validate the SSH Workflow

After provisioning, validate deployment over a real SSH connection:

```bash
molecule converge -s ubuntu26_ssh
```

This connects exclusively through SSH (127.0.0.1:2222) and verifies:

- SSH authentication
- service operation
- privilege escalation
- role execution against a real network connection

### Run All Scenarios

From the project root:

```bash
python run_molecule_scenarios.py rebuild
```

This performs the complete workflow in order:

1. destroys any previous test environment
2. creates a fresh Ubuntu instance
3. runs the provisioning scenario
4. runs the SSH validation scenario

### Clean Up

```bash
molecule destroy -s ubuntu
```

---

## Environment

Source the environment file to configure project paths and Vault credentials:

```bash
source .env
```

---

## Project Structure

```text
.
├── ansible_template/         # Ansible project
│   ├── inventories/          # Git submodule (external inventory)
│   ├── roles/
│   ├── molecule/
│   ├── setup_venv.sh
│   └── 
├── roles/                    # Reusable Ansible roles
├── molecule/                 # Molecule scenarios
└── repo_operations.py        # Deployment operations
```

---

## Requirements

- Python 3.11+
- Docker
- Git
- OpenSSH
- Ansible Core 2.21+
- Molecule 6+

---

## Future Improvements

Potential extensions:

- CI execution of Molecule scenarios
- multiple hosts in inventory
