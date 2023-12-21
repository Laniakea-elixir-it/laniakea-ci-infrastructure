#!/usr/bin/expect -f
set timeout -1
set secret [lindex $argv 0]
spawn oidc-add iam-recas
match_max 100000
expect -exact "\[36mEnter decryption password for account config 'iam-recas'\[0m\[36m: \[0m"
send -- "$secret\r"
expect eof
