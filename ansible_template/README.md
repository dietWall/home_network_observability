# Ansible Demo Role Foundation

## 🎯 Goals

This project provides a Docker-based sandboxing environment for testing Ansible roles with Molecule, using Ubuntu 26.04 as the target OS.

**Core Objectives:**
- Demonstrate Molecule's two-stage workflow (container preparation + role testing)
- Showcase native Ansible inventory handling (Molecule v6 compatibility)
- Provide reusable `demo` role for quick verification without external SSH
- Demonstrate SSH-based role testing via cached Docker containers
- Serve as foundation for future Prometheus and service integrations
- Support full SSH workflow with `ssh_keys` role for key generation/deployment

> **Note:** The `ssh_verify` role is a placeholder for future implementation. The `ssh_keys` role is fully functional and handles SSH key generation and deployment. Both roles are tested via the `ubuntu26_ssh` scenario which connects to a cached Docker container.

## ✨ Features

### Quick Verification with Demo Role and SSH Keys

The **demo role** provides immediate feedback to verify Ansible is working correctly.

The **ssh_keys role** manages SSH key generation and deployment.

**Run converge on localhost:**
```bash
cd ansible_template
DEMO_DETAILED=false molecule converge -s localhost
```

**Output includes:**
- Demo title and status messages
- Ansible version and connection type
- System facts (OS, distribution, architecture)
- Command output examples (whoami, time, etc.)
- Conditional task demonstrations
- SSH key generation and deployment (when ssh_keys role runs)

**Verbose mode:**
```bash
DEMO_DETAILED=true molecule converge -s localhost
```

### 1. Prerequisites

```bash
# Check Ansible and Python are available
ansible --version
python --version
```

### 2. Setup

```bash
# Activate virtual environment (optional but recommended)
source venv/bin/activate

# Install dependencies
pip install -r requirements.yml

# (Optional) Install Galaxy collections if needed
ansible-galaxy install -r requirements.yml
```

### 3. Run Tests

**Molecule v6 workflow (correct order):**

```bash
# Scenario 1: localhost (default) - Quick tests on host
molecule prepare -s default
molecule converge -s default

# Scenario 2: ubuntu - Prepare Docker container (runs once, then cached)
molecule prepare -s ubuntu
molecule converge -s ubuntu

# Scenario 3: ubuntu26_ssh - Test roles via SSH to cached container
DEMO_DETAILED=false molecule converge -s ubuntu26_ssh

# Run all tests for all scenarios
molecule test

# Run specific scenarios
molecule test -s default
molecule test -s ubuntu
molecule test -s ubuntu26_ssh
```

### 4. Individual Commands

```bash
# Create containers/scenarios
molecule create -s default    # localhost scenario
molecule create -s ubuntu     # Docker container
molecule create -s ubuntu26_ssh  # uses cached container

# Run converge playbooks
molecule converge -s default
molecule converge -s ubuntu
molecule converge -s ubuntu26_ssh

# Check idempotence
molecule idempotence -s ubuntu26_ssh

# Verify connectivity
molecule verify -s ubuntu26_ssh

# Clean up
molecule destroy -s default
molecule destroy -s ubuntu
molecule destroy -s ubuntu26_ssh
```

## 🐳 Docker Container Setup

### Workflow Overview

The project uses Molecule scenarios with a three-stage progression:

```
1. localhost (default) → Quick tests on your host
2. ubuntu              → Prepares Docker container, caches it
3. ubuntu26_ssh        → Uses cached container via SSH for role testing
```

### Scenario 1: `default` (localhost)

Run on your host machine for quick iteration:

```bash
molecule prepare -s default
molecule converge -s default
molecule idempotence -s default
```

### Scenario 2: `ubuntu` (Docker container preparation)

Creates and configures a Docker container:

```bash
molecule prepare -s ubuntu      # Installs SSH, configures user
molecule converge -s ubuntu     # Runs demo role in container
```

- Runs in Docker with `driver: docker`
- Image: `geerlingguy/docker-ubuntu2604-ansible:latest`
- Prepares the container by installing SSH server, time, and sudo utilities
- Configures the `ubuntu` user with passwordless sudo
- Enables password authentication in SSH
- Starts the SSH service on port 2222
- Container is cached as `ubuntu26-sandbox` for reuse by next scenario

