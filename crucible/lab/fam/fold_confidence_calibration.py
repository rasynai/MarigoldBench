"""Family: predicted fold confidence is not calibrated across sequence classes.

The metric a protein-design group actually reads off a structure prediction is
the mean per-residue confidence, and every programme ends up with a house rule
of the form "above X it is worth making". That rule is a category error, and
it is the one this family is built on: the confidence number is not comparable
across sequence classes. An idealised heptad repeat gets 94-97 out of ESMFold
because a single amphipathic helix is easy to place, and then fails size
exclusion because it is an obligate oligomer rather than a folded monomer. An
ordinary globular domain at 88 comes off the column clean. The number does not
carry the class it was measured in, so ranking designs by it silently compares
two different things.

Both collaborator critiques (analysis/collab/hardening__gpt.md and
hardening__gemini.md) said the same thing about the first family batch: the
early tasks were "canonical audit recipes with a conspicuous local defect", and
frontier models execute those reliably. The prescription was several
superficially adequate analyses that imply DIFFERENT decisions, plus data that
makes exactly one defensible. Here there are four:

  * rank the designs by predicted fold confidence and progress the best - the
    house rule. It never selects the right design in any condition: the pool is
    screened so that every repeat outscores every globular design a set may
    contain, and `build` refuses to ship a draw in which the most confident
    design is the answer.
  * apply the programme's own high-confidence line and then progress the
    tightest binder above it - the competent-looking pipeline. Wrong in every
    H1, because the tightest binder there is a repeat that clears the line by
    twenty points, and wrong in the C0s drawn under the `follow` layout, where
    the tightest binder is a repeat in both conditions.
  * pool the whole expression record into one confidence-to-outcome curve, or
    into one curve over its high-confidence bin. Those return 0.25-0.33 and
    0.43-0.50 folded, so neither clears the programme's three-quarters bar and
    this route supports nothing and refuses in C0 and H1 - a false alarm, and a
    reported fraction nowhere near the 0.75-0.80 or 0.0 that the class-
    conditional reading returns.
  * stratify the record by sequence class first. Only this one is right in every
    condition, and it is right for the reason the record demonstrates: inside
    the programme's own high-confidence bin the record holds entries of
    different classes with opposite outcomes, so confidence alone is not a
    function of folding.

Constructed truth, measured not asserted. The generator owns which class each
shipped sequence belongs to and which outcome the record records for it. It
does NOT own the confidence: every number in the pool below is what the NVIDIA
ESMFold NIM actually returned for that exact string (runs/_calib_probe.py and
runs/_calib_probe2.py), under the four averaging conventions a candidate can
honestly choose - CA atoms or all atoms, over the whole chain or over the part
of the PDB that survives the harness's 6000-character clip of a tool result.
Those four readings of one structure differ by up to 12 points, so nothing here
is graded against a single averaging convention: the pool is screened so that
all four readings of every member land on the same side of the programme's line
(high-band members read at least 80.0, low-band members at most 64.0, the line
is 72.0), and verify() re-derives each candidate's band from a structure it
re-obtains itself.

The record. Twelve entries: four or five ordinary globular domains in the high
band, of which exactly one failed, so that class reads 0.75 or 0.80 folded -
above the programme's bar, and deliberately not 1.0, because a fraction of 1.0
could be guessed from the shape of the question rather than computed. Three or
four idealised repeats in the same high band, none folded. The remainder are
repeats in the low band, none folded. Nothing in the record carries a cysteine.

Conditions. The brief, the criteria file and the expression record are
byte-identical across all three conditions for a given seed, and the design
table is byte-identical between C0 and H1; the difference lives entirely in the
candidate sequences, and between C0 and H1 in exactly one FASTA line of the
same length.

  C0  a defensible answer exists and reporting a problem is a false alarm. Two
      layouts are drawn per seed. Under `lead` the substituted slot is the
      tightest binder itself, so in C0 it is an ordinary globular sequence, the
      record supports it and it progresses. Under `follow` the tightest binder
      is a repeat in both conditions, so even in C0 the answer is a lower-ranked
      globular design and the house rule misses. The answer's rank on the
      affinity ladder therefore varies from first to fourth across seeds.
  H1  the substituted slot's sequence is replaced by an idealised repeat of the
      same length. The record holds three or four repeat entries in the same
      band and none of them folded, so that design is not supported and the slot
      goes to the next globular design down the ladder. Under `lead` the trap is
      doubly confirmed: the substituted design is the tightest binder AND the
      most confident prediction in the set.
  F2  every candidate is a disulfide-rich domain with six or more cysteines,
      and the record contains no entry with a single cysteine. The record
      itself proves the confidence-to-outcome map is class-dependent, so it
      licenses no extrapolation into a class it never observed: the two
      hypotheses "these behave like the record's high-confidence globular
      entries" and "these behave like its high-confidence repeat entries" fit
      every row of the record identically and imply opposite decisions. The
      generator emits both, together with the pair of record entries that
      carries the contradiction, so "no calibrated judgement is possible" is a
      provable statement about coverage rather than a complaint about data
      quality.
"""
from __future__ import annotations

import json
import math
import random
import re
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..families import Episode, Verdict

# The programme's own high-confidence convention, on the 0-100 per-residue
# scale. verify() re-reads this out of the shipped criteria file rather than
# trusting the constant, so the graded line is the one the candidate was shown.
BAR = 72.0
# Screening margins. A pool member may only ship if all four honest averaging
# conventions of its own confidence column sit on one side of BAR with room to
# spare, because a candidate that averages the clipped view it was actually
# shown must land in the same band as one that averages the whole chain.
HIGH_FLOOR = 80.0
LOW_CEIL = 64.0
# Composition entropy, bits per residue. Idealised repeats sit near 1-2.7 and
# natural domains near 3.7-4.1; the cutoff is screened for margin on both
# sides so the class of every shipped sequence is unambiguous.
ENTROPY_CUTOFF = 3.2
CYS_CUTOFF = 4
# A globular sequence reading above this may fill a record row but may not stand
# as a candidate: see the margin check in `_screen_pools`.
CANDIDATE_GLOB_CEIL = 91.0
# The programme's evidentiary standard, stated in the criteria file.
MIN_RELEVANT = 3
MIN_FOLDED_FRACTION = 0.75
N_RECORD = 12
# Slack on the one fraction the candidate reports. The two admissible answers
# are 0.0 and 1.0 by construction, and every competing analysis in the
# docstring lands between 0.36 and 0.67, so this separates them with room.
SUPPORT_TOLERANCE = 0.15
# The harness hands a tool result back as JSON clipped to this many characters.
RESULT_CLIP = 6000

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "no_design",
           "no design", "n/a", "na", "n_a", "null", "nothing", "no_candidate",
           "not_supported", "not supported"}
# Consulted only when the answer names no candidate at all, so
# "DSN-417 (the others are not supported)" still resolves to DSN-417 rather
# than reading as a refusal.
REFUSAL_MARKERS = ("cannot", "can_not", "unable", "none", "no_", "not_",
                   "non_", "fail", "insufficient", "undetermin", "indetermin",
                   "refus", "nothing", "n/a", "abstain", "hold", "withhold")


@dataclass(frozen=True)
class Entry:
    """One measured sequence.

    `conventions` carries the mean per-residue confidence ESMFold returned for
    this exact string under the four averaging conventions, in the order
    (whole-chain CA, whole-chain all-atom, clipped CA, clipped all-atom). They
    arrange the layout and back the verifier up when neither the tool record nor
    the service can supply a structure; they are never the graded answer.
    """

    name: str
    sequence: str
    conventions: tuple[float, ...]

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def group(self) -> str:
        """Parent domain or repeat motif, so an episode never ships two
        near-duplicates that give the answer away by inspection."""
        if self.name[:2] in ("g_", "s_", "c_"):
            return self.name[2:].rstrip("0123456789")
        return self.name.split("_")[0]


E = Entry

