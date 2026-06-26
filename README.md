# Dead Man's Switch

**An offline, encrypted Dead Man's Switch CLI. If you stop checking in, it automatically sends your pre-written messages to your chosen recipients.**

Built for journalists, activists, lawyers, and anyone who needs a digital safety net that fires even if they can't trigger it themselves.

![CI](https://github.com/Barack-zero-to-one/deadman-switch/actions/workflows/ci.yml/badge.svg)

---

## What It Does

You configure:
- A **check-in interval** (e.g. every 7 days)
- One or more **recipients** (name + email)
- One or more **messages** (subject + body)
- Your **SMTP credentials** (Gmail, Outlook, any provider)

Every time you launch the app and check in, the timer resets. If you miss a check-in deadline — the app fires automatically the next time it launches, sends all your messages to all recipients, and resets the timer.

**Zero cloud. Zero account. Zero telemetry. Everything runs on your machine.**

---

## Security Architecture

| Layer | Mechanism |
|---|---|
| Vault encryption | AES-256-GCM |
| Key derivation | PBKDF2HMAC-SHA256, 480,000 iterations |
| Key size | 256 bits |
| Nonce | 96-bit random per encryption |
| Auth tag | 128-bit GCM tag (tamper detection) |
| Atomic write | tempfile + os.replace (no partial writes) |
| Password guard | Empty password raises ValueError before key derivation |

The vault lives at `~/.deadman/vault.enc`. Without the master password, it is computationally indistinguishable from random bytes.

---

## Installation

```bash
git clone https://github.com/Barack-zero-to-one/deadman-switch
cd deadman-switch
pip install -r requirements.txt
python main.py
```

Python 3.11 or later required.

---

## First Launch

On first launch, a setup wizard runs:

```
  Bienvenue — aucun vault détecté.
  ❯ Nouveau mot de passe maître:
  ❯ Confirmer le mot de passe:

  ❯ Intervalle de check-in en jours [7]:
  ❯ Serveur SMTP [smtp.gmail.com]:
  ❯ Port [587]:
  ❯ Email expéditeur:
  ❯ Mot de passe email / App Password:
```

For Gmail, use an [App Password](https://myaccount.google.com/apppasswords) rather than your account password.

---

## Menu

```
  1)  Check in (réinitialiser le timer)
  2)  Ajouter un destinataire
  3)  Ajouter un message
  4)  Configurer SMTP
  5)  Voir le statut
  6)  Tester l'envoi
  7)  Quitter
```

The menu header always shows the current countdown:

```
  MENU PRINCIPAL  │  Deadline: 6j 14h 32m
```

---

## Auto-Trigger

If you launch the app after the deadline has passed:

```
  [ DÉCLENCHEMENT AUTOMATIQUE ]

  [12:34:56] [WARN] Le délai de check-in est dépassé.
  [12:34:56] [PROC] Envoi à 2 destinataire(s)...
  [12:34:56] [OK  ] Tous les messages ont été envoyés.
  [12:34:56] [INFO] Prochaine deadline réinitialisée: 2026-07-03T12:34:56
```

After firing, the timer is reset so the next launch shows the menu. Exit code is 0 on success, 1 if any delivery failed.

---

## File Structure

```
deadman-switch/
    crypto.py           AES-256-GCM + PBKDF2 key derivation
    config_manager.py   Encrypted vault read/write (atomic)
    scheduler.py        Deadline logic and countdown formatting
    delivery.py         SMTP email delivery (stdlib only)
    main.py             Interactive ANSI CLI
    requirements.txt    cryptography>=41.0.0
```

---

## Use Cases

- **Journalists**: Pre-write a story. If you disappear, it publishes automatically.
- **Activists**: Store location of evidence. If you are detained, it reaches your lawyer.
- **Individuals**: Send personal messages to family if you become incapacitated.
- **Developers**: Auto-revoke access or trigger an alert if your systems go silent.

---

*CODED BY BARACK OS — If I disappear, the truth gets out.*
