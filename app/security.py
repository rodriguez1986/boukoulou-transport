import os
import jwt
import hashlib
import hmac

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

# Configuration JWT : clé de test/développement uniquement en l'absence de
# JWT_SECRET. En production, une vraie clé est obligatoire.
from .jwt_config_step63 import get_jwt_secret
SECRET = get_jwt_secret()

# Durée de validité d'un token JWT, exprimée en minutes.
from .jwt_expiry_step71 import get_access_token_minutes
MIN = get_access_token_minutes()

# Gestion du hachage et de la vérification des mots de passe.
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Tolérance bornée pour les écarts d’horloge sur iat/nbf uniquement.
# Ne jamais appliquer de tolérance à exp : expiration stricte.
JWT_CLOCK_SKEW_SECONDS = 5

# Algorithme unique, partagé par l’émetteur et le vérificateur.
JWT_ALGORITHM = "HS256"

# Récupération des tokens transmis avec Authorization: Bearer.
bearer = HTTPBearer(auto_error=False)


def token(u):
    """Génère un token JWT pour un utilisateur authentifié."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(u.id),
            "tv": int(u.token_version),
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=MIN),
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )


def user(
    c: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
):
    """Vérifie le token JWT et récupère l'utilisateur correspondant."""
    # Même réponse pour un Bearer absent, malformé ou d’un autre schéma.
    if c is None or not c.credentials:
        raise HTTPException(status_code=401, detail="Token invalide", headers={"WWW-Authenticate": "Bearer"})
    # Refuser les jetons anciens, malformés ou signés avec une autre clé.
    try:
        claims = jwt.decode(
            c.credentials, SECRET, algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "tv", "exp"],
                     "verify_iat": False, "verify_nbf": False},
        )
        # Les identifiants doivent être des chaînes décimales positives,
        # sans booléens, signes, espaces ou notation alternative.
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject.isascii() or not subject.isdecimal():
            raise ValueError("Identifiant de jeton invalide")
        uid = int(subject)
        if uid <= 0:
            raise ValueError("Identifiant de jeton invalide")
        # PyJWT vérifie exp, mais accepterait aussi des types coercibles.
        if type(claims["exp"]) is not int or claims["exp"] <= 0:
            raise ValueError("Expiration de jeton invalide")
        # Les anciens jetons sans iat/nbf restent compatibles jusqu'à expiration.
        # Si présents, ces champs doivent être des timestamps Unix entiers,
        # sans conversion implicite (booléens, chaînes et flottants refusés).
        for name in ("iat", "nbf"):
            if name in claims:
                value = claims[name]
                if type(value) is not int or value <= 0 or value > claims["exp"]:
                    raise ValueError("Date JWT invalide")
        # Une faible avance de l’horloge émettrice est tolérée uniquement
        # pour iat et nbf. PyJWT conserve sa vérification stricte de exp.
        now_seconds = int(datetime.now(timezone.utc).timestamp())
        for name in ("iat", "nbf"):
            if name in claims and claims[name] > now_seconds + JWT_CLOCK_SKEW_SECONDS:
                raise ValueError("Date JWT trop avancée")
        # Les jetons récents doivent fournir les deux champs ensemble :
        # un seul champ ne doit pas permettre de contourner la limite de durée.
        has_iat = "iat" in claims
        has_nbf = "nbf" in claims
        if has_iat != has_nbf:
            raise ValueError("Dates JWT incomplètes")
        if has_iat and (claims["iat"] > claims["nbf"]
                        or claims["nbf"] >= claims["exp"]):
            raise ValueError("Chronologie JWT incohérente")
        # Pour les nouveaux jetons, la durée réelle signée ne doit jamais
        # dépasser la durée autorisée par le serveur, même avec une exp valide.
        # Les jetons historiques sans iat/nbf restent compatibles.
        if has_iat:
            max_lifetime = MIN * 60
            if (claims["exp"] - claims["iat"] > max_lifetime
                    or claims["exp"] - claims["nbf"] > max_lifetime):
                raise ValueError("Durée de vie JWT excessive")
            # Défense en profondeur : les deux dates doivent aussi être
            # suffisamment récentes par rapport à l'horloge du serveur.
            # Une tolérance de 2 secondes couvre les arrondis aux secondes
            # des NumericDate sans prolonger la durée de vie signée.
            now_seconds = int(datetime.now(timezone.utc).timestamp())
            oldest_allowed = now_seconds - max_lifetime - 2
            if claims["iat"] < oldest_allowed or claims["nbf"] < oldest_allowed:
                raise ValueError("Dates JWT trop anciennes")
        version = claims["tv"]
        if type(version) is not int or version < 0:
            raise ValueError("Version de jeton invalide")
    except (jwt.PyJWTError, KeyError, ValueError, TypeError, OverflowError):
        raise HTTPException(status_code=401, detail="Token invalide", headers={"WWW-Authenticate": "Bearer"})

    u = db.get(User, uid)
    if not u or not u.is_active:
        raise HTTPException(status_code=401, detail="Session invalide", headers={"WWW-Authenticate": "Bearer"})

    # Un changement de rôle, de mot de passe ou de statut invalide
    # immédiatement tous les JWT émis avant la modification.
    if version != u.token_version:
        raise HTTPException(status_code=401, detail="Session expirée : reconnectez-vous", headers={"WWW-Authenticate": "Bearer"})
    return u


def roles(*allowed):
    """Restreint l'accès aux utilisateurs possédant un rôle autorisé."""

    def d(u=Depends(user)):
        if u.role.value not in allowed:
            raise HTTPException(status_code=403, detail="Accès refusé")
        return u

    return d


def sign_qr(code):
    """Génère la signature HMAC d'un billet QR."""
    return hmac.new(
        (SECRET + ":qr").encode(),
        code.encode(),
        hashlib.sha256,
    ).hexdigest()


def check_qr(code, sig):
    """Vérifie la signature d'un billet QR."""
    return hmac.compare_digest(sign_qr(code), sig)

# Lecture facultative du JWT, sans ignorer un en-tête Authorization invalide.
bearer_optionnel = HTTPBearer(auto_error=False)

def utilisateur_optionnel(
    request: Request,
    c: HTTPAuthorizationCredentials | None = Depends(bearer_optionnel),
    db: Session = Depends(get_db),
):
    authorization = request.headers.get("Authorization")
    if authorization is None:
        return None
    if c is None or not c.credentials:
        raise HTTPException(status_code=401, detail="Token invalide", headers={"WWW-Authenticate": "Bearer"})
    return user(c=c, db=db)

def verifier_acces_pays(utilisateur, country_id):
    # ADMIN dispose d'une portée globale.
    if utilisateur.role.value == "ADMIN":
        return
    if utilisateur.role.value != "COUNTRY_MANAGER" or utilisateur.country_id is None:
        raise HTTPException(status_code=403, detail="Accès refusé")
    if utilisateur.country_id != country_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