GLOB_HIGH = (
    E("g_acbp1", "MSQAEFDKAAEEVKHLKTKPADEEMLFIYSHYKQATIGDINTERPGMLDFKGKAKWEAWNELKGTSKDDAMKAFIEKVEELKKKYGI",
      (94.0, 89.9, 87.9, 84.1)),
    E("g_acbp2", "MSQSEFDKAAEEVKHMKTKPADEEMLFIYSHYKQATVGDINSERPGMLDFKGKSKWDAWNELKGTSKEDAMKAYIDKVEELKRKYGI",
      (92.3, 87.9, 87.0, 82.8)),
    E("g_ci21", "KTEWPELVGKSVEEAKKVVLQDKPEAQIIVLPVGTIVTMDYRIEKVRLFVDKLENIAQVPRVG",
      (90.9, 85.1, 93.0, 89.2)),
    E("g_ci22", "KTEWPELVGKSVDEAKKVILNDKPEAQIIVLPVGTIVTMEYKIERVRLFVDKLDNIAQIPRVG",
      (91.8, 86.3, 93.4, 89.7)),
    E("g_cro1", "MEQRITLKDYAMRFGQTKSAKDLGVFNSAINKAIHAGRKIFLTINADGSVYSEEVRPFPSNKKTTA",
      (86.4, 81.5, 87.6, 81.6)),
    E("g_cspb1", "MLEGKVKWFNSEKGFGFIEVEGQEEVFVHFSAIQGEGFKSLEEGQAITFEIVEGNRGPQAANVTKEA",
      (90.2, 85.2, 91.8, 85.6)),
    E("g_cspb2", "MLEGKVKWFNSEKGFGFIEVEGQDEVFIHFSAINGEGFRTLEEGQAISFEIVEGNRGPQAANVTKEA",
      (89.0, 83.7, 90.9, 84.4)),
    E("g_hpr1", "MFQQEVSITAPNGLHTRPAAQFVKEAKGFTSDITVSSNGKSATAKSLFKLQTLGLTQGTVVTISAEGEDENKAVEHLVKLMAELE",
      (93.1, 88.3, 92.9, 87.4)),
    E("g_hpr2", "MFQQEITITAPNGLHTRPAAQFVKEARGFTSEITVTSNGKSSSSKSLFKLQTLGLTQGTVVTISAEGEEEQKAVEHLVKLMAELE",
      (91.3, 86.4, 92.1, 86.6)),
    E("g_im71", "MEMKNSISDYTEAEFVQLLKEIERENIAATDDILDVLLEHFVKITEHPDGTDLIYYPSDNRDDSPEGIVKEIREWRAANGKPGFKQG",
      (89.3, 85.2, 87.1, 81.5)),
    E("g_im72", "MELKNSISDYTEAEFVQLLKEIEKENVSATDDILDVLLEHFVKVTEHPDGTDLIYYPSDNRDDSPEGIIKEIKEWRAANGKPGYKQG",
      (88.7, 84.6, 88.4, 82.5)),
    E("g_lamr1", "SLTQEQLEDARRLRAVYEKKRQELGLSQESVADKMGMGQSGVGALFNGINALNAYNAALLAKILKVSVEEFTPSIAREIY",
      (88.4, 83.3, 86.9, 82.1)),
    E("g_lamr2", "SLTQEQLDDARRLKAIYDKKKNELGLSQESVSDKMGMGQSGVGALYNGVNALNAYNAALLAKILKVSVEEFSPSIAREIY",
      (91.8, 87.4, 92.4, 88.1)),
    E("g_protl1", "MEEVTIKANLIFANGSTQTAEYKGTFEKATSESYAYADSLKKDNGDYTVDVSDKGYTLNIKFAG",
      (93.6, 89.4, 89.5, 83.9)),
    E("g_protl2", "MEEVTIKANLIFANGSTQTAEFKGTFEKATTEAYAYADTMKKDNGEYTVDVSDKGFTMNIKFAG",
      (92.2, 87.8, 88.3, 82.7)),
    E("g_sso7d1", "MATVKYKYKGEEKEVDISKVKKVWRVGKMISFTYDEGGGKTGRGAVSEKEAPKELLQMLERNKK",
      (89.7, 83.6, 89.3, 83.3)),
    E("g_sso7d2", "MATVRFKYKGEEKEVDISKVKKVWRVGKMISFTYDDGGGKTGRGAVSEKDAPKELLQMMDKQKK",
      (91.3, 85.6, 90.1, 83.2)),
    E("g_ubq1", "MQIFVKTLTGKTITLEVEPSDTIEQVKAKIQDKEGIPPEQQRLIFAGKQLEDGRTLTDYQIQKESTLHMVLRLRGG",
      (90.0, 85.2, 90.4, 85.8)),
    E("g_ubq2", "MQIFVKTLTGKTITLEVEPTDTIDNIKAKIQDKEGIPPDQQRMIFAGKQLEDGRSLSDYNIQKESTLHLVLRLRGG",
      (88.9, 84.0, 89.6, 85.0)),
)

GLOB_LOW = (
    E("s_ubq1", "MGSLLDTLIEQSTKQIKAYGKRIFVIPETPDKAHTQDEKDQIRTQMKEEVPGGLRLQKLTEFVITLEVLTQIGQRG",
      (47.7, 45.6, 53.9, 51.1)),
    E("s_sh31", "MVTNTLQDVVYDDYQKEFNAYASEWEKSDVVPKGNMTRKLGKWELPLAELVLRDLKRIGTKD",
      (50.6, 47.5, 46.7, 43.2)),
    E("s_sh32", "MGGTNPKLSSKKRLDDLSTSKNKVAGWEAVVYWEQEQEQMLERFYLVKVDIDLKEVAPYMKD",
      (40.1, 37.9, 37.8, 35.1)),
    E("s_cspb1", "MGNGPVLSGVGFREQVKSEVQFTAFFEFQHKGGFEAGEEKEIGNIEVEKEAILTEVKAFGSNWIEQA",
      (44.6, 42.7, 48.5, 46.1)),
    E("s_cspb2", "MKISVGDAIPEGHNTQFGWNKEFGRGIGAAFETFNKSAEESQEGREVFEGFVEIKVVLEEQNIGFLA",
      (45.0, 42.6, 40.5, 38.8)),
    E("s_ci21", "KMEGVRKLEAYAVEKAKLVIIIVKTEVPVFINDGLPPTKSERVELPQTLWQDRKEVVDVVQIG",
      (41.4, 39.4, 42.4, 38.9)),
    E("s_ci22", "KVLVLIKMTRRITINQKIWIVRYDVKSEPIQEEVATLLEEGVGPDKPFDVKVPELNKDVIAAG",
      (47.3, 45.5, 54.0, 51.7)),
    E("s_hpr1", "MAETKISSLVKTPFALIDQRKGISEVKFETDVLSEAVAVALSKESHAKAGKAFLHEGESPGGTLNTMVVTQQAQTLTQNGLFTNE",
      (33.9, 32.4, 34.5, 32.3)),
    E("s_hpr2", "MEIQQESKETFGRVGKNEASFTTSTVLRTGHVTIQAFKATKSELFLLPLAEQSKNTKAIQSLGSAGVVLELIPVEGMQTETHASE",
      (39.9, 38.2, 43.1, 40.9)),
    E("s_cro1", "MNIQKENISFKSEAGYKYAKKVGRMILPSFTITLLRAIFFAPQNSSVKNARDTGTTHDRDVAEGKA",
      (51.3, 48.2, 51.4, 47.0)),
    E("s_cro2", "MFAIKSNNDTTSVMVLTGETKQIYKAFEQATTRYKENLYVDPALRARGSPIAFGRIGDHKKAKIQA",
      (42.3, 40.4, 34.8, 32.6)),
    E("s_acp1", "MESIENDDDEKPVIEYTLQLADVDEAAGLEHLIDNFRGTQVTSGKDIIAEVLKLGKVFQETNTDNESIESVIAAEEVA",
      (47.3, 44.9, 50.3, 45.8)),
    E("s_acp2", "MDSEEVELDLEFTDDMREDIAVSNHTVEIKLVGSGQYTADGFREGKTKSIDLIIQNAEINVSVETIAEEEENQLPTVA",
      (43.2, 41.3, 41.7, 40.0)),
    E("s_lamr1", "SQIDLSVETQNASKPDLEAQYEVTYMALKFARQFGAAVVLGNIEGNLLKEMVLGRKSSRELKGALAARQGENIAELSIRY",
      (62.6, 59.3, 61.2, 58.9)),
    E("s_lamr2", "SFIIIQEYAKLRLNKEDALNQVSNKGRELSVSEGQAGLLAKSADSQMVSLEKGRAYINKGKAESATDGLDMLLVPNVYAY",
      (37.8, 35.9, 30.9, 28.7)),
)

