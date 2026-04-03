# ansible-role-wireguard

Configures WireGuard between all dashboard VMs and a single bastion.
Run the playbook once per bastion passing only `bastion_host`.

Each bastion gets a `wg0` interface with one `[Peer]` per dashboard.
Each dashboard gets one dedicated WireGuard interface per bastion (e.g. `wg0`, `wg01`, ...).

Keys are generated automatically on each node — only public keys are exchanged via Ansible facts.

## Requirements

- Ubuntu 22.04+ (WireGuard in kernel >= 5.6)
- No external Python dependencies (no `netaddr`)

## Inventory structure

```ini
[bastion1]
bastion1 ansible_host=0.1.2.3 ansible_user=root

[bastion2]
bastion2  ansible_host=4.5.6.7 ansible_user=root

[laniakea-dashboard]
laniakea-dashboard-1 ansible_host=8.9.10.11 ansible_user=root
laniakea-dashboard-2 ansible_host=12.13.14.15  ansible_user=root
```

## group_vars

All bastion definitions in one file, easy to keep track of:

```yaml
# inventory/group_vars/laniakea-dashboard/wireguard.yml

wireguard_bastions:
  bastion1:
    iface_dashboard: wg0
    bastion_private_iface: ens4
    wg_subnet: "10.10.0.0/24"
    private_network: "192.168.10.0"
    private_prefix: 24

  bastion2:
    iface_dashboard: wg1
    bastion_private_iface: ens4
    wg_subnet: "10.10.1.0/24"
    private_network: "192.168.7.0"
    private_prefix: 24
```

## host_vars

Each dashboard declares its WireGuard IP for each bastion:

```yaml
# inventory/host_vars/laniakea-dashboard-1/wireguard.yml
wireguard_wg_ip:
  wg0: "10.10.0.2"
  wg1: "10.10.1.2"

# inventory/host_vars/laniakea-dashboard-2/wireguard.yml
wireguard_wg_ip:
  wg0: "10.10.0.3"
  wg1: "10.10.1.3"
```

## Playbook

```yaml
# wireguard.yml
- hosts: laniakea-dashboard
  vars:
    bastion_host: bastion1
    wireguard_peer: "{{ wireguard_bastions[bastion_host] | combine({'bastion_host': bastion_host}) }}"
  roles:
    - ansible-role-wireguard
```

Run per bastion — only `bastion_host` changes:

```bash
ansible-playbook -i inventory/hosts wireguard.yml 
```

## Adding a new bastion

1. Add it to the inventory
2. Add its entry to `wireguard_bastions` in `group_vars/laniakea-dashboard/wireguard.yml`
3. Add its IP to `wireguard_wg_ip` in each dashboard's `host_vars`
4. Run the playbook with the new `bastion_host`

## IP assignment

| Host            | wg_subnet    | WireGuard IP      |
|-----------------|--------------|-------------------|
| bastion         | 10.10.X.0/24 | 10.10.X.1         |
| dashboard-dev   | 10.10.X.0/24 | defined in host_vars |
| dashboard-prod  | 10.10.X.0/24 | defined in host_vars |

## Variables

| Variable                  | Where      | Description                                             |
|---------------------------|------------|---------------------------------------------------------|
| `bastion_host`            | playbook / `-e` | Inventory hostname of the bastion to configure    |
| `wireguard_bastions`      | group_vars | Dict of all known bastions and their config             |
| `wireguard_wg_ip`         | host_vars  | Per-dashboard WireGuard IPs, keyed by `iface_dashboard` |
| `wireguard_port`          | defaults   | WireGuard UDP listen port (default: `51820`)            |
| `wireguard_config_dir`    | defaults   | Config and key directory (default: `/etc/wireguard`)    |
| `wireguard_dashboard_group` | defaults | Inventory group of dashboards (default: `laniakea-dashboard`) |

