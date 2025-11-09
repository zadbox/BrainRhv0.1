"""
Module pour l'intégration avec l'API ROME de France Travail
Gère l'authentification OAuth2 et la récupération des compétences métiers
"""

import os
import requests
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class ROMEAPIClient:
    """Client pour l'API ROME de France Travail"""

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        base_url: str = "https://api.francetravail.io/partenaire",
        token_url: str = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
    ):
        """
        Initialise le client ROME API

        Args:
            client_id: Client ID (ou depuis env ROME_CLIENT_ID)
            client_secret: Client Secret (ou depuis env ROME_CLIENT_SECRET)
            base_url: URL de base de l'API ROME
            token_url: URL pour obtenir le token OAuth2
        """
        self.client_id = client_id or os.getenv("ROME_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("ROME_CLIENT_SECRET")
        self.base_url = base_url
        self.token_url = token_url

        if not self.client_id or not self.client_secret:
            raise ValueError("❌ ROME_CLIENT_ID et ROME_CLIENT_SECRET doivent être définis")

        self.access_token = None
        self.token_expires_at = 0

    def _get_access_token(self) -> str:
        """
        Obtient un access token OAuth2

        Returns:
            Access token valide
        """
        # Vérifier si le token existe et est encore valide
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        # Obtenir un nouveau token
        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "api_rome-metiersv1 api_rome-competencesv1 api_rome-fiches-metiersv1"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                # Soustraire 60s pour la marge de sécurité
                expires_in = token_data.get("expires_in", 3600) - 60
                self.token_expires_at = time.time() + expires_in

                print(f"✅ Token ROME obtenu (expire dans {expires_in}s)")
                return self.access_token
            else:
                print(f"❌ Erreur lors de l'obtention du token: {response.status_code}")
                print(f"Réponse: {response.text}")
                raise Exception(f"Échec d'authentification ROME: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur réseau lors de l'authentification ROME: {e}")
            raise

    def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Effectue une requête à l'API ROME avec retry logic

        Args:
            endpoint: Endpoint complet (ex: "rome-metiers/v1/metiers/metier/M1805")
            params: Paramètres de la requête
            max_retries: Nombre maximum de retries

        Returns:
            Réponse JSON ou None en cas d'erreur
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Accept": "application/json"
        }

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=10
                )

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 401:
                    # Token expiré, forcer le renouvellement
                    print("🔄 Token expiré, renouvellement...")
                    self.access_token = None
                    self.token_expires_at = 0
                    continue

                elif response.status_code == 429:
                    # Rate limiting
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                    print(f"⏳ Rate limit atteint, attente de {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                else:
                    print(f"❌ Erreur API ROME: {response.status_code}")
                    print(f"Réponse: {response.text[:200]}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur réseau (tentative {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None

        return None

    def get_metier_by_code(self, code_rome: str) -> Optional[Dict]:
        """
        Récupère un métier par son code ROME

        Args:
            code_rome: Code ROME du métier (ex: "M1805")

        Returns:
            Détails du métier ou None
        """
        print(f"🔍 Récupération métier ROME: {code_rome}")
        result = self._make_request(f"rome-metiers/v1/metiers/metier/{code_rome}")

        if result:
            print(f"✅ Métier trouvé: {result.get('libelle', code_rome)}")
        return result

    def get_fiche_metier_by_code(self, code_rome: str) -> Optional[Dict]:
        """
        Récupère la fiche métier complète par code ROME

        Args:
            code_rome: Code ROME (ex: "M1805")

        Returns:
            Fiche métier complète ou None
        """
        print(f"📄 Récupération fiche métier: {code_rome}")
        return self._make_request(f"rome-fiches-metiers/v1/fiches-rome/fiche-metier/{code_rome}")

    def get_competences_by_code_rome(self, code_rome: str) -> Dict[str, List[str]]:
        """
        Récupère les compétences pour un code ROME

        Args:
            code_rome: Code ROME du métier (ex: "M1805")

        Returns:
            Dict avec listes de compétences techniques et transversales
        """
        print(f"📡 Récupération des compétences pour code ROME: {code_rome}")

        # Essayer d'abord avec l'API compétences
        result = self._make_request(f"rome-competences/v1/competences/competence/{code_rome}")

        if not result:
            # Fallback: essayer via la fiche métier
            fiche = self.get_fiche_metier_by_code(code_rome)
            if fiche and "competences" in fiche:
                result = fiche["competences"]

        if not result:
            return {"techniques": [], "transversales": []}

        competences_techniques = []
        competences_transversales = []

        # Si result est une liste
        if isinstance(result, list):
            for comp in result:
                if isinstance(comp, dict):
                    libelle = comp.get("libelle", "")
                    type_comp = comp.get("type", "").lower()
                elif isinstance(comp, str):
                    libelle = comp
                    type_comp = ""
                else:
                    continue

                if "technique" in type_comp or "metier" in type_comp or "savoir" in type_comp:
                    competences_techniques.append(libelle)
                elif "transversal" in type_comp or "general" in type_comp or "comportemental" in type_comp:
                    competences_transversales.append(libelle)
                else:
                    # Par défaut, considérer comme technique
                    competences_techniques.append(libelle)

        # Si result est un dict avec des clés spécifiques
        elif isinstance(result, dict):
            if "savoirs" in result:
                competences_techniques.extend([s.get("libelle", s) if isinstance(s, dict) else s
                                               for s in result["savoirs"]])
            if "savoir_faire" in result:
                competences_techniques.extend([s.get("libelle", s) if isinstance(s, dict) else s
                                               for s in result["savoir_faire"]])
            if "savoir_etre" in result or "competences_transversales" in result:
                key = "savoir_etre" if "savoir_etre" in result else "competences_transversales"
                competences_transversales.extend([s.get("libelle", s) if isinstance(s, dict) else s
                                                  for s in result[key]])

        print(f"📊 {len(competences_techniques)} techniques, {len(competences_transversales)} transversales")

        return {
            "techniques": competences_techniques,
            "transversales": competences_transversales
        }

    def _map_titre_to_code_rome(self, titre_poste: str) -> Optional[str]:
        """
        Mapping manuel titre → code ROME (fallback si API recherche pas dispo)

        Args:
            titre_poste: Titre du poste

        Returns:
            Code ROME ou None
        """
        # Mapping basique des titres communs
        mapping = {
            "data scientist": "M1805",
            "data analyst": "M1403",
            "architecte données": "M1805",
            "architecte de données": "M1805",
            "développeur": "M1805",
            "ingénieur logiciel": "M1805",
            "chef de projet": "M1806",
            "consultant": "M1402",
            "analyste": "M1403",
            "business analyst": "M1403",
            "product owner": "M1803",
            "scrum master": "M1806",
            "devops": "M1810",
            "administrateur système": "M1810",
            "administrateur réseau": "M1810",
        }

        titre_lower = titre_poste.lower().strip()

        # Recherche exacte
        if titre_lower in mapping:
            return mapping[titre_lower]

        # Recherche par mots-clés
        for key, code in mapping.items():
            if key in titre_lower or titre_lower in key:
                return code

        # Par défaut, métiers informatiques
        if any(kw in titre_lower for kw in ["data", "développeur", "ingénieur", "informatique", "it", "tech"]):
            return "M1805"  # Études et développement informatique

        return None

    def enrich_offre_with_rome(self, titre_poste: str, code_rome: str = None) -> Dict[str, List[str]]:
        """
        Enrichit une offre d'emploi avec les compétences ROME

        Args:
            titre_poste: Titre du poste
            code_rome: Code ROME (optionnel, si None essaie de le deviner)

        Returns:
            Dict avec compétences techniques et transversales
        """
        # Si pas de code ROME fourni, essayer de le trouver
        if not code_rome:
            code_rome = self._map_titre_to_code_rome(titre_poste)

        if not code_rome:
            print(f"⚠️ Impossible de déterminer le code ROME pour '{titre_poste}'")
            return {"techniques": [], "transversales": []}

        print(f"📋 Code ROME sélectionné: {code_rome} pour '{titre_poste}'")

        # Récupérer les compétences
        competences = self.get_competences_by_code_rome(code_rome)

        return competences

    def get_fiche_metier(self, code_rome: str) -> Optional[Dict]:
        """
        Récupère la fiche métier complète

        Args:
            code_rome: Code ROME du métier

        Returns:
            Fiche métier complète ou None
        """
        print(f"📄 Récupération de la fiche métier pour: {code_rome}")
        return self._make_request(f"fiches-metiers/{code_rome}")


# Fonction helper pour usage simple
def get_rome_competences(titre_poste: str, client_id: str = None, client_secret: str = None) -> Dict[str, List[str]]:
    """
    Fonction helper pour récupérer les compétences ROME d'un coup

    Args:
        titre_poste: Titre du poste
        client_id: Client ID (optionnel si dans .env)
        client_secret: Client Secret (optionnel si dans .env)

    Returns:
        Dict avec compétences techniques et transversales
    """
    try:
        client = ROMEAPIClient(client_id=client_id, client_secret=client_secret)
        return client.enrich_offre_with_rome(titre_poste)
    except Exception as e:
        print(f"❌ Erreur lors de l'enrichissement ROME: {e}")
        return {"techniques": [], "transversales": []}


if __name__ == "__main__":
    # Test du client ROME
    import json

    print("🧪 Test du client ROME API")
    print("=" * 60)

    try:
        # Test avec un métier exemple
        titre_test = "Data Scientist"

        competences = get_rome_competences(titre_test)

        print("\n📊 Résultats:")
        print(json.dumps(competences, indent=2, ensure_ascii=False))

        print(f"\n✅ Test réussi!")
        print(f"  - {len(competences['techniques'])} compétences techniques")
        print(f"  - {len(competences['transversales'])} compétences transversales")

    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