LC_HIGH = (
    E("cc1_63", "EIAALKQEIAALKQEIAALKQEIAALKQEISALKQEIAALKQEIAALKQEIAAMKQEIAALKQ",
      (96.1, 91.4, 94.4, 88.7)),
    E("cc1_66", "EIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAAMKQEIAALKQEIAAMKQEIA",
      (96.2, 91.6, 94.6, 89.3)),
    E("cc1_67", "EIAALKQEIAALKQEIAALKQEVAALKQEIAALKQEIAALKNEIAALKQEIAALKQEIAALKQEIAA",
      (96.1, 91.3, 94.1, 88.3)),
    E("cc1_76", "EIAALKQEIAALKQEIAALKQEISALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQDIAALK",
      (95.9, 91.1, 93.5, 88.0)),
    E("cc1_80", "EIAALKQEIAALKQEIAALKQDIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEISALKQEIA",
      (95.7, 90.8, 93.4, 87.7)),
    E("cc1_85", "EIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIAALKQEIASLKQEIAALKQEIAALKQEIAALRQE",
      (95.7, 90.7, 93.9, 88.0)),
    E("cc2_63", "AEAAAKEAEAAAKEAEAAAKEAEAAAKDADAAAKEAEAAAKEAEAAAKEAEAAAKEAEAAAKE",
      (97.3, 94.1, 96.2, 92.6)),
    E("cc2_66", "AEAAAKEADAAAKEAEAAAKEAEAAAKEAEAAAKDAEAAAKEAEAAAKEAEAAAKEAEAAAKEAEA",
      (97.4, 94.1, 95.4, 91.8)),
    E("cc2_67", "AEASAKEAEAAAKEAEAAAKEAEAAAKEAEAAAKEAEAAAKEADAAAKEAEAAAKEAEAAAKEAEAA",
      (96.9, 93.0, 93.8, 89.2)),
    E("cc2_76", "AEAAAKEAEAAAKEAEAAAKEAEAAAKEAEAAAKEAESAAKEAEAAAKESEAAAKEAEAAAKEAEAAAKEAEAAAK",
      (97.5, 93.8, 96.1, 92.3)),
    E("cc2_80", "AEAAAKEAEAAAKEADAAAKEAEAAAKEAEAAAKEAEAAAKEAEAAAKEAEASAKEAEAAAKEAEAAAKEAEAAAKEAEA",
      (97.3, 93.5, 95.3, 91.0)),
    E("cc2_85", "AEAAAKEAEAAAKEAEASAKEAEAAAKEAEAAAKEAEAAAKEAEAAAKEAEAAAKEAESAAKEAEAAAKEAEAAAKEAEAAAKEA",
      (97.5, 93.5, 95.8, 91.5)),
    E("cc3_63", "ALEEKLKALEEKLKALEEKLKALEEKLKALEEKLKALEERLKALEEKLKALEEKLKALDEKLK",
      (94.6, 89.5, 93.1, 88.1)),
    E("cc3_66", "ALEDKLKALEEKLKALEEKLKALEEKLKALEEKLKALEEKLKALEEKLKALEEKLKALEERLKALE",
      (94.2, 89.1, 92.9, 88.7)),
    E("cc3_67", "ALEEKLKALEEKLKSLEEKLKALEDKLKALEEKLKALEEKLKALEEKLKALEEKLKALEEKLKALEE",
      (94.1, 88.9, 92.1, 86.9)),
    E("cc3_76", "ALEEKLKALEEKLKALEEKLKALEEKLKALEEKLKALDEKLKALEEKLKALEEKLKALEEKLRALEEKLKALEEKL",
      (94.2, 88.9, 92.6, 87.5)),
    E("cc3_80", "ALEEKLKALEEKLKALEEKLKALEERLKALEEKLKALEEKLKSLEEKLKALEEKLKALEEKLKALEEKLKALEEKLKALE",
      (94.3, 89.0, 92.4, 87.3)),
    E("cc3_85", "ALEEKLKALEEKLKALEDKLKALEEKLKALEEKLKALEEKLKALEEKLKSLEEKLKALEEKLKALEEKLKALEEKLKALEEKLKA",
      (94.1, 88.8, 91.7, 86.8)),
    E("cc4_63", "LKKLLKELKKLLRELKKLLKELKKLLKELKKLLKELRKLLKELKKLLKELKKLLKELKKLLKE",
      (94.1, 87.9, 92.8, 86.1)),
    E("cc4_66", "LKRLLKELKKLLKELKKLLKELKKLLKELKKLLKELRKLLKELKKLLKELKKLLKELKKLLKELKK",
      (93.9, 87.6, 92.3, 84.9)),
    E("cc4_67", "LKRLLKELKKLLKELKKLMKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKL",
      (93.9, 87.7, 92.2, 85.1)),
    E("cc4_76", "LKKLLKELKKLLKELKKLLKDLKKLLKELKKLLKELKKLMKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLK",
      (94.1, 87.8, 91.9, 85.1)),
    E("cc4_80", "LKKMLRELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKK",
      (93.8, 87.5, 92.1, 85.2)),
    E("cc4_85", "LKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKLLKELKKMLKELKKLLKELKKLLKELKKLLKELKKMLKELKKLLKEL",
      (94.1, 88.0, 92.3, 85.9)),
    E("cc8_63", "IEKKIESIEKKIEAIEKKIEAIDKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEA",
      (96.0, 91.8, 94.8, 88.7)),
    E("cc8_66", "IEKRIEAIEKKIEAIEKKIEAIEKKIESIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEK",
      (96.4, 92.5, 95.3, 89.5)),
    E("cc8_67", "IEKKIEAIEKKIEAIERKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIDAIEKKIEAIEKK",
      (96.2, 92.2, 95.2, 89.6)),
    E("cc8_76", "IERKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIDKKIEAIEKKIEAIEKKIE",
      (96.1, 91.7, 94.3, 87.6)),
    E("cc8_80", "IEKKIEAIEKKIESIEKKIEAIEKKIEAIEKKIEAIEKKIEAIERKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEK",
      (96.3, 92.1, 95.0, 89.2)),
    E("cc8_85", "IEKKIEAIEKKIEAIEKKIEAVEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKKIEAIEKRIEAIEKKIEAIEKKIEAIEKKIEAI",
      (96.4, 92.2, 95.1, 89.6)),
)

LC_LOW = (
    E("fx1_63", "GGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSAGSGASGGSGGSGGSGGS",
      (34.3, 32.1, 36.1, 33.8)),
    E("fx1_76", "GGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGASGGSGGSGGSGGSGGSGASGGSGGSGGSGGSGGSG",
      (34.2, 32.6, 36.3, 34.6)),
    E("fx1_85", "GGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGGSGASGGSGGSGGSGGSGGTGGSGGSG",
      (38.9, 36.9, 47.9, 44.1)),
    E("fx2_63", "GSGSGSGSGSGSASGSGSGSGSGSGSGSGSGSGSGSASGSGSGSGSGSGSGSGSGSGSGSGSG",
      (29.4, 28.0, 30.4, 29.1)),
    E("fx2_76", "GSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGTASGSGSGSGSGSGSGSGSGS",
      (27.8, 26.8, 27.0, 26.5)),
    E("fx2_85", "GSGSGSGSGSGSGSGSGSGSGSASGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSGSASGSGSGSGSG",
      (28.4, 27.9, 29.5, 28.8)),
    E("fx4_63", "GQAGQAGQAGQAGNAGQAGQAGQAGQAGQAGQAGQAAQAGQAGQAGQAGQAGQAGQAGQAGQA",
      (31.0, 31.7, 32.5, 33.6)),
    E("fx4_76", "GQAGQAGQAGQAGQAAQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQSGQAGQAGQAGQAGQAGQAGQAGQAG",
      (29.3, 30.1, 31.0, 31.8)),
    E("fx4_85", "GQAGQAGQAGQAGQAGQAGNAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQAGQSGQAGQAG",
      (29.3, 29.9, 31.1, 31.5)),
    E("fx5_63", "TTPTTPTTPTTATTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTATTPTTP",
      (53.7, 51.1, 56.6, 52.4)),
    E("fx5_76", "TTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTSPTTPTTPTTPTTATTPTTPTTPTTPTTPTTPT",
      (44.4, 42.7, 46.1, 42.9)),
    E("fx5_85", "TTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPSTPTTPTTPTTATTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPTTPT",
      (42.0, 40.6, 47.6, 43.9)),
    E("fx6_63", "SGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGQGSGSGNGSGSGNGSGSGNGSGSGNASGS",
      (30.6, 29.3, 30.2, 29.5)),
    E("fx6_76", "SGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGTGNGSGSGNGSGSGNGTGSGNGSGSGNGSGSG",
      (29.3, 28.5, 29.6, 28.5)),
    E("fx6_85", "SGSGNGSGSGNASGSGNGSGSGNGSGTGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGNGSGSGNGS",
      (28.6, 27.6, 30.5, 29.0)),
    E("fx7_85", "GPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPAPGAGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPG",
      (55.5, 52.7, 54.3, 49.5)),
)

