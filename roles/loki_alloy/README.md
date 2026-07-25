# loki_alloy Role

Installs and configures **Grafana Loki** (log server) and **Grafana Alloy** (log agent) for collecting Systemd journal logs.

## Features

- Automated Loki installation with Docker
- Grafana Alloy setup for Systemd journal collection
- Integration test verifying logs flow from Alloy to Loki
- Uses only builtin Ansible modules (no external dependencies beyond `community.docker`)

## Requirements

- Ansible 2.14+
- Docker installed on the target host
- Ubuntu 20.04, 22.04, or 24.04

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `loki_image` | `grafana/loki:latest` | Loki Docker image to use |
| `alloy_image` | `grafana/alloy:latest` | Alloy Docker image to use |
| `loki_container_port` | `3100` | Port Loki exposes |
| `systemd_journal_job` | `systemd-journal` | Label for collected logs |
| `systemd_journal_host` | `inventory_hostname` | Host label value |

## Usage

### Include in site.yml

```yaml
- name: "Phase 3: Install Loki and Alloy logging infrastructure"
  hosts: all
  gather_facts: true
  roles:
    - role: loki_alloy
```

### Run independently

```bash
ansible-playbook -i inventory your_playbook.yml -l localhost --tags loki_alloy
```

## Integration Test

The role includes an automated integration test that:

1. Starts Loki and validates API readiness
2. Starts Alloy to collect Systemd logs
3. Queries Loki API to verify logs are flowing

Check the output for "Success! Systemd logs are flowing successfully into Loki."

## Architecture

```
┌─────────────────────────────────────────────────┐
│               Host System                        │
│                                                 │
│  ┌─────────────┐    ┌─────────────────────────┐ │
│  │  Loki       │◄──►│   Grafana Alloy         │ │
│  │  :3100      │    │   (Systemd Journal)     │ │
│  │  API        │    │                         │ │
│  └─────────────┘    └─────────────────────────┘ │
│         │                     │                 │
│         │                     │                 │
│  ┌─────────────────────────────────────────┐   │
│  │            /var/log/journal             │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## How to Read the Validation Result

When this role is included in your Molecule playbook:

1. Loki starts and is validated via the `/ready` endpoint
2. Alloy starts, accessing the host journal and pushing logs to Loki
3. The `uri` task queries the Loki API with the LogQL query `{job="systemd-journal"}`
4. The `assert` task ensures the list is not empty
5. The `debug` task prints the last 3 real Systemd log lines to the Ansible terminal

Would you like to integrate this combined logging setup directly into your `converge.yml` playbook?
