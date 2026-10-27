# Étape 62 — Isolation des tests de paiement et authentification JWT

## Reconstitution
Tous les fichiers des étapes 1 à 61 sont conservés.

## Correction
- `test_payment_api_step45.py` ne substitue plus `app.security` dans `sys.modules`.
- Le test utilise le vrai routeur et la vraie dépendance `app.security.user`.
- Si `passlib` n'est pas installé, le shim `test_support_step53/passlib` sert exclusivement à permettre l'import des modules pendant les tests ; il ne fournit pas de hachage opérationnel et ne doit jamais être déployé.
- `test_payment_test_isolation_step62.py` ajoute deux vérifications de non-régression sur le module de sécurité et la dépendance JWT du routeur.

## Validation
Commande : `python -m pytest -q`
Résultat local : **520 passed, 12 skipped, 58 warnings**.
Plus besoin d'exclure `test_payment_api_step45.py` ou `test_security_step6.py` pour obtenir une suite verte.

## Limites
- Les 12 tests ignorés dépendent notamment d'installations ou d'environnements non disponibles localement ; ils ne sont pas des validations positives.
- Les avertissements JWT concernent des clés de test trop courtes ; les secrets de production doivent être robustes et fournis par configuration.
- Les tests SQLite ne remplacent pas une validation PostgreSQL et de concurrence réelle.
- Aucun routeur nouveau monté, aucune migration, aucun paiement réel, aucun déploiement de production.
