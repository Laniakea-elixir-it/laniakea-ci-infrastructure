#!/usr/bin/expect -f
set timeout -1
set secret [lindex $argv 0]
spawn oidc-add usegalaxy-it.jenkins.bot
match_max 100000
expect -exact "\[36mEnter decryption password for account config 'usegalaxy-it.jenkins.bot'\[0m\[36m: \[0m"
send -- "$secret\r"
expect eof
