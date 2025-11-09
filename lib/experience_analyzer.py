"""
Analyseur d'expériences professionnelles
Détecte les trous (gappes) et chevauchements (overlaps) dans le parcours
"""

import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any, Tuple, Optional

from lib.models import Gap, Overlap, Flags


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse une date depuis les formats courants des CVs

    Formats supportés:
    - MM/YYYY
    - YYYY-MM
    - YYYY
    - "Présent", "Actuel", "En cours", "Current", etc.

    Args:
        date_str: Chaîne de date à parser

    Returns:
        datetime object ou None si parsing échoue
    """
    if not date_str:
        return None

    # Nettoyer la chaîne
    date_str = date_str.strip().lower()

    # Dates "en cours"
    if any(keyword in date_str for keyword in ['présent', 'actuel', 'en cours', 'current', 'present', 'now']):
        return datetime.now()

    # Format MM/YYYY
    match = re.match(r'(\d{1,2})/(\d{4})', date_str)
    if match:
        month, year = int(match.group(1)), int(match.group(2))
        # Valider que le mois est entre 1 et 12
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return datetime(year, month, 1)
        return None

    # Format YYYY-MM
    match = re.match(r'(\d{4})-(\d{1,2})', date_str)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        # Valider que le mois est entre 1 et 12
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return datetime(year, month, 1)
        return None

    # Format YYYY seulement (prendre janvier par défaut pour début, décembre pour fin)
    match = re.match(r'(\d{4})', date_str)
    if match:
        year = int(match.group(1))
        return datetime(year, 1, 1)  # On prendra 1er janvier par défaut

    return None


def months_between(date1: datetime, date2: datetime) -> int:
    """Calcule le nombre de mois entre deux dates"""
    delta = relativedelta(date2, date1)
    return abs(delta.years * 12 + delta.months)


def days_between(date1: datetime, date2: datetime) -> int:
    """Calcule le nombre de jours entre deux dates"""
    return abs((date2 - date1).days)


def detect_gaps_and_overlaps(experiences: List[Dict[str, Any]]) -> Flags:
    """
    Détecte les trous et chevauchements dans les expériences professionnelles

    Args:
        experiences: Liste des expériences (doit contenir date_debut, date_fin, poste, entreprise)

    Returns:
        Flags object contenant gappes et overlaps détectés
    """
    gaps = []
    overlaps = []

    # Parser et trier les expériences par date de fin décroissante
    parsed_exps = []
    for i, exp in enumerate(experiences):
        date_debut = parse_date(exp.get('date_debut', ''))
        date_fin = parse_date(exp.get('date_fin', ''))

        if date_debut and date_fin:
            parsed_exps.append({
                'index': i,
                'poste': exp.get('poste', 'Inconnu'),
                'entreprise': exp.get('entreprise', 'Inconnu'),
                'date_debut': date_debut,
                'date_fin': date_fin,
                'original': exp
            })

    # Trier par date de fin décroissante
    parsed_exps.sort(key=lambda x: x['date_fin'], reverse=True)

    # Détecter les gappes (trous >= 3 mois)
    for i in range(len(parsed_exps) - 1):
        exp_current = parsed_exps[i]
        exp_next = parsed_exps[i + 1]

        # Le trou est entre la fin de exp_next et le début de exp_current
        gap_months = months_between(exp_next['date_fin'], exp_current['date_debut'])

        if gap_months >= 3:
            period = f"{exp_next['date_fin'].strftime('%Y-%m')} → {exp_current['date_debut'].strftime('%Y-%m')}"
            between = f"Expérience #{exp_next['index']+1} ({exp_next['entreprise']}) et Expérience #{exp_current['index']+1} ({exp_current['entreprise']})"

            gaps.append(Gap(
                period=period,
                duration_months=gap_months,
                between=between,
                cv_excerpt=None  # Pourrait être enrichi en cherchant dans le CV
            ))

    # Détecter les overlaps (chevauchements > 14 jours)
    for i in range(len(parsed_exps)):
        for j in range(i + 1, len(parsed_exps)):
            exp_a = parsed_exps[i]
            exp_b = parsed_exps[j]

            # Vérifier si les périodes se chevauchent
            # Chevauchement si: début_B < fin_A ET début_A < fin_B
            if exp_b['date_debut'] < exp_a['date_fin'] and exp_a['date_debut'] < exp_b['date_fin']:
                # Calculer la période de chevauchement
                overlap_start = max(exp_a['date_debut'], exp_b['date_debut'])
                overlap_end = min(exp_a['date_fin'], exp_b['date_fin'])

                overlap_days_count = days_between(overlap_start, overlap_end)

                # Ignorer les chevauchements < 14 jours (peuvent être normaux)
                if overlap_days_count > 14:
                    overlap_period = f"{overlap_start.strftime('%Y-%m')} → {overlap_end.strftime('%Y-%m')}"
                    experiences_str = f"Expérience #{exp_a['index']+1} ({exp_a['entreprise']}) et Expérience #{exp_b['index']+1} ({exp_b['entreprise']})"
                    same_company = exp_a['entreprise'].lower() == exp_b['entreprise'].lower()

                    overlaps.append(Overlap(
                        overlap_period=overlap_period,
                        overlap_days=overlap_days_count,
                        experiences=experiences_str,
                        same_company=same_company,
                        cv_excerpt=None  # Pourrait être enrichi
                    ))

    return Flags(gappes=gaps, overlaps=overlaps)


def format_flags_for_llm(flags: Flags) -> str:
    """
    Formate les flags pour inclusion dans le prompt LLM

    Args:
        flags: Flags object

    Returns:
        Chaîne formatée pour le prompt
    """
    if not flags.gappes and not flags.overlaps:
        return "Aucun flag détecté (pas de trous ni de chevauchements significatifs)."

    parts = []

    if flags.gappes:
        parts.append(f"⚠️ TROUS DÉTECTÉS ({len(flags.gappes)}):")
        for gap in flags.gappes:
            parts.append(f"  - {gap.period} ({gap.duration_months} mois) entre {gap.between}")

    if flags.overlaps:
        parts.append(f"⚠️ CHEVAUCHEMENTS DÉTECTÉS ({len(flags.overlaps)}):")
        for overlap in flags.overlaps:
            same_company_str = " (même entreprise)" if overlap.same_company else ""
            parts.append(f"  - {overlap.overlap_period} ({overlap.overlap_days} jours) : {overlap.experiences}{same_company_str}")

    return "\n".join(parts)
