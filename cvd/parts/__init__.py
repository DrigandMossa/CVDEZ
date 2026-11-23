"""Static parts library: element catalogue, genes, strategies, enzymes, genome coordinates.

Pure data.  Nothing in this package imports from the rest of cvd, so it can be read or
edited without pulling in the designer, the CNV analysis or the GUI.
"""

from .elements import (BUILT_IN_IDS, COSTIM, HINGES, KINDS, LINKS, MARKERS, P2A_SEQ, POLYA,
                       PROMOTERS, RESISTANCE, SGRNA_SCAFFOLD, SHRNA_LOOP, TAGS,
                       TUMOR_SELECTIVE, VECTORS, WPRE_SHORT_LEN)
from .enzymes import RESTRICTION_SITES
from .genes import GENES
from .genome import (ACROCENTRIC_P, ARM_GENES, ARM_ORDER, AUTOSOMES, BUILDS,
                     EXAMPLE_ARM_VALUES, IMMUNE_ARM_NOTES, N_SCORED_ARMS)
from .strategies import STRATEGIES

__all__ = ["ACROCENTRIC_P", "ARM_GENES", "ARM_ORDER", "AUTOSOMES", "BUILDS", "BUILT_IN_IDS",
           "COSTIM", "EXAMPLE_ARM_VALUES", "GENES", "HINGES", "IMMUNE_ARM_NOTES", "KINDS",
           "LINKS", "MARKERS", "N_SCORED_ARMS", "P2A_SEQ", "POLYA", "PROMOTERS",
           "RESISTANCE", "RESTRICTION_SITES", "SGRNA_SCAFFOLD", "SHRNA_LOOP", "STRATEGIES",
           "TAGS", "TUMOR_SELECTIVE", "VECTORS", "WPRE_SHORT_LEN"]
