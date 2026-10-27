"""Depuis la racine du projet : python -m scripts.purge_security_alerts_step90 [--apply]."""
import argparse
import json
import os
import sys
from app.security_alert_retention_step90 import purge


def main(argv=None):
    parser = argparse.ArgumentParser(description='Purge des alertes de sécurité SQL; simulation par défaut')
    parser.add_argument('--apply', action='store_true', help='Supprimer réellement un lot')
    parser.add_argument('--batch-size', type=int, default=500)
    args = parser.parse_args(argv)
    if os.getenv('BOUKOULOU_SECURITY_ALERT_STORAGE', '').strip().lower() != 'database':
        parser.error('Activer explicitement BOUKOULOU_SECURITY_ALERT_STORAGE=database')
    try:
        result = purge(dry_run=not args.apply, batch_size=args.batch_size)
    except (ValueError, Exception) as exc:
        print(f'Purge impossible : {type(exc).__name__}', file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
