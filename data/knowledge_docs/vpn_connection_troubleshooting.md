---
article_id: KB-NET-001
title: Troubleshoot a corporate VPN connection
category: Network
sub_category: VPN
tags: [vpn, remote-access, network]
source_file: vpn_connection_troubleshooting.md
content_status: demo_example
---

# Troubleshoot a corporate VPN connection

Use these checks when the approved corporate VPN client will not connect. Follow your organization's VPN and security policies; these general steps do not replace them.

## Steps

1. Confirm the device has an internet connection before starting the VPN. If possible, test a normal approved website.
2. Confirm the device date and time are correct. Authentication can fail when the clock is substantially out of sync.
3. Open the approved VPN client and sign in with the corporate account. Complete the expected multifactor authentication prompt only when you initiated the sign-in.
4. Read the exact client error and note when it occurred. Close and reopen the client once, then retry.
5. Check for client updates through the organization's software catalog or IT instructions. Do not download a VPN client from an unofficial site.
6. If permitted, restart the device and try again on a trusted network.

## Security reminders

Never share your password or one-time codes with support staff. Do not disable endpoint protection, bypass certificate warnings, or approve an unexpected MFA request to make the connection work.

## Escalate to IT

Contact IT if the issue continues, affects multiple users, follows a password or MFA change, or displays a certificate, account-lock, or policy error. Include the error text, time, device operating system, VPN client version, and network type. Do not include passwords, recovery codes, or session tokens.
