# Home Network Observability

Ansible automation for deploying and managing home network observability services: Grafana, Loki, Alloy, Prometheus, Node-Exporter, and Docker.

The project uses Molecule for testing playbooks against real SSH connections to validate provisioning and operational stages.

An external inventory is included as a Git submodule, keeping infrastructure definitions separate from automation code.

---

## Deployment

### Provision the Reference Host

This creates the reference host and performs initial server configuration:

- creates the administrative user
- installs and configures OpenSSH
- installs Docker
- deploys the ED25519 SSH key pair
- configures privilege escalation

```bash
molecule converge -s ubuntu
```

### Validate the SSH Workflow

After provisioning, validate that all services work over SSH:

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
python run_molecule_scenarios.py all
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

Or remove all resources:

```bash
python run_molecule_scenarios.py clean
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
│   └── ...
├── ansible/                  # Deployed/inventories
├── roles/                    # Reusable Ansible roles
├── molecule/                 # Molecule scenarios
├── molecule.yml              # Molecule configuration
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

- GitHub Actions integration
- linting and security pipelines
- automatic documentation generation
- additional inventory layouts

Contributions and ideas are welcome.