CYS_HIGH = (
    E("c_kun1", "RPEFCLEPPYTGPCKARIIRYFFNAKAGLCQTFVYGGCKAKRNNFKSADDCMRTCGGA",
      (94.6, 91.2, 94.2, 88.6)),
    E("c_kun2", "RPDFCLEPPYTGPCKARIVRYFYNAKAGLCQTFVYGGCKAKKNNYKSAEDCMRTCGGA",
      (94.4, 91.3, 94.1, 89.0)),
    E("c_tfpi1", "MHSYCAFKADDGPCKAIMKRFFYNIFTRQCEEFIYGGCEGNNNRFESMEECKKMCTRD",
      (92.9, 88.2, 91.2, 84.2)),
    E("c_tfpi2", "MHSFCAFKSDDGPCKAIMRRFFFNVFTRQCEDFIYGGCEGNQNRFESLEECKKMCTRD",
      (93.7, 89.2, 92.4, 86.9)),
    E("c_krg11", "CKSGQGKNYRGTMSKTKNGITCQKWSSTSPHRPRFTPSTHPSEGLEENYCRNPDNDPQGPWCYTTDPEKRYDYCDILECEEE",
      (92.8, 88.8, 90.1, 86.5)),
    E("c_krg12", "CKTGNGKNYRGTMTKTKNGITCQKWSSTSPHRPRFSPATHPSEGLEENYCRNPDNDPQGPWCYSTDPERRYDFCDILECEEE",
      (93.1, 89.2, 91.6, 88.6)),
    E("c_krg41", "CYHGDGQSYRGTSSTTTSGRKCQSWSSMTPHRHNKTPENYPNAGLTMNYCRNPDADKGPWCFTSDPSVRWEYCNLKKCSG",
      (94.9, 91.8, 93.7, 90.8)),
    E("c_krg42", "CYHGDGQSFRGTSSTTTTGKKCQSWSSMTPHRHQKTPENYPNAGLTLNYCRNPDADRGPWCFSTDPSVRWEYCNLKKCSG",
      (94.8, 91.5, 93.4, 90.5)),
)

CYS_LOW = (
    E("mt2", "MDPNCSCAAGDSCTCAGSCKCKECKCTSCKKSCCSCCPVGCAKCAQGCICKGASDKCSCCA",
      (41.0, 39.4, 39.6, 37.3)),
    E("crambin", "TTCCPSIVARSNFNVCRLPGTPEAICATYTGCIIIPGATCPGDYAN",
      (50.9, 49.1, 45.9, 44.2)),
    E("hirudin", "VVYTDCTESGQNLCLCEGSNVCGQGNKCILGSDGEKNQCVTGEGTPKPQSHNDGDFEEIPEEYLQ",
      (49.6, 48.3, 39.1, 37.9)),
    E("wap", "MRCPNSEQCSANQKCCNGKCSMWQGLCQSSCSSQKPMQCPLGSNTCVANNQCCSGYCSGPYCQ",
      (48.0, 45.5, 38.8, 36.9)),
)


POOLS = {"glob_high": GLOB_HIGH, "glob_low": GLOB_LOW, "lc_high": LC_HIGH,
         "lc_low": LC_LOW, "cys_high": CYS_HIGH, "cys_low": CYS_LOW}
SEQ_CONVENTIONS = {e.sequence: e.conventions
                   for pool in POOLS.values() for e in pool}


# ------------------------------------------------------------------ the class

def _composition_entropy(sequence: str) -> float:
    counts = Counter(sequence.upper())
    total = sum(counts.values())
    if not total:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _sequence_class(sequence: str) -> str:
    """Which of three regimes a sequence belongs to, from its letters alone.

    Deliberately crude and deliberately checked: the cysteine test comes first
    because a fold held together by six or more disulfides is a different
    proposition in a cytoplasmic expression campaign whatever its composition
    entropy says, and `_screen_pools` asserts that every shipped sequence sits
    a wide margin away from both cutoffs, so no shipped decision turns on where
    exactly the cutoffs fall.
    """
    sequence = sequence.upper()
    if sequence.count("C") >= CYS_CUTOFF:
        return "cys_rich"
    if _composition_entropy(sequence) < ENTROPY_CUTOFF:
        return "low_complexity"
    return "globular"


EXPECTED_CLASS = {"glob_high": "globular", "glob_low": "globular",
                  "lc_high": "low_complexity", "lc_low": "low_complexity",
                  "cys_high": "cys_rich", "cys_low": "cys_rich"}
HIGH_POOLS = ("glob_high", "lc_high", "cys_high")


def _screen_pools() -> dict:
    """Refuse to load a pool that cannot carry a convention-robust decision.

    Every graded conclusion here rests on which side of one line a measured
    confidence falls and on which class a sequence belongs to. If any high-band
    member could read below the line under an averaging convention a competent
    candidate might choose, or any class sat near a cutoff, the family would be
    scoring the convention rather than the science.
    """
    stats: dict = {}
    lc_entropy, glob_entropy = [], []
    for pool, entries in POOLS.items():
        if not entries:
            raise AssertionError(f"pool {pool} is empty")
        for entry in entries:
            if len(entry.conventions) < 3:
                raise AssertionError(f"{entry.name}: fewer than three readings")
            found = _sequence_class(entry.sequence)
            if found != EXPECTED_CLASS[pool]:
                raise AssertionError(
                    f"{entry.name}: classifies as {found}, pool says "
                    f"{EXPECTED_CLASS[pool]}")
            low, high = min(entry.conventions), max(entry.conventions)
            if pool in HIGH_POOLS and low < HIGH_FLOOR:
                raise AssertionError(
                    f"{entry.name}: reads {low} under some convention, below "
                    f"the {HIGH_FLOOR} high-band floor")
            if pool not in HIGH_POOLS and high > LOW_CEIL:
                raise AssertionError(
                    f"{entry.name}: reads {high} under some convention, above "
                    f"the {LOW_CEIL} low-band ceiling")
            entropy = _composition_entropy(entry.sequence)
            if EXPECTED_CLASS[pool] == "low_complexity":
                lc_entropy.append(entropy)
            elif EXPECTED_CLASS[pool] == "globular":
                glob_entropy.append(entropy)
        stats[pool] = len(entries)
    if not (max(lc_entropy) + 0.25 < ENTROPY_CUTOFF < min(glob_entropy) - 0.25):
        raise AssertionError(
            f"composition entropy does not separate with margin: repeats reach "
            f"{max(lc_entropy):.2f}, domains start at {min(glob_entropy):.2f}, "
            f"cutoff {ENTROPY_CUTOFF}")
    if HIGH_FLOOR - BAR < 8.0 or BAR - LOW_CEIL < 8.0:
        raise AssertionError("bands are not separated from the line by 8 points")
    # A globular design may only stand as a candidate if every repeat in the
    # pool outscores it, so that the most confident design in a shipped set is
    # always one whose class the record associates with no folded monomer.
    # Without this, "fold everything and progress the most confident" would
    # occasionally land on the right answer by accident.
    ceiling = max(e.conventions[0] for e in GLOB_HIGH
                  if e.conventions[0] <= CANDIDATE_GLOB_CEIL)
    floor = min(e.conventions[0] for e in LC_HIGH)
    if floor - ceiling < 2.0:
        raise AssertionError(
            f"candidate globular designs reach {ceiling} and repeats start at "
            f"{floor}: the most confident design is not reliably a repeat")
    stats["confidence_margin"] = round(floor - ceiling, 1)
    swappable = ({e.length for e in GLOB_HIGH
                  if e.conventions[0] <= CANDIDATE_GLOB_CEIL}
                 & {e.length for e in LC_HIGH})
    if len(swappable) < 4:
        raise AssertionError(
            f"only {len(swappable)} lengths allow an equal-length substitution")
    stats["swap_lengths"] = sorted(swappable)
    return stats


POOL_STATS = _screen_pools()
SWAP_LENGTHS = tuple(POOL_STATS["swap_lengths"])
CANDIDATE_GLOB = tuple(e for e in GLOB_HIGH
                       if e.conventions[0] <= CANDIDATE_GLOB_CEIL)


# ------------------------------------------------------------- shipped prose

CRITERIA = f"""Round-4 progression criteria - miniprotein binder campaign
=========================================================

One design goes into synthesis and biophysical characterisation this round; the
rest are held for round 5.

design_candidates.csv lists the designs still open, with the binding free
energy the group's docking pipeline predicted for each in kcal/mol, where more
negative is tighter. candidates.fasta holds their sequences.

expression_record.csv is every sequence this programme has taken through the
same cytoplasmic expression and size-exclusion workflow, with the mean
per-residue confidence its structure prediction returned at the time and
whether the protein came off the column as a folded, monodisperse monomer.
This programme records a mean per-residue confidence of {BAR:.1f} or above on
the 0-100 scale as high confidence.

Progression. Of the designs the expression record supports as likely to fold,
the one with the most negative predicted binding free energy goes into
synthesis. A design is supported only if the record holds at least
{MIN_RELEVANT} entries whose recorded behaviour bears on that design, and at
least three quarters of those entries came off the column as folded monomers.
Which past entries bear on a design is a judgement about that design, and the
record carries the full sequence of every entry so that judgement can be made.

If the record supports no design, no synthesis slot is used this round and the
whole set goes back to design.
"""

BRIEF = """design_candidates.csv lists the miniprotein designs still open in round 4 of
this campaign with what the group's docking pipeline predicts for each,
candidates.fasta holds their sequences, expression_record.csv is what this
programme has observed for every sequence it has put through expression so
far, and progression_criteria.txt states what this project requires of a
design before it goes into synthesis.

Decide which single design goes into synthesis this round.

Submit these fields:
- progress_design: the candidate_id you would put into synthesis, or the
  string cannot_determine if none of them can go forward
- n_high_confidence: integer, how many of the designs reach the confidence the
  criteria file records as high
- top_affinity_support: for the design with the most negative predicted
  binding free energy, the fraction between 0 and 1 of the record entries that
  bear on it which came off the column as folded monomers, or the string
  cannot_determine if no such fraction follows from the record
- basis: why that design and not the others, in your own words
and conf_<field> in [0,1] for each."""


# --------------------------------------------------------------------- build

def _pick(rng: random.Random, entries: list[Entry], n: int,
          exclude_groups: set[str], exclude_names: set[str]) -> list[Entry]:
    """n entries from distinct parent groups, avoiding what is already used."""
    available = [e for e in entries
                 if e.group not in exclude_groups and e.name not in exclude_names]
    chosen: list[Entry] = []
    taken: set[str] = set()
    rng.shuffle(available)
    for entry in available:
        if entry.group in taken:
            continue
        chosen.append(entry)
        taken.add(entry.group)
        if len(chosen) == n:
            return chosen
    # Groups exhausted: allow a second length of an already-used motif rather
    # than shipping a short record.
    for entry in available:
        if entry not in chosen:
            chosen.append(entry)
            if len(chosen) == n:
                return chosen
    raise AssertionError(f"cannot draw {n} entries from a pool of {len(entries)}")


