# Configuration file for Fail2Ban
# Default settings for all jails
[DEFAULT]
# Basic security settings
ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24  # Trusted IPs to ignore
bantime = 10m  # Ban duration
findtime = 10m  # Time window for counting attempts
maxretry = 5  # Max failed attempts before ban

# Global enable flag
enabled = true

# Email notification settings
destemail = admin@example.com
sender = fail2ban@example.com
action = %(action_mwl)s

# SSH-specific jail configuration
[sshd]
enabled = true  # Enable SSH protection
bantime = 1h  # SSH-specific ban duration
maxretry = 3  # SSH-specific retry limit