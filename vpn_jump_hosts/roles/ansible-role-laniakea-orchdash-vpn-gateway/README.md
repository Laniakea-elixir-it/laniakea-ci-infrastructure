# ansible-role-orchdash-vpn-gateway

Configura una seconda istanza OpenVPN sul bastion (`server_orchdash.conf`) con autenticazione solo a certificato, e il file `.ovpn` corrispondente sulla dashboard.

Le variabili usano gli **stessi nomi** di `ansible-role-openvpn` (Laniakea) — basta cambiare `openvpn_port` e `openvpn_server_subnet` per non entrare in conflitto con l'istanza PAM esistente.

## Requisiti

- OpenVPN già installato su bastion e dashboard
- easy-rsa già configurato e CA inizializzata sul bastion in `{{ openvpn_easyrsa_dir }}`
- `tc.key` già presente sul bastion in `{{ openvpn_server_dir }}/tc.key`

## Variabili principali

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `openvpn_public_ip` | `""` | **REQUIRED** IP pubblico del bastion |
| `openvpn_tenant_network` | `""` | **REQUIRED** Rete privata delle VM |
| `openvpn_tenant_iface` | `""` | **REQUIRED** Interfaccia verso la rete privata |
| `openvpn_tenant_prefix` | `""` | **REQUIRED** Prefisso rete privata |
| `openvpn_bastion_host` | `""` | **REQUIRED** Nome host bastion nell'inventario |
| `openvpn_port` | `1195` | Porta (diversa da 1194 dell'istanza PAM) |
| `openvpn_protocol` | `tcp` | Protocollo (tcp/udp) |
| `openvpn_server_subnet` | `10.9.0.0` | Subnet VPN (diversa da 10.8.0.0 dell'istanza PAM) |
| `openvpn_client_name` | `dashboard` | Nome del certificato client |
| `openvpn_push_routes` | `[]` | Subnet aggiuntive da pushare (oltre alla tenant) |
| `easyrsa_cert_days` | `3650` | Validità certificato client in giorni |

## Utilizzo

```yaml
# inventario
[bastion]
vpn-bastion ansible_host=212.189.202.200

[dashboard]
laniakea-dashboard ansible_host=212.189.202.181

# playbook.yml
- hosts: dashboard
  vars:
    openvpn_bastion_host: vpn-bastion
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

## Note

- Il ruolo gira sulla dashboard e delega i task del bastion tramite `delegate_to: "{{ openvpn_bastion_host }}"`.
- I certificati vengono letti dal bastion via `slurp` e iniettati inline nel `.ovpn` — nessun file temporaneo.
- La generazione del certificato client è idempotente: se esiste già viene saltata.
- Il file `.ovpn` viene salvato con permessi `0600`.