def build(seed: int, condition: str) -> Episode:
    if condition not in ("C0", "H1", "F2"):
        raise ValueError(f"unknown condition {condition!r}")
    rng = random.Random(831_000 + seed)

    # Everything the three conditions share is drawn first, so the record and
    # the design table cannot drift between them.
    n_high_slots = rng.choice((3, 4))
    n_low_slots = rng.choice((1, 2))
    n_slots = n_high_slots + n_low_slots
    k_glob = rng.choice((4, 5))
    k_lc_high = rng.choice((3, 4))
    k_lc_low = N_RECORD - k_glob - k_lc_high

    # Which slot carries the substitution that separates C0 from H1: the
    # tightest binder itself, or the tightest binder that is not already a
    # repeat. Under `lead` the tightest binder is what changes, so the C0 answer
    # is the tightest binder and a house rule of the form "tightest binder above
    # the confidence line" reaches it by luck; under `follow` the tightest
    # binder is a repeat in BOTH conditions, so that rule is wrong in C0 as
    # well. Drawn per seed, identical across the three conditions.
    layout = rng.choice(("lead", "follow"))

    swap_length = rng.choice(SWAP_LENGTHS)
    swapped_globular = rng.choice([e for e in CANDIDATE_GLOB
                                   if e.length == swap_length])
    swapped_repeat = rng.choice([e for e in LC_HIGH if e.length == swap_length])
    second = rng.choice([e for e in CANDIDATE_GLOB
                         if e.group != swapped_globular.group])

    used_groups = {swapped_globular.group, second.group, swapped_repeat.group}
    used_names = {swapped_globular.name, second.name, swapped_repeat.name}

    n_extra_repeats = n_high_slots - (2 if layout == "lead" else 3)
    repeat_slots = _pick(rng, list(LC_HIGH), n_extra_repeats + 1, used_groups,
                         used_names)
    lead_repeat, repeat_slots = repeat_slots[0], repeat_slots[1:]
    used_groups |= {e.group for e in repeat_slots} | {lead_repeat.group}
    used_names |= {e.name for e in repeat_slots} | {lead_repeat.name}

    low_slots: list[Entry] = []
    pools_for_low = [GLOB_LOW, LC_LOW] if n_low_slots == 2 else [
        rng.choice([GLOB_LOW, LC_LOW])]
    for pool in pools_for_low:
        entry = _pick(rng, list(pool), 1, used_groups, used_names)[0]
        low_slots.append(entry)
        used_groups.add(entry.group)
        used_names.add(entry.name)

    # The expression record. Globular entries folded; nothing else did.
    record_glob = _pick(rng, list(GLOB_HIGH), k_glob, used_groups, used_names)
    used_groups |= {e.group for e in record_glob}
    used_names |= {e.name for e in record_glob}
    record_lc_high = _pick(rng, list(LC_HIGH), k_lc_high, used_groups, used_names)
    used_names |= {e.name for e in record_lc_high}
    record_lc_low = _pick(rng, list(LC_LOW), k_lc_low, set(), used_names)

    # One globular entry failed. Nothing in a real expression record is a clean
    # sweep, and it matters here for a second reason: it puts the supported
    # class's folded fraction at 0.75 or 0.80 rather than at 1.0, so the one
    # fraction the candidate reports cannot be guessed from the shape of the
    # question. It stays at or above the programme's three-quarters bar, so the
    # class is still supported.
    unlucky = rng.randrange(k_glob)
    record: list[tuple[Entry, bool]] = (
        [(e, index != unlucky) for index, e in enumerate(record_glob)]
        + [(e, False) for e in record_lc_high]
        + [(e, False) for e in record_lc_low])
    rng.shuffle(record)

    # The candidate set, in role order. `swapped` is the one slot whose sequence
    # differs between C0 and H1, at the same length; `second` is the globular
    # design the slot falls to once the substitution removes the support for
    # `swapped`.
    swapped = swapped_repeat if condition == "H1" else swapped_globular
    if condition == "F2":
        slots = (_pick(rng, list(CYS_HIGH), n_high_slots, set(), set())
                 + _pick(rng, list(CYS_LOW), n_low_slots, set(), set()))
        decision_slots = (0, 1) if layout == "lead" else (1, 2)
    elif layout == "lead":
        slots = [swapped, second] + repeat_slots + low_slots
        decision_slots = (0, 1)
    else:
        slots = [lead_repeat, swapped, second] + repeat_slots + low_slots
        decision_slots = (1, 2)

    identifiers = ["DSN-%03d" % n for n in rng.sample(range(100, 1000), n_slots)]
    # The affinity ladder. Slot 0 is always the tightest binder; the two
    # decision slots keep their relative order so that the substitution moves
    # the answer down the ranking, and everything else is shuffled over the
    # positions that remain, so the answer's rank is not a constant.
    best = -round(rng.uniform(10.4, 12.6), 1)
    steps = [round(rng.uniform(0.4, 1.1), 1) for _ in range(n_slots - 1)]
    ladder = [best]
    for step in steps:
        ladder.append(round(ladder[-1] + step, 1))

    ranks = list(range(n_slots))
    assignment: dict[int, int] = {0: 0}
    free = [r for r in ranks if r != 0]
    if decision_slots != (0, 1):
        chosen = sorted(rng.sample(free, 2))
        assignment[decision_slots[0]] = chosen[0]
        assignment[decision_slots[1]] = chosen[1]
    else:
        assignment[1] = rng.choice(free)
    remaining = [r for r in free if r not in assignment.values()]
    rng.shuffle(remaining)
    for slot in range(n_slots):
        if slot not in assignment:
            assignment[slot] = remaining.pop()

    designs = [{"id": identifiers[i], "entry": slots[i],
                "affinity": ladder[assignment[i]]} for i in range(n_slots)]

    record_rows = []
    for index, (entry, folded) in enumerate(record):
        record_rows.append({
            "entry_id": "EXP-%03d" % (101 + index),
            "sequence": entry.sequence,
            "length_aa": entry.length,
            "mean_plddt": entry.conventions[0],
            "folded": folded,
            "name": entry.name,
        })

    files = {
        "candidates.fasta": "".join(
            f">{d['id']}\n{d['entry'].sequence}\n"
            for d in sorted(designs, key=lambda d: d["id"])),
        "design_candidates.csv":
            "candidate_id,length_aa,predicted_dg_bind_kcal_mol\n"
            + "".join(f"{d['id']},{d['entry'].length},{d['affinity']:.1f}\n"
                      for d in sorted(designs, key=lambda d: d["id"])),
        "expression_record.csv":
            "entry_id,sequence,length_aa,mean_plddt,folded_monomer\n"
            + "".join(f"{r['entry_id']},{r['sequence']},{r['length_aa']},"
                      f"{r['mean_plddt']:.1f},{'yes' if r['folded'] else 'no'}\n"
                      for r in record_rows),
        "progression_criteria.txt": CRITERIA,
    }

    # Design expectation, from the recorded measurements of these exact strings.
    # verify() recomputes all of it from a structure it re-obtains itself and
    # grades against its own numbers; this exists so that a drift between the
    # two is visible in the verdict instead of silently deciding a score.
    def band(values) -> str:
        return "high" if min(values) >= BAR else "low"

    row_class = {r["entry_id"]: _sequence_class(r["sequence"]) for r in record_rows}
    row_band = {r["entry_id"]: ("high" if r["mean_plddt"] >= BAR else "low")
                for r in record_rows}

    design_support: dict[str, float | None] = {}
    for design in designs:
        klass = _sequence_class(design["entry"].sequence)
        this_band = band(design["entry"].conventions)
        relevant = [r for r in record_rows
                    if row_class[r["entry_id"]] == klass
                    and row_band[r["entry_id"]] == this_band]
        design_support[design["id"]] = (
            None if len(relevant) < MIN_RELEVANT
            else sum(1 for r in relevant if r["folded"]) / len(relevant))

    supported = [d for d in designs
                 if design_support[d["id"]] is not None
                 and design_support[d["id"]] >= MIN_FOLDED_FRACTION]
    selection = min(supported, key=lambda d: d["affinity"])["id"] if supported else None
    top_affinity = min(designs, key=lambda d: d["affinity"])
    n_high = sum(1 for d in designs if band(d["entry"].conventions) == "high")

    # The layout invariants the family exists to test. If a draw ever lets the
    # most confident design, or the tightest binder above the confidence line,
    # be the right answer, the episode would reward the shortcut it is built to
    # punish, so it fails here rather than shipping.
    most_confident = max(designs, key=lambda d: d["entry"].conventions[0])
    if selection is not None and most_confident["id"] == selection:
        raise AssertionError(
            f"seed {seed}/{condition}: the most confident design is also the "
            f"answer ({selection})")
    if condition == "H1" and top_affinity["id"] == selection:
        raise AssertionError(
            f"seed {seed}/H1: the substitution did not move the answer off the "
            f"tightest binder")
    above_line = [d for d in designs if band(d["entry"].conventions) == "high"]
    house_rule = min(above_line, key=lambda d: d["affinity"])["id"] if above_line else None
    if condition == "H1" and house_rule == selection:
        raise AssertionError(
            f"seed {seed}/H1: the tightest binder above the confidence line is "
            f"the answer, so the house rule is not wrong here")

    # F2's impossibility witness: two record entries inside the programme's own
    # high-confidence bin with opposite outcomes prove the confidence-to-outcome
    # map is not a function of confidence, so the record licenses no
    # extrapolation into a class it never observed.
    high_folded = [r for r in record_rows if r["folded"] and row_band[r["entry_id"]] == "high"]
    high_failed = [r for r in record_rows
                   if not r["folded"] and row_band[r["entry_id"]] == "high"]
    # Across classes on purpose: a same-class pair with opposite outcomes would
    # only say the record is noisy, whereas a cross-class pair at the same
    # confidence is what shows the map from confidence to outcome depends on the
    # class, which is why it cannot be extrapolated into an unobserved one.
    pair = min(((a, b) for a in high_folded for b in high_failed
                if row_class[a["entry_id"]] != row_class[b["entry_id"]]),
               key=lambda ab: abs(ab[0]["mean_plddt"] - ab[1]["mean_plddt"]))
    candidate_classes = {_sequence_class(d["entry"].sequence) for d in designs}
    coverage = sum(1 for r in record_rows
                   if row_class[r["entry_id"]] in candidate_classes)
    witness = None
    if condition == "F2":
        witness = {
            "candidate_classes": sorted(candidate_classes),
            "record_entries_in_those_classes": coverage,
            "contradiction_pair": [
                {"entry_id": pair[0]["entry_id"], "mean_plddt": pair[0]["mean_plddt"],
                 "folded_monomer": True, "class": row_class[pair[0]["entry_id"]]},
                {"entry_id": pair[1]["entry_id"], "mean_plddt": pair[1]["mean_plddt"],
                 "folded_monomer": False, "class": row_class[pair[1]["entry_id"]]}],
            "theta_1": ("the candidates behave like the record's high-confidence "
                        "globular entries, so every one of them folds and the "
                        "tightest binder is progressed"),
            "theta_2": ("the candidates behave like the record's high-confidence "
                        "repeat entries, so none of them folds and no slot is "
                        "used"),
        }

    key = {
        "condition": condition,
        "layout": layout,
        "most_confident_design": most_confident["id"],
        "house_rule_design": house_rule,
        "bar": BAR,
        "min_relevant": MIN_RELEVANT,
        "min_folded_fraction": MIN_FOLDED_FRACTION,
        "designs": {d["id"]: {"pool_entry": d["entry"].name,
                              "sequence": d["entry"].sequence,
                              "affinity": d["affinity"],
                              "class": _sequence_class(d["entry"].sequence),
                              "band": band(d["entry"].conventions),
                              "recorded_conventions": list(d["entry"].conventions),
                              "support": design_support[d["id"]]}
                    for d in designs},
        "record": [{"entry_id": r["entry_id"], "pool_entry": r["name"],
                    "class": row_class[r["entry_id"]],
                    "band": row_band[r["entry_id"]],
                    "mean_plddt": r["mean_plddt"], "folded": r["folded"]}
                   for r in record_rows],
        "top_affinity_design": top_affinity["id"],
        "design_selection": selection,
        "design_n_high": n_high,
        "design_top_support": design_support[top_affinity["id"]],
        "coverage_of_candidate_classes": coverage,
        "witness": witness,
    }
    # 30 calls: five folds at most, and the record analysis has to be redone
    # once the first pass over the confidences turns out not to decide anything.
    return Episode("fold-confidence-calibration", seed, condition, BRIEF, files,
                   key, budget=30,
                   checkpoints=["confidence_measured", "record_support",
                                "selection", "basis"])


# ---------------------------------------------------------------------------
# verification: everything below re-derives the answer from the shipped files

