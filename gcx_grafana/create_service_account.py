#! /usr/bin/env python3
import os
import subprocess
import sys
import yaml
from ansible import constants as C
from ansible.parsing.vault import VaultLib, VaultSecret



def get_git_root():
    """ Returns absolute <repo_root> path"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("[ERROR] repo_root could not be found!, cannot proceed", file=sys.stderr)
        sys.exit(1)

VAULT_PASSWORD = os.environ.get("ANSIBLE_VAULT_PASS")
VAULT_FILE = f"{get_git_root()}/ansible_template/inventory/host_vars/zeus-lat/grafana_vault.yml"


def load_vault_pass(): 
    global VAULT_PASSWORD

    if not VAULT_PASSWORD:
        print("env ANSIBLE_VAULT_PASS not set: trying file from ANSIBLE_VAULT_PASSWORD_FILE")
        PASSWORD_FILE_PATH = os.environ.get("ANSIBLE_VAULT_PASSWORD_FILE")
        if PASSWORD_FILE_PATH and os.path.exists(PASSWORD_FILE_PATH):
            with open(PASSWORD_FILE_PATH, "r", encoding="utf-8") as f:
                VAULT_PASSWORD = f.read().strip()
                print("Successfully loaded vault password from file.")
                return VAULT_PASSWORD
        else:
            print("Warning: ANSIBLE_VAULT_PASSWORD_FILE path does not exist or is not set.", file=sys.stderr)
    else:
        print("Successfully loaded vault password from environment variable.")
        return VAULT_PASSWORD

    if not VAULT_PASSWORD:
        print("Error: No password for the vault could be loaded.", file=sys.stderr)
        sys.exit(1) # Bricht das Skript hier direkt ab, anstatt mit Fehlern weiterzugeben

def load_vault_variables(filepath, password):
    """Entschlüsselt die Vault-Datei direkt im RAM."""
    vault = VaultLib([(C.DEFAULT_VAULT_ID_MATCH, VaultSecret(password.encode()))])

    with open(filepath, "rb") as f:
        decrypted_bytes = vault.decrypt(f.read())

    return yaml.safe_load(decrypted_bytes)

def create_service_account(admin_user: str = "admin", 
                           admin_password: str = "admin", 
                           grafana_url = "http://localhost:3000",
                           service_account_name: str = "gcx-provisioning"):
    import requests
    response = requests.post(
        f"{grafana_url}/api/serviceaccounts",
        auth=(admin_user, admin_password),
        headers={
            "Content-Type": "application/json"
        },
        json={
            "name": service_account_name,
            "role": "Admin"
        },
    )
    response.raise_for_status()

    service_account = response.json()
    print(f"Service Account created: {service_account}")
    service_account_id = service_account["id"]
    # API Call to create a token
    response = requests.post(
        f"{grafana_url}/api/serviceaccounts/{service_account_id}/tokens",
        auth=(admin_user, admin_password),
        headers={
            "Content-Type": "application/json"
        },
        json={
            "name": "gcx-token"
        },
    )
    response.raise_for_status()
    token = response.json()["key"]
    print(f"Token: {token}")
    return token

def write_gcx_config_file(server, token):
    config_template = f'''version: 1
stacks:
  default:
    grafana:
      server: {server}
      token: {token}
      auth-method: token
      org-id: 1
contexts:
  default:
    stack: default
current-context: default
'''
    from pathlib import Path

    config_path = Path("~/.config/gcx/config.yaml").expanduser()
    # Wathc out: this overwrites any existing configs
    # If a second configuration is required:
    # create a second instance "manually" by running gcx login
    # read the file format of ~/.config/gcx/config.yaml 
    # adapt the string to your needs (or even better)
    # provide an argument whether the script should overwrite or add the new configuration
    with open(config_path , mode="w") as config_file:
        config_file.write(config_template)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Helper Script for interacting with the Grafana API and vaults")
    parser.add_argument("--url", "-u", default="http://localhost:3000", help="sets the url for grafana")

    args = parser.parse_args()
    password = load_vault_pass()
    try:
        secrets = load_vault_variables(VAULT_FILE, password)
        if secrets and isinstance(secrets, dict):
            # count the keys
            print(f"[SUCCESS] Vault '{VAULT_FILE}' is opened and decrypted")
            print(f"[INFO] {len(secrets)} Variables are available")

            token = create_service_account(secrets["vault_grafana_admin_user"],
                                   secrets["vault_grafana_admin_password"])

            write_gcx_config_file(args.url, token=token)
        else:
            print(f"[ERROR] required variables have not been found in {VAULT_FILE}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Eception {e}, while processing vault at: {VAULT_FILE}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()