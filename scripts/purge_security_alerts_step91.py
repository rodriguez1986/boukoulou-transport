"""Commande à déclencher par un planificateur externe (cron ou timer systemd)."""
import argparse
import json
import sys
from app.security_alert_automation_step91 import run_scheduled


def main(argv=None):
    parser = argparse.ArgumentParser(description='Purge planifiée sécurisée des alertes SQL (simulation par défaut)')
    parser.add_argument('--apply', action='store_true', help='Autoriser une suppression réelle, si activée par configuration')
    parser.add_argument('--batch-size', type=int, default=500)
    args = parser.parse_args(argv)
    try:
        report = run_scheduled(apply=args.apply, batch_size=args.batch_size)
    except Exception as exc:
        print(f'Purge planifiée refusée : {type(exc).__name__}', file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