### Scenario 3: `ubuntu26_ssh` (role testing with SSH)

Tests roles from `roles/` directory via SSH to the cached container:

```bash
molecule prepare -s ubuntu26_ssh    # Uses cached container
molecule converge -s ubuntu26_ssh   # Runs demo + ssh_keys roles
```

- Runs on your host with `driver: default` (native Ansible)
- Connects to the **same cached container** (`ubuntu26-sandbox`) via SSH
- Uses container's SSH server on port 2222
- Reads host definitions from `hosts.yml` (bypasses Molecule's cache)
- Uses vault password from `.vault_pass` for SSH authentication
- Runs converge playbook: `demo` + `ssh_keys` roles

### Container Configuration

- **Image:** `geerlingguy/docker-ubuntu2604-ansible:latest`
- **Systemd:** Enabled with PID 1
- **SSH:** Available on port 2222 (configured in `ubuntu` scenario)
- **cgroups:** Host cgroup filesystem mounted for systemd compatibility
- **Volume mount:** `/sys/fs/cgroup:/sys/fs/cgroup:rw` required for systemd

### Required System Setup

Before running the Ubuntu scenario, ensure your host has access to cgroups:

```bash
# Mount cgroups (if not already done)
mount --bind /sys/fs/cgroup /sys/fs/cgroup
mount --rbind /sys/fs/cgroup /sys/fs/cgroup
```

### Environment Variables

| Variable | Description | Default |
|---------|-------------|---------|
| `DEMO_DETAILED` | Enable detailed demo output in `demo` role | `false` |

**Usage examples:**
```bash
# Show detailed facts and output
export DEMO_DETAILED=true
molecule converge -s ubuntu26_ssh

# Disable detailed output (faster)
export DEMO_DETAILED=false
molecule converge -s ubuntu26_ssh
```

## 📁 Project Structure

```
prometheus_observability/
├── molecule/
│   ├── default/                           # Localhost scenario (quick tests)
│   │   ├── molecule.yml                   # Localhost-only config
│   │   └── converge.yml                   # Converge playbook (localhost)
│   ├── ubuntu/                            # Docker container PREPARATION
│   │   ├── molecule.yml                   # Docker container config (prepares container)
│   │   ├── converge.yml                   # Initial converge playbook (cached)
│   │   ├── prepare.yml                    # Container preparation (SSH, sudo config)
│   │   └── _create.yml                    # Create sequence
│   └── ubuntu26_ssh/                      # Role testing scenario (uses cached container)
│       ├── molecule.yml                   # Native Ansible config (driver: default)
│       ├── converge.yml                   # Role converge (demo + ssh_keys)
│       └── hosts.yml                      # Host definitions (SSH config, port 2222)
├── roles/
│   ├── demo/                              # Demo role (runs in container)
│   ├── ssh_verify/                        # Future: SSH verification role
│   └── ssh_keys/                         # Working: SSH key management role
├── group_vars/                            # Shared variables
├── site.yml                               # Site-level playbook
├── molecule.yml                          # Global Molecule config
├── ansible.cfg                           # Ansible configuration
└── README.md
```

## 🔍 What Gets Tested

### localhost target
- Demo role execution on host machine
- System facts gathering
- Ansible capabilities verification
- Conditional task demonstrations
- Command output examples

### ubuntu target (Docker container - preparation stage)
- Container creation with systemd and cgroups
- SSH server installation and configuration
- Ubuntu user setup with passwordless sudo
- Creates cached container: `ubuntu26-sandbox`

### ubuntu26_ssh target (role testing stage)
- **Uses the SAME cached container** from ubuntu target via SSH
- Connects to container's SSH server on port 2222
- Runs converge playbook with `demo` and `ssh_keys` roles
- Validates role idempotence and output
- Demonstrates native Ansible inventory handling (hosts.yml)
- Tests roles from `roles/` directory in cached container

## 📝 Configuration

### ansible.cfg

The project uses a centralized `ansible.cfg` with the following settings:

- **roles_path:** Points to `./roles` directory
- **timeout:** 30 seconds for SSH connections
- **retry_files_enabled:** Yes, for failed command retries
- **host_key_checking:** Disabled (no StrictHostKeyChecking)
- **pipelining:** Enabled for faster execution
- **fact_caching:** Memory caching disabled

### Molecule Configuration

The `molecule.yml` files define:
- **provisioner:** Ansible with custom environment
- **verifier:** Ansible-based verification
- **scenarios:** default (localhost) and ubuntu (Docker)

## 🐍 Automated Scenario Runner

Use the `run_molecule_scenarios.py` script for automated execution:

```bash
# Run all scenarios in correct order
python run_molecule_scenarios.py

# Or run with verbose output
export DEMO_DETAILED=true
python run_molecule_scenarios.py
```

**Features:**
- Runs all scenarios in correct order (default → ubuntu → ubuntu26_ssh)
- Each scenario: `prepare` → `converge`
- Stops immediately if any scenario fails
- Automatic cleanup on failure
- Docker container verification for SSH testing

**The script uses a command array (`SCENARIO_COMMANDS`) that defines all prepare/converge commands in order:**

```python
SCENARIO_COMMANDS = [
    # default scenario
    ("molecule syntax -s default", "Syntax check"),
    ("molecule create -s default", "Create"),
    ("molecule prepare -s default", "Prepare"),
    ("molecule converge -s default", "Converge"),

    # ubuntu scenario
    ("molecule create -s ubuntu", "Create container"),
    ("molecule prepare -s ubuntu", "Prepare container"),
    ("molecule converge -s ubuntu", "Converge"),

    # ubuntu26_ssh scenario
    ("molecule prepare -s ubuntu26_ssh", "Prepare via SSH"),
    ("molecule converge -s ubuntu26_ssh", "Converge via SSH"),
]
```

### Target Details

- **default scenario:** Runs on your host with `driver: default` (no Docker)
- **ubuntu scenario:** Prepares Docker container with `driver: docker` - container cached as `ubuntu26-sandbox`
- **ubuntu26_ssh scenario:** Uses cached container via SSH with `driver: default` (native Ansible)
- **DEMO_DETAILED:** Set to `true` for verbose output, `false` for minimal output
- **cgroupns_mode:** Set to `host` for systemd compatibility
- **Volume mount:** `/sys/fs/cgroup:/sys/fs/cgroup:rw` required for systemd
- **Molecule v6:** Uses native Ansible architecture with separate `hosts.yml` inventory
- **roles_path:** Ansible reads roles from `./roles` directory (defined in `ansible.cfg`)

## ⚠️ Important Notes

### Workflow Order

**Manual execution - Run scenarios in this order:**
1. `molecule prepare -s default` + `molecule converge -s default` (localhost tests)
2. `molecule prepare -s ubuntu` + `molecule converge -s ubuntu` (prepares Docker container)
3. `molecule prepare -s ubuntu26_ssh` + `molecule converge -s ubuntu26_ssh` (tests roles via SSH)

**Using the automated script:**
```bash
python run_molecule_scenarios.py  # Runs all in order, stops on failure
```

### Target Details

- **default scenario:** Runs on your host with `driver: default` (no Docker)
- **ubuntu scenario:** Prepares Docker container with `driver: docker` - container cached as `ubuntu26-sandbox`
- **ubuntu26_ssh scenario:** Uses cached container via SSH with `driver: default` (native Ansible)
- **DEMO_DETAILED:** Set to `true` for verbose output, `false` for minimal output
- **cgroupns_mode:** Set to `host` for systemd compatibility
- **Volume mount:** `/sys/fs/cgroup:/sys/fs/cgroup:rw` required for systemd
- **Molecule v6:** Uses native Ansible architecture with separate `hosts.yml` inventory
- **roles_path:** Ansible reads roles from `./roles` directory (defined in `ansible.cfg`)

## 🔜 Future Work

The following items are planned for future development:

1. **ssh_verify:** SSH connectivity verification commands (placeholder role)
2. **site.yml:** Site-level playbook combining multiple roles (demo, ssh_keys)
3. **Prometheus integration:** Metrics collection and visualization for monitored services
4. **Parallel execution:** Run independent scenarios in parallel where possible

**Current status:**
- `ssh_keys` role is fully functional and handles SSH key generation/deployment
- Both `ssh_keys` and `ssh_verify` roles are tested via the `ubuntu26_ssh` scenario
- Automated scenario runner (`run_molecule_scenarios.py`) is fully functional
