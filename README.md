# Home Network Observability

Ansible-based automation framework for deploying and testing a home network observability stack.

The project focuses on reproducible infrastructure provisioning, real SSH-based integration testing with Molecule, and GitOps-friendly infrastructure management.

The project uses Molecule for testing playbooks against real SSH connections to validate provisioning and operational stages.

An external inventory is included as a Git submodule, keeping infrastructure definitions separate from automation code.

# Features

- reproducible infrastructure provisioning
- real SSH integration testing with Molecule
- Full Ansible Vault support
- external inventory repository
- GitOps-friendly project structure
- reusable deployment helper scripts

---

## Deployment

### Create and Prepare the Test Environment

This creates the reference host and performs initial server configuration:

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

After provisioning, deploy all services over SSH to molecule container:

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

CI execution of Molecule scenarios
