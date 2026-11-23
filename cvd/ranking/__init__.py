"""Ranked, prebuilt vector options for an insert.

rank_vector_options() builds every candidate layout (lentivirus and AAV, several promoter
layouts), modifies each as far as the part library allows, scores the modified vector on
five criteria out of 100 and ranks them.  Every score, every modification and every
comparison between two options is explained in text that is generated from the actual
numbers, so the explanation cannot drift from the ranking.

Layering: tables and model are data; scoring, optimize and engine sit on cvd.design;
explain turns a ranking into text.  Nothing here imports cvd.gui or cvd.cli.
"""

from .engine import rank_vector_options
from .explain import (basis_for_option, compare_line, config_for_option, explain_option,
                      explain_option_parts, fit_text, modification_parts, options_report,
                      options_table, parse_explain, ranking_summary, write_options_report)
from .model import (CriterionScore, InsertProfile, Modification, RankingResult, VectorOption)
from .optimize import optimize_config
from .scoring import parse_setting, profile_insert
from .tables import SETTING_CHOICES, VECTOR_LABEL, VECTOR_SHORT

__all__ = ["CriterionScore", "InsertProfile", "Modification", "RankingResult", "SETTING_CHOICES",
           "VECTOR_LABEL", "VECTOR_SHORT", "VectorOption", "basis_for_option", "compare_line",
           "config_for_option", "explain_option", "explain_option_parts", "fit_text",
           "modification_parts", "optimize_config", "options_report", "options_table",
           "parse_explain", "parse_setting", "profile_insert", "rank_vector_options",
           "ranking_summary", "write_options_report"]
