# ansible-role-orchdash-vpn-gateway

Configures a second OpenVPN instance on the bastion (`server_orchdash.conf`) with certificate-only authentication, and the corresponding `.ovpn` file on the dashboard.

The variables use the **same names** as `ansible-role-openvpn` (Laniakea) — you just need to change `openvpn_port` and `openvpn_server_subnet` to avoid conflicts with the existing PAM instance.

## Requirements

- OpenVPN already installed on both the bastion and the dashboard
- `easy-rsa` already configured and the CA initialized on the bastion in `{{ openvpn_easyrsa_dir }}`
- `tc.key` already present on the bastion in `{{ openvpn_server_dir }}/tc.key`

## Main Variables

| Variable | Default | Description |
|-----------|---------|-------------|
| `openvpn_public_ip` | `""` | **REQUIRED** Public IP of the bastion |
| `openvpn_tenant_network` | `""` | **REQUIRED** Private network of the VMs |
| `openvpn_tenant_iface` | `""` | **REQUIRED** Interface connected to the private network |
| `openvpn_tenant_prefix` | `""` | **REQUIRED** Private network prefix |
| `openvpn_server_host` | `""` | **REQUIRED** Bastion host name in the inventory |
| `openvpn_port` | `1195` | Port (must be different from the PAM instance's 1194) |
| `openvpn_protocol` | `tcp` | Protocol (tcp/udp) |
| `openvpn_server_subnet` | `10.9.0.0` | VPN Subnet (must be different from the PAM instance's 10.8.0.0) |
| `openvpn_client_name` | `dashboard` | Name of the client certificate |
| `openvpn_push_routes` | `[]` | Additional subnets to push (besides the tenant network) |
| `easyrsa_cert_days` | `3650` | Client certificate validity in days |

## Usage

```yaml
# inventory
[bastion]
vpn-bastion ansible_host=212.189.202.200

[dashboard]
laniakea-dashboard ansible_host=212.189.202.181

# playbook.yml
- hosts: dashboard
  vars:
    openvpn_server_host: vpn-bastion
    openvpn_public_ip: "212.189.202.200"
    openvpn_tenant_network: "172.18.7.0"
    openvpn_tenant_iface: "ens4"
    openvpn_tenant_prefix: "24"
    # openvpn_push_routes:
    #   - network: "192.168.100.0"
    #     netmask: "255.255.255.0"
  roles:
    - ansible-role-orchdash-vpn-gateway
```

## Notes

- The role runs on the dashboard and delegates bastion tasks via `delegate_to: "{{ openvpn_server_host }}"`.
- Certificates are read from the bastion via `slurp` and injected inline into the `.ovpn` file — no temporary files are used.
- Client certificate generation is idempotent: if it already exists, the generation step is skipped.
- The `.ovpn` file is saved with `0600` permissions.
