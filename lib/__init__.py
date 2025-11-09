# -*- coding: utf-8 -*-
"""
Lib - Logique metier extraite (sans dependances Streamlit)
"""

from lib.models import (
    CV,
    Offre,
    ResultatMatching,
    CVParseResult,
    MatchingResponse,
    Project,
    Enterprise
)

from lib.cv_parsing import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_file,
    parse_cv_with_llm,
    parse_cv_from_file,
    get_openai_client
)

from lib.matching_core import (
    cosine_similarity,
    calculate_nice_have_malus,
    calculate_final_score,
    validate_coefficient_experience,
    flatten_cv_sections,
    flatten_offre_sections,
    build_matching_result
)

from lib.parallel_engine import (
    parse_cvs_parallel_async,
    parse_cvs_parallel_sync,
    process_cvs_in_batches_sync
)

__version__ = "1.0.0"