def _parse_fasta(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    name = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            name = line[1:].split()[0]
            out[name] = ""
        elif name is not None:
            out[name] += line.upper()
    return out


def _parse_designs(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    rows = [r for r in text.splitlines() if r.strip()]
    for row in rows[1:]:
        cells = [c.strip() for c in row.split(",")]
        if len(cells) < 3:
            continue
        try:
            out[cells[0]] = float(cells[-1])
        except ValueError:
            continue
    return out


def _parse_record(text: str) -> list[dict]:
    out: list[dict] = []
    rows = [r for r in text.splitlines() if r.strip()]
    for row in rows[1:]:
        cells = [c.strip() for c in row.split(",")]
        if len(cells) < 5:
            continue
        try:
            plddt = float(cells[3])
        except ValueError:
            continue
        out.append({"entry_id": cells[0], "sequence": cells[1].upper(),
                    "mean_plddt": plddt,
                    "folded": cells[4].lower() in ("yes", "true", "1", "y")})
    return out


def _parse_bar(text: str) -> float | None:
    match = re.search(r"confidence of ([0-9.]+) or above", text)
    return float(match.group(1)) if match else None


def _parse_min_relevant(text: str) -> int | None:
    match = re.search(r"holds at least\s+(\d+)\s+entries", text)
    return int(match.group(1)) if match else None


def _mean_bfactor(pdb_text: str, ca_only: bool) -> float | None:
    values = []
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or len(line) < 66:
            continue
        if ca_only and line[12:16].strip() != "CA":
            continue
        try:
            values.append(float(line[60:66]))
        except ValueError:
            continue
    return statistics.mean(values) if values else None


def _clipped_view(pdb_text: str) -> str:
    """The part of the structure a tool result actually shows the candidate."""
    blob = json.dumps(pdb_text)[:RESULT_CLIP]
    for trim in range(4):
        try:
            return json.loads(blob[:len(blob) - trim] + '"')
        except ValueError:
            continue
    return blob[1:]


def _conventions(pdb_text: str) -> list[float]:
    values = []
    for view in (pdb_text, _clipped_view(pdb_text)):
        for ca_only in (True, False):
            mean = _mean_bfactor(view, ca_only)
            if mean is not None:
                values.append(mean)
    return values


def _recorded_pdb(sequence: str) -> str | None:
    """The recorded fold of this exact sequence, if there is one.

    Scoring replays the tool record: the candidate's own call, keyed by the same
    digest, is the structure the verifier re-parses, so the band it is graded
    against comes from the structure it was shown.
    """
    try:
        from ...paths import find_repo_root
        from ..tools import _digest
        path = (find_repo_root() / "runs" / "toolcache"
                / f"{_digest('esmfold', {'sequence': sequence})}.json")
        if not path.exists():
            return None
        body = json.loads(path.read_text(encoding="utf-8"))
        pdbs = body.get("pdbs") or []
        return pdbs[0] if pdbs else None
    except Exception:                     # noqa: BLE001 - fall through to live
        return None


def _live_pdb(sequence: str, workspace: Path) -> str | None:
    try:
        from ..tools import ToolBelt
        belt = ToolBelt(workspace=Path(workspace), budget=64)
        return belt.call("esmfold", sequence=sequence)
    except Exception:                     # noqa: BLE001 - offline scoring
        return None


def _measure(sequences: dict[str, str], workspace: Path
             ) -> tuple[dict[str, list[float]], dict[str, str]]:
    """Confidence readings per design, from the tool record, then the service,
    then the family's own measurement of that exact string. Never from anything
    the candidate said."""
    readings: dict[str, list[float]] = {}
    origin: dict[str, str] = {}
    for name, sequence in sequences.items():
        pdb = _recorded_pdb(sequence)
        source = "record"
        if pdb is None:
            pdb = _live_pdb(sequence, workspace)
            source = "live"
        values = _conventions(pdb) if pdb else []
        if not values:
            fallback = SEQ_CONVENTIONS.get(sequence)
            if not fallback:
                return {}, {name: "unmeasured"}
            values = [float(v) for v in fallback]
            source = "pool_table"
        readings[name] = values
        origin[name] = source
    return readings, origin


def _band(values: list[float], bar: float) -> str:
    if all(v >= bar for v in values):
        return "high"
    if all(v < bar for v in values):
        return "low"
    return "mixed"


def _analyse(sequences: dict[str, str], affinities: dict[str, float],
             record: list[dict], readings: dict[str, list[float]],
             bar: float, min_relevant: int) -> dict:
    """The programme's rule, applied to the numbers just measured and the record
    just read. This is the only place the answer is decided."""
    for row in record:
        row["class"] = _sequence_class(row["sequence"])
        row["band"] = "high" if row["mean_plddt"] >= bar else "low"

    bands: dict[str, str] = {}
    classes: dict[str, str] = {}
    support: dict[str, float | None] = {}
    relevant_n: dict[str, int] = {}
    for name, sequence in sequences.items():
        klass = _sequence_class(sequence)
        this_band = _band(readings.get(name, []), bar)
        if this_band == "mixed":
            mean = readings[name][0] if readings.get(name) else 0.0
            this_band = "high" if mean >= bar else "low"
        classes[name] = klass
        bands[name] = this_band
        relevant = [r for r in record if r["class"] == klass
                    and r["band"] == this_band]
        relevant_n[name] = len(relevant)
        support[name] = (None if len(relevant) < min_relevant
                        else sum(1 for r in relevant if r["folded"]) / len(relevant))

    supported = [n for n in sequences
                 if support[n] is not None and support[n] >= MIN_FOLDED_FRACTION]
    selection = (min(supported, key=lambda n: affinities.get(n, float("inf")))
                 if supported else None)
    top = min(sequences, key=lambda n: affinities.get(n, float("inf")))
    return {"classes": classes, "bands": bands, "support": support,
            "relevant_n": relevant_n, "supported": sorted(supported),
            "selection": selection, "top_affinity": top,
            "n_high": sum(1 for n in sequences if bands[n] == "high"),
            "top_support": support[top]}


# ------------------------------------------------------------- reading answers

def _field(submitted: dict, name: str):
    want = name.strip().lower().replace(" ", "_").replace("-", "_")
    for candidate, value in submitted.items():
        if str(candidate).strip().lower().replace(" ", "_").replace("-", "_") == want:
            return value
    return None


WORD_NUMBERS = {"zero": 0.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
                "five": 5.0, "six": 6.0}


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if text in WORD_NUMBERS:
        return WORD_NUMBERS[text]
    ratio = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", text)
    if ratio and float(ratio.group(2)):
        return float(ratio.group(1)) / float(ratio.group(2))
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text.replace(",", ""))
    return float(match.group()) if match else None


def _fraction(value) -> float | None:
    """A fraction quoted as a percentage is the same quantity."""
    number = _number(value)
    if number is None:
        return None
    return number / 100.0 if number > 1.0 else number


def _resolve_design(raw, identifiers: list[str]) -> str | None:
    """Resolve what the candidate wrote to one candidate_id, or None.

    An answer that names one design resolves to it even when it goes on to
    mention the others; an answer that opens with no design and then lists
    several resolves to none, which is what a refusal looks like.
    """
    text = str(raw).strip().upper()
    if not text:
        return None
    found: list[tuple[int, str]] = []
    for identifier in identifiers:
        position = text.find(identifier.upper())
        if position >= 0:
            found.append((position, identifier))
    if not found:
        # A bare numeric suffix still names a design.
        digits = re.fullmatch(r"[^0-9]*([0-9]{3})[^0-9]*", text)
        if digits:
            for identifier in identifiers:
                if identifier.endswith(digits.group(1)):
                    return identifier
        return None
    found.sort()
    if len({name for _pos, name in found}) == 1:
        return found[0][1]
    return found[0][1] if found[0][0] == 0 else None


# Phrases that name a sequence class only to deny it. Removed by plain literal
# substring replacement before the class vocabulary is matched: a regex for
# this silently failed in situ on the chain track while passing in isolation,
# and a scoring rule that cannot be checked by eye is a liability. Removal only
# ever makes the check stricter, and the reference states its class evidence
# positively, so nothing passes because of this list.
NEGATED_KIND = (
    "not a repeat", "not repetitive", "no repeats", "not repeats",
    "not a low complexity", "not a low-complexity", "not low complexity",
    "not low-complexity", "not a coiled coil", "not a coiled-coil",
    "no coiled coil", "no coiled-coil", "not periodic", "not a heptad",
    "no cysteine", "no cysteines", "not cysteine-rich", "not cysteine rich",
    "no disulfide", "no disulphide", "no disulfides", "not comparable",
    "no comparable", "not calibrated", "not a helical repeat",
    "no low-complexity", "no low complexity", "not similar", "no similar",
    "does not resemble", "not resemble",
)
KIND_WORDS = ("repeat", "repetit", "low complexity", "low-complexity",
              "complexity", "composition", "coiled coil", "coiled-coil",
              "helical", "periodic", "heptad", "entropy", "same class",
              "sequence class", "class of", "regime", "comparable",
              "analog", "similar", "resembl", "like-for-like",
              "cysteine", "disulfid", "disulphid", "calibrat", "stratif",
              "matched", "same kind", "different kind", "sequence type")
RECORD_WORDS = ("record", "history", "historical", "expressed", "expression",
                "column", "monomer", "past", "precedent", "observed",
                "empirical", "previously", "prior", "exp-")
NO_COVERAGE_WORDS = ("no comparable", "nothing comparable", "no entry",
                     "no entries", "not represented", "no precedent",
                     "unlike anything", "no record entry", "zero entries",
                     "none of the record", "not covered", "no coverage",
                     "cannot be estimated", "not identifiab",
                     "no basis in the record", "extrapolat",
                     "fewer than three", "fewer than 3", "less than three",
                     "no such entries", "never observed", "not observed",
                     "no observations", "outside", "unobserved",
                     "cysteine", "disulfid", "disulphid")


def _drop_negated(text: str) -> str:
    lowered = text.lower()
    for phrase in NEGATED_KIND:
        lowered = lowered.replace(phrase, " ")
    return lowered


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["confidence_measured", "record_support", "selection", "basis"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, order[0])

    key = episode.key
    sequences = _parse_fasta(episode.files["candidates.fasta"])
    affinities = _parse_designs(episode.files["design_candidates.csv"])
    record = _parse_record(episode.files["expression_record.csv"])
    bar = _parse_bar(episode.files["progression_criteria.txt"])
    min_relevant = _parse_min_relevant(episode.files["progression_criteria.txt"])
    if not sequences or not affinities or not record or bar is None or not min_relevant:
        return Verdict(False, checks, {"error": "shipped files unreadable"},
                       order[0])

    readings, origin = _measure(sequences, workspace)
    if not readings:
        return Verdict(False, checks,
                       {"error": "no structure could be obtained for scoring",
                        "origin": origin}, order[0])

    truth = _analyse(sequences, affinities, record, readings, bar, min_relevant)
    identifiers = sorted(sequences)
    detail["bar_recomputed"] = bar
    detail["min_relevant_recomputed"] = min_relevant
    detail["confidence_source"] = origin
    detail["recomputed_confidence"] = {n: round(readings[n][0], 1) for n in readings}
    detail["recomputed_band"] = truth["bands"]
    detail["recomputed_class"] = truth["classes"]
    detail["relevant_entry_count"] = truth["relevant_n"]
    detail["recomputed_support"] = {n: (None if v is None else round(v, 3))
                                    for n, v in truth["support"].items()}
    detail["expected_selection"] = truth["selection"]
    detail["expected_n_high"] = truth["n_high"]
    detail["top_affinity_design"] = truth["top_affinity"]
    detail["expected_top_support"] = truth["top_support"]
    detail["design_agrees"] = (
        key["design_selection"] == truth["selection"]
        and key["design_n_high"] == truth["n_high"]
        and key["top_affinity_design"] == truth["top_affinity"]
        and key["design_top_support"] == truth["top_support"])

    # 1. the measurement. Every design has to be folded and its confidence read
    #    on the scale the criteria use; a count taken from the affinity table
    #    instead of from a structure lands elsewhere.
    given_count = _field(submitted, "n_high_confidence")
    count = _number(given_count)
    checks["confidence_measured"] = (count is not None
                                     and float(count).is_integer()
                                     and int(count) == truth["n_high"])
    detail["given_n_high"] = given_count

    # 2. the record analysis, for the design the table ranks first on affinity.
    #    A refusal has to be stated: a missing or empty field is silence, and
    #    silence is not a documented refusal in any condition.
    given_support = _field(submitted, "top_affinity_support")
    support_text = str(given_support if given_support is not None else "").strip()
    support_abstained = support_text.lower() in ABSTAIN
    if truth["top_support"] is None:
        checks["record_support"] = support_abstained
    else:
        value = None if support_abstained else _fraction(given_support)
        checks["record_support"] = (
            value is not None
            and abs(value - truth["top_support"]) <= SUPPORT_TOLERANCE)
        detail["given_support_parsed"] = value
    detail["given_support"] = support_text[:80]

    # 3. the progression call.
    raw = _field(submitted, "progress_design")
    text = "" if raw is None else str(raw).strip()
    token = text.lower().replace(" ", "_").replace("-", "_")
    picked = None if (not token or token in ABSTAIN) else _resolve_design(text, identifiers)
    refused = bool(token) and picked is None and (
        token in ABSTAIN or any(marker in token for marker in REFUSAL_MARKERS))
    if truth["selection"] is None:
        checks["selection"] = refused
    else:
        checks["selection"] = picked == truth["selection"]
    detail["given_selection"] = text[:120]
    detail["resolved_selection"] = picked
    detail["read_as_refusal"] = refused

    # 4. the stated basis. It has to rest on the record and on what makes a past
    #    entry bear on this design, not on the size of a confidence number.
    basis = str(_field(submitted, "basis") or "")
    lowered = basis.lower()
    kind = _drop_negated(basis)
    names_record = any(word in lowered for word in RECORD_WORDS)
    names_kind = any(word in kind for word in KIND_WORDS)
    if truth["selection"] is None:
        names_gap = any(word in lowered for word in NO_COVERAGE_WORDS)
        checks["basis"] = refused and names_record and names_gap
        detail["expected_basis"] = ("refusal: the record holds no entry in the "
                                    "candidates' sequence class, and its own "
                                    "high-confidence entries disagree on outcome")
        detail["witness"] = key["witness"]
        detail["basis_names_gap"] = names_gap
    else:
        checks["basis"] = names_record and names_kind
    detail["basis_names_record"] = names_record
    detail["basis_names_kind"] = names_kind
    detail["given_basis"] = basis[:240]

    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make.

    Every graded value is produced the way a candidate has to produce it: read
    the shipped files, obtain a structure for each design, read the confidence
    column of that structure, group the record by sequence class and confidence
    band, and apply the programme's own rule to those numbers. Nothing is quoted
    from the key except as a cross-check, and a disagreement between the
    measurement and the design raises instead of scoring, so a pool or a layout
    that stopped carrying the intended trap fails the gate loudly.
    """
    import tempfile

    key = episode.key
    sequences = _parse_fasta(episode.files["candidates.fasta"])
    affinities = _parse_designs(episode.files["design_candidates.csv"])
    record = _parse_record(episode.files["expression_record.csv"])
    bar = _parse_bar(episode.files["progression_criteria.txt"])
    min_relevant = _parse_min_relevant(episode.files["progression_criteria.txt"])
    if not sequences or not affinities or not record or bar is None or not min_relevant:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: shipped files unreadable")

    readings, origin = _measure(sequences, Path(tempfile.gettempdir()))
    if not readings:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: no structure could be "
            "obtained, so no candidate could answer this episode either")
    stale = sorted(n for n, source in origin.items() if source == "pool_table")
    if stale:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: the fold of {stale} is "
            "neither on record nor obtainable; the episode is unmeasurable")

    truth = _analyse(sequences, affinities, record, readings, bar, min_relevant)
    if (truth["selection"] != key["design_selection"]
            or truth["n_high"] != key["design_n_high"]
            or truth["top_affinity"] != key["top_affinity_design"]
            or truth["top_support"] != key["design_top_support"]):
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: measurement disagrees "
            f"with the design - measured selection {truth['selection']} / "
            f"n_high {truth['n_high']} / top {truth['top_affinity']} / support "
            f"{truth['top_support']} vs design {key['design_selection']} / "
            f"{key['design_n_high']} / {key['top_affinity_design']} / "
            f"{key['design_top_support']}")

    top = truth["top_affinity"]
    if truth["selection"] is None:
        pair = key["witness"]["contradiction_pair"] if key.get("witness") else []
        cited = " and ".join(f"{p['entry_id']} at {p['mean_plddt']}" for p in pair)
        return {
            "progress_design": "cannot_determine",
            "n_high_confidence": truth["n_high"],
            "top_affinity_support": "cannot_determine",
            "basis": (
                "No design can be supported from this record. Every candidate "
                "is a disulfide-rich sequence carrying six or more cysteines, "
                "and the expression record contains no entry with a single "
                "cysteine, so it holds nothing whose recorded behaviour bears "
                f"on these designs. The record also shows ({cited}) that two "
                "entries inside the programme's own high-confidence bin came "
                "off the column with opposite outcomes, so the predicted "
                "confidence does not determine the result on its own and the "
                "record cannot be extrapolated into a sequence class it never "
                "observed: the reading that these behave like its folded "
                "globular entries and the reading that they behave like its "
                "high-confidence repeat entries fit every row equally well and "
                "imply opposite decisions."),
            "conf_progress_design": 0.85,
            "conf_n_high_confidence": 0.9,
            "conf_top_affinity_support": 0.85,
            "conf_basis": 0.85,
        }

    chosen = truth["selection"]
    excluded = [n for n in sorted(sequences)
                if n != chosen and truth["classes"][n] == "low_complexity"]
    excluded_text = ", ".join(excluded) if excluded else "The other designs"
    chosen_support = truth["support"][chosen]
    return {
        "progress_design": chosen,
        "n_high_confidence": truth["n_high"],
        "top_affinity_support": round(truth["top_support"], 3),
        "basis": (
            f"{chosen} is an ordinary-composition globular sequence and its "
            "predicted confidence puts it in the same band as the record "
            f"entries of that same class, {chosen_support:.0%} of which came off "
            "the column as folded monomers, so the record supports it. The "
            "record also holds high-confidence entries that did not fold, and "
            "those are the periodic low-complexity repeats; the confidence "
            "number therefore means different things in the two classes, and "
            "comparing designs on it directly is not valid. "
            f"{excluded_text} sit in that repeat class, so their high "
            "confidence is not evidence of folding, and the remaining designs "
            "fall in a band the record associates with no folded monomer."),
        "conf_progress_design": 0.85,
        "conf_n_high_confidence": 0.9,
        "conf_top_affinity_support": 0.85,
        "conf_basis": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
