"""
Dead Man's Switch — Interactive CLI
Auto-triggers on launch if the deadline has passed.
"""

from __future__ import annotations

import getpass
import os
import sys
import time

from config_manager import config_exists, default_config, load_config, save_config
from delivery import send_messages, test_smtp
from scheduler import checkin, format_countdown, is_triggered, new_deadline

if sys.platform == "win32":
    os.system("")

G    = "\033[92m"
DG   = "\033[32m"
Y    = "\033[93m"
R    = "\033[91m"
C    = "\033[96m"
W    = "\033[97m"
DIM  = "\033[2m"
RST  = "\033[0m"
BOLD = "\033[1m"

_BANNER = f"""{BOLD}{G}
  ██████╗ ███████╗ █████╗ ██████╗
  ██╔══██╗██╔════╝██╔══██╗██╔══██╗
  ██║  ██║█████╗  ███████║██║  ██║
  ██║  ██║██╔══╝  ██╔══██║██║  ██║
  ██████╔╝███████╗██║  ██║██████╔╝
  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝{RST}
{BOLD}{G}
  ███╗   ███╗ █████╗ ███╗   ██╗    ███████╗    ███████╗██╗    ██╗██╗████████╗ ██████╗██╗  ██╗
  ████╗ ████║██╔══██╗████╗  ██║    ██╔════╝    ██╔════╝██║    ██║██║╚══██╔══╝██╔════╝██║  ██║
  ██╔████╔██║███████║██╔██╗ ██║    ███████╗    ███████╗██║ █╗ ██║██║   ██║   ██║     ███████║
  ██║╚██╔╝██║██╔══██║██║╚██╗██║    ╚════██║    ╚════██║██║███╗██║██║   ██║   ██║     ██╔══██║
  ██║ ╚═╝ ██║██║  ██║██║ ╚████║    ███████║    ███████║╚███╔███╔╝██║   ██║   ╚██████╗██║  ██║
  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚══════╝    ╚══════╝ ╚══╝╚══╝ ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝{RST}

{BOLD}{G}  ╔══════════════════════════════════════════════════════════════════════╗
  ║   ⚰️   CODED BY BARACK OS  ·  If I disappear, the truth gets out   ⚰️   ║
  ╚══════════════════════════════════════════════════════════════════════╝{RST}
"""


def _clear() -> None:
    os.system("cls" if sys.platform == "win32" else "clear")


def _log(level: str, msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    palette = {"INFO": C, "OK": G, "WARN": Y, "ERR": R, "PROC": DG}
    col = palette.get(level, W)
    print(f"  {DIM}[{ts}]{RST} {BOLD}{col}[{level:4s}]{RST} {msg}")


def _hr(width: int = 68) -> None:
    print(f"  {DG}{'─' * width}{RST}")


def _prompt(label: str, default: str = "") -> str:
    hint = f" {DIM}[{default}]{RST}" if default else ""
    try:
        raw = input(f"  {G}❯{RST} {W}{label}{hint}: {RST}").strip()
    except EOFError:
        print()
        return default
    return raw if raw else default


def _prompt_password(label: str = "Mot de passe maître") -> str:
    try:
        return getpass.getpass(f"  {G}❯{RST} {W}{label}: {RST}")
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _pause() -> None:
    try:
        input(f"\n  {DIM}Appuyez sur ENTRÉE pour continuer…{RST}")
    except (KeyboardInterrupt, EOFError):
        pass


def _show_banner() -> None:
    _clear()
    print(_BANNER)


def _wizard(password: str) -> dict:
    """First-launch setup wizard."""
    _show_banner()
    print(f"  {BOLD}{Y}[ PREMIER LANCEMENT — CONFIGURATION ]{RST}\n")
    _hr()

    cfg = default_config()

    interval_str = _prompt("Intervalle de check-in en jours", "7")
    try:
        cfg["interval_days"] = max(1, int(interval_str))
    except ValueError:
        cfg["interval_days"] = 7

    print(f"\n  {BOLD}{C}Configuration SMTP (pour l'envoi automatique d'emails){RST}")
    _hr()
    cfg["smtp"]["host"]     = _prompt("Serveur SMTP", "smtp.gmail.com")
    try:
        cfg["smtp"]["port"] = int(_prompt("Port", "587"))
    except ValueError:
        cfg["smtp"]["port"] = 587
    cfg["smtp"]["user"]     = _prompt("Email expéditeur")
    cfg["smtp"]["password"] = _prompt_password("Mot de passe email / App Password")

    cfg["deadline"] = new_deadline(cfg["interval_days"])
    save_config(cfg, password)

    _log("OK", f"Vault créé. Deadline dans {cfg['interval_days']} jours.")
    _log("INFO", "Ajoutez des destinataires et des messages depuis le menu.")
    _pause()
    return cfg


def _flow_checkin(cfg: dict, password: str) -> dict:
    _show_banner()
    print(f"  {BOLD}{G}[ CHECK-IN ]{RST}\n")
    _hr()
    cfg = checkin(cfg)
    save_config(cfg, password)
    _log("OK", "Timer réinitialisé.")
    _log("INFO", f"Prochain deadline: {cfg['deadline']}")
    _log("INFO", f"Temps restant: {format_countdown(cfg['deadline'])}")
    _pause()
    return cfg


def _flow_add_recipient(cfg: dict, password: str) -> dict:
    _show_banner()
    print(f"  {BOLD}{G}[ AJOUTER UN DESTINATAIRE ]{RST}\n")
    _hr()
    name  = _prompt("Nom")
    email = _prompt("Email")
    if not name or not email:
        _log("ERR", "Nom et email requis.")
        _pause()
        return cfg
    cfg["recipients"].append({"name": name, "email": email})
    save_config(cfg, password)
    _log("OK", f"Destinataire ajouté: {name} <{email}>")
    _log("INFO", f"Total destinataires: {len(cfg['recipients'])}")
    _pause()
    return cfg


def _flow_add_message(cfg: dict, password: str) -> dict:
    _show_banner()
    print(f"  {BOLD}{G}[ AJOUTER UN MESSAGE ]{RST}\n")
    _hr()
    subject = _prompt("Sujet")
    print(f"  {W}Corps du message (terminez avec une ligne contenant uniquement 'FIN'):{RST}")
    lines = []
    try:
        while True:
            line = input(f"  {DIM}>{RST} ")
            if line.strip().upper() == "FIN":
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        pass
    body = "\n".join(lines)
    if not subject or not body:
        _log("ERR", "Sujet et corps requis.")
        _pause()
        return cfg
    cfg["messages"].append({"subject": subject, "body": body})
    save_config(cfg, password)
    _log("OK", f"Message ajouté: {subject!r}")
    _log("INFO", f"Total messages: {len(cfg['messages'])}")
    _pause()
    return cfg


def _flow_smtp(cfg: dict, password: str) -> dict:
    _show_banner()
    print(f"  {BOLD}{G}[ CONFIGURER SMTP ]{RST}\n")
    _hr()
    cfg["smtp"]["host"] = _prompt("Serveur SMTP", cfg["smtp"].get("host", "smtp.gmail.com"))
    try:
        cfg["smtp"]["port"] = int(_prompt("Port", str(cfg["smtp"].get("port", 587))))
    except ValueError:
        cfg["smtp"]["port"] = 587
    cfg["smtp"]["user"] = _prompt("Email expéditeur", cfg["smtp"].get("user", ""))
    new_pwd = _prompt_password("Mot de passe / App Password (laisser vide = conserver l'actuel)")
    if new_pwd:
        cfg["smtp"]["password"] = new_pwd
    save_config(cfg, password)
    _log("OK", "SMTP mis à jour.")
    _pause()
    return cfg


def _flow_status(cfg: dict) -> None:
    _show_banner()
    print(f"  {BOLD}{G}[ STATUT ]{RST}\n")
    _hr()

    countdown = format_countdown(cfg.get("deadline"))
    triggered = is_triggered(cfg.get("deadline"))

    status_col = R if triggered else G
    status_txt = "DÉCLENCHÉ" if triggered else "EN VEILLE"
    print(f"\n  Statut:           {BOLD}{status_col}{status_txt}{RST}")
    print(f"  Temps restant:    {BOLD}{Y}{countdown}{RST}")
    print(f"  Intervalle:       {cfg.get('interval_days', 7)} jours")
    print(f"  Dernier check-in: {cfg.get('last_checkin', 'jamais')}")
    print(f"  Deadline:         {cfg.get('deadline', 'non défini')}")
    print(f"  Destinataires:    {len(cfg.get('recipients', []))}")
    print(f"  Messages:         {len(cfg.get('messages', []))}")

    _hr()
    if cfg.get("recipients"):
        print(f"\n  {BOLD}{C}Destinataires:{RST}")
        for r in cfg["recipients"]:
            print(f"    {DG}•{RST} {r['name']} <{r['email']}>")
    if cfg.get("messages"):
        print(f"\n  {BOLD}{C}Messages:{RST}")
        for m in cfg["messages"]:
            print(f"    {DG}•{RST} {m['subject']}")

    _pause()


def _flow_test(cfg: dict) -> None:
    _show_banner()
    print(f"  {BOLD}{G}[ TEST D'ENVOI ]{RST}\n")
    _hr()
    _log("PROC", "Envoi d'un email de test à votre propre adresse…")
    errors = test_smtp(cfg)
    if not errors:
        _log("OK", "Email de test envoyé avec succès.")
    else:
        for err in errors:
            _log("ERR", err)
    _pause()


def _auto_trigger(cfg: dict, password: str) -> None:
    """Called automatically if the deadline has passed. Sends all messages and exits."""
    _show_banner()
    print(f"  {BOLD}{R}[ DÉCLENCHEMENT AUTOMATIQUE ]{RST}\n")
    _hr()
    _log("WARN", "Le délai de check-in est dépassé.")
    _log("PROC", f"Envoi à {len(cfg.get('recipients', []))} destinataire(s)…")
    print()

    errors = send_messages(cfg)
    if not errors:
        _log("OK", "Tous les messages ont été envoyés.")
    else:
        for err in errors:
            _log("ERR", err)

    # Reset deadline so the next launch shows the menu instead of re-triggering.
    try:
        updated = checkin(cfg)
        save_config(updated, password)
        _log("INFO", f"Prochaine deadline réinitialisée: {updated['deadline']}")
    except Exception as exc:
        _log("WARN", f"Impossible de réinitialiser le timer: {exc}")

    _hr()
    print(f"\n  {DIM}  Relancez l'application pour faire un check-in et réactiver le switch.{RST}\n")
    sys.exit(1 if errors else 0)


def _print_menu(cfg: dict) -> None:
    countdown = format_countdown(cfg.get("deadline"))
    triggered = is_triggered(cfg.get("deadline"))
    countdown_col = R if triggered else G

    print(f"  {BOLD}{W}{'━' * 66}{RST}")
    print(f"  {BOLD}{C}    MENU PRINCIPAL{RST}  {DIM}│{RST}  "
          f"Deadline: {BOLD}{countdown_col}{countdown}{RST}")
    print(f"  {BOLD}{W}{'━' * 66}{RST}\n")
    print(f"    {BOLD}{Y}1){RST}  {G}✓{RST}  Check in (réinitialiser le timer)")
    print(f"    {BOLD}{Y}2){RST}  {G}+{RST}  Ajouter un destinataire")
    print(f"    {BOLD}{Y}3){RST}  {G}+{RST}  Ajouter un message")
    print(f"    {BOLD}{Y}4){RST}  {C}⚙{RST}  Configurer SMTP")
    print(f"    {BOLD}{Y}5){RST}  {C}ℹ{RST}  Voir le statut")
    print(f"    {BOLD}{Y}6){RST}  {Y}✉{RST}  Tester l'envoi")
    print(f"    {BOLD}{Y}7){RST}  {R}✕{RST}  Quitter")
    print()


def main() -> None:
    _show_banner()

    if not config_exists():
        print(f"  {BOLD}{Y}Bienvenue — aucun vault détecté.{RST}")
        print(f"  {DIM}Choisissez un mot de passe maître pour sécuriser votre configuration.{RST}\n")
        password = _prompt_password("Nouveau mot de passe maître")
        confirm  = _prompt_password("Confirmer le mot de passe")
        if password != confirm or not password:
            print(f"\n  {R}Mots de passe non concordants. Abandon.{RST}\n")
            sys.exit(1)
        cfg = _wizard(password)
    else:
        password = _prompt_password()
        if not password:
            sys.exit(0)
        try:
            cfg = load_config(password)
        except ValueError:
            print(f"\n  {BOLD}{R}Mot de passe incorrect ou vault corrompu.{RST}\n")
            sys.exit(1)
        except OSError as exc:
            print(f"\n  {BOLD}{R}Impossible de lire le vault: {exc}{RST}\n")
            sys.exit(1)

    try:
        triggered = is_triggered(cfg.get("deadline"))
    except ValueError as exc:
        print(f"\n  {BOLD}{R}Deadline corrompue dans le vault: {exc}{RST}")
        print(f"  {DIM}Faites un check-in manuel pour réinitialiser.{RST}\n")
        triggered = False

    if triggered:
        _auto_trigger(cfg, password)

    handlers = {
        "1": lambda: _flow_checkin(cfg, password),
        "2": lambda: _flow_add_recipient(cfg, password),
        "3": lambda: _flow_add_message(cfg, password),
        "4": lambda: _flow_smtp(cfg, password),
        "5": lambda: (_flow_status(cfg), cfg)[1],
        "6": lambda: (_flow_test(cfg), cfg)[1],
    }

    while True:
        _show_banner()
        _print_menu(cfg)

        try:
            choice = _prompt("Votre choix (1-7)").strip()
        except KeyboardInterrupt:
            choice = "7"

        if choice == "7":
            _clear()
            print(f"\n  {BOLD}{G}Dead Man's Switch — Arrêt propre.{RST}\n")
            sys.exit(0)

        handler = handlers.get(choice)
        if handler is None:
            _log("WARN", "Option invalide — saisissez 1 à 7.")
            time.sleep(1.0)
            continue

        try:
            result = handler()
            if isinstance(result, dict):
                cfg = result
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
