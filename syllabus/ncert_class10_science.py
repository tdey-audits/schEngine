from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower().replace("-", " ").replace("_", " "))


CBSE_QUESTION_TYPES = (
    "mcq",
    "assertion_reason",
    "vsa",
    "sa",
    "la",
    "case_study",
)

TYPE_MARKS_MAP: dict[str, int] = {
    "mcq": 1, "assertion_reason": 1,
    "vsa": 2, "sa": 3, "la": 5, "case_study": 4,
}

QUESTION_TYPE_ALIASES = {
    "sa_i": "vsa",
    "sa_ii": "sa",
}

HARDNESS_MARKS: dict[str, tuple[int, int]] = {
    "simple": (1, 2),
    "medium": (2, 3),
    "hard": (4, 5),
}


@dataclass(frozen=True)
class Subtopic:
    name: str
    aliases: tuple[str, ...] = ()
    focus_terms: tuple[str, ...] = ()
    cbse_types: tuple[str, ...] = ("vsa", "sa")
    hardness_default: str = "medium"


@dataclass(frozen=True)
class Chapter:
    number: int
    name: str
    aliases: tuple[str, ...]
    focus_terms: tuple[str, ...]
    subtopics: tuple[Subtopic, ...]
    suggested_types: tuple[str, ...] = CBSE_QUESTION_TYPES
    marks_distribution: tuple[int, ...] = (1, 2, 3, 4, 5)


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(1, "Chemical Reactions and Equations",
        ("chemical reactions", "chemical equations", "reactions and equations"),
        ("balanced equation", "oxidation", "reduction", "redox", "combination", "decomposition", "displacement", "precipitation"),
        (
            Subtopic("chemical equations and balancing", ("balancing equations",), ("balanced", "equation", "coefficients"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("types of chemical reactions", ("combination reaction", "decomposition reaction", "displacement reaction"), ("combination", "decomposition", "displacement", "double displacement"), ("mcq", "assertion_reason", "vsa", "sa"), "medium"),
            Subtopic("oxidation and reduction", ("redox", "oxidation reduction"), ("oxidation", "reduction", "oxidising agent", "reducing agent"), ("vsa", "sa", "la"), "hard"),
            Subtopic("corrosion and rancidity", ("rancidity", "corrosion"), ("corrosion", "rancidity", "prevent"), ("mcq", "vsa", "case_study"), "simple"),
        )),
    Chapter(2, "Acids, Bases and Salts",
        ("acids bases salts", "acids and bases", "salts"),
        ("indicator", "ph", "neutralisation", "bleaching powder", "baking soda", "washing soda", "plaster of paris"),
        (
            Subtopic("chemical properties of acids and bases", ("properties of acids", "properties of bases"), ("metal", "carbonate", "hydrogen", "neutralisation"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("pH and indicators", ("ph scale", "indicators"), ("ph", "indicator", "universal indicator"), ("mcq", "assertion_reason", "vsa", "case_study"), "simple"),
            Subtopic("important salts and their uses", ("bleaching powder", "baking soda", "washing soda", "plaster of paris"), ("salt", "preparation", "uses"), ("vsa", "sa", "la"), "medium"),
        )),
    Chapter(3, "Metals and Non-metals",
        ("metals non metals", "metals and nonmetals"),
        ("reactivity series", "ionic compounds", "extraction", "corrosion", "ore", "alloy"),
        (
            Subtopic("physical and chemical properties", ("properties of metals", "properties of non metals"), ("lustre", "malleable", "ductile", "oxide"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("reactivity series and displacement", ("reactivity", "displacement"), ("reactivity series", "displacement", "metal salt"), ("mcq", "assertion_reason", "sa"), "medium"),
            Subtopic("ionic compounds", ("formation of ionic compounds",), ("electron transfer", "ions", "high melting point"), ("vsa", "sa"), "medium"),
            Subtopic("extraction and corrosion", ("metallurgy", "corrosion"), ("ore", "roasting", "calcination", "electrolytic refining", "rusting"), ("sa", "la", "case_study"), "hard"),
        )),
    Chapter(4, "Carbon and its Compounds",
        ("carbon compounds", "carbon and compounds"),
        ("covalent bonding", "saturated", "unsaturated", "homologous series", "ethanol", "ethanoic acid", "soap"),
        (
            Subtopic("covalent bonding in carbon", ("covalent bond", "tetravalency"), ("tetravalency", "catenation", "covalent"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("hydrocarbons and homologous series", ("hydrocarbons", "homologous series"), ("alkane", "alkene", "alkyne", "functional group"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("ethanol and ethanoic acid", ("ethanol", "ethanoic acid"), ("properties", "esterification", "saponification"), ("vsa", "sa", "la"), "medium"),
            Subtopic("soaps and detergents", ("soap", "detergent"), ("micelle", "hard water", "cleansing action"), ("sa", "case_study"), "hard"),
        )),
    Chapter(5, "Periodic Classification of Elements",
        ("periodic classification", "periodic table", "classification of elements"),
        ("dobereiner", "newlands", "mendeleev", "modern periodic law", "period", "group", "valency"),
        (
            Subtopic("early attempts at classification", ("dobereiner triads", "newlands octaves", "mendeleev"), ("triads", "octaves", "mendeleev"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("modern periodic table", ("modern periodic law",), ("atomic number", "period", "group", "shells"), ("mcq", "assertion_reason", "sa"), "medium"),
            Subtopic("periodic trends", ("trends", "periodic properties"), ("valency", "atomic size", "metallic character"), ("vsa", "sa", "case_study"), "medium"),
        )),
    Chapter(6, "Life Processes",
        ("life processes",),
        ("nutrition", "respiration", "transportation", "excretion", "photosynthesis"),
        (
            Subtopic("nutrition in plants and animals", ("nutrition", "photosynthesis", "digestion"), ("autotrophic", "heterotrophic", "stomata", "enzymes"), ("mcq", "vsa", "sa", "case_study"), "medium"),
            Subtopic("respiration", ("aerobic respiration", "anaerobic respiration"), ("mitochondria", "ATP", "lungs", "alveoli"), ("mcq", "assertion_reason", "sa"), "medium"),
            Subtopic("transportation", ("transport in humans", "transport in plants"), ("heart", "blood", "xylem", "phloem"), ("vsa", "sa", "la", "case_study"), "medium"),
            Subtopic("excretion", ("excretory system", "nephron"), ("kidney", "nephron", "urine", "dialysis"), ("vsa", "sa", "la"), "hard"),
        )),
    Chapter(7, "Control and Coordination",
        ("control coordination", "nervous system", "hormones"),
        ("reflex action", "brain", "neuron", "plant hormones", "endocrine glands"),
        (
            Subtopic("nervous system and reflex action", ("reflex action", "neuron"), ("receptor", "synapse", "spinal cord"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("coordination in plants", ("plant hormones", "tropism"), ("auxin", "phototropism", "geotropism"), ("mcq", "assertion_reason", "sa"), "medium"),
            Subtopic("hormones in animals", ("endocrine glands", "animal hormones"), ("thyroxine", "adrenaline", "insulin", "feedback"), ("vsa", "sa", "case_study"), "medium"),
        )),
    Chapter(8, "How do Organisms Reproduce?",
        ("reproduction", "organisms reproduce"),
        ("asexual reproduction", "sexual reproduction", "pollination", "fertilisation", "contraception"),
        (
            Subtopic("asexual reproduction", ("fission", "budding", "vegetative propagation"), ("binary fission", "budding", "spore", "regeneration"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("sexual reproduction in flowering plants", ("flower reproduction", "pollination"), ("stamen", "carpel", "pollination", "fertilisation"), ("vsa", "sa", "case_study"), "medium"),
            Subtopic("human reproduction", ("reproductive system",), ("puberty", "male reproductive system", "female reproductive system"), ("mcq", "sa", "la"), "medium"),
            Subtopic("reproductive health", ("contraception", "std"), ("contraceptive", "STI", "population"), ("vsa", "sa"), "simple"),
        )),
    Chapter(9, "Heredity and Evolution",
        ("heredity evolution", "genetics"),
        ("traits", "mendel", "dominant", "recessive", "sex determination", "evolution"),
        (
            Subtopic("heredity and inherited traits", ("traits", "inheritance"), ("variation", "dominant", "recessive"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("mendel's experiments", ("mendel", "monohybrid cross"), ("pea plant", "F1", "F2", "ratio"), ("sa", "la", "case_study"), "hard"),
            Subtopic("sex determination", ("sex determination",), ("chromosome", "XX", "XY"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("evolution", ("speciation", "evolution"), ("natural selection", "fossils", "homologous", "analogous"), ("vsa", "sa"), "medium"),
        )),
    Chapter(10, "Light - Reflection and Refraction",
        ("light reflection refraction", "reflection and refraction", "light"),
        ("mirror", "lens", "refraction", "refractive index", "power", "focal length"),
        (
            Subtopic("reflection by spherical mirrors", ("spherical mirrors", "mirror formula"), ("concave", "convex", "focal length", "magnification"), ("mcq", "vsa", "sa", "la"), "medium"),
            Subtopic("refraction of light", ("refraction", "refractive index"), ("glass slab", "Snell", "refractive index"), ("mcq", "assertion_reason", "sa", "case_study"), "medium"),
            Subtopic("lenses and power", ("lens formula", "power of lens"), ("convex lens", "concave lens", "dioptre", "magnification"), ("vsa", "sa", "la"), "hard"),
        )),
    Chapter(11, "The Human Eye and the Colourful World",
        ("human eye", "colourful world", "colorful world"),
        ("accommodation", "myopia", "hypermetropia", "prism", "dispersion", "scattering"),
        (
            Subtopic("human eye and defects of vision", ("defects of vision", "eye"), ("retina", "accommodation", "myopia", "hypermetropia"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("dispersion and atmospheric refraction", ("dispersion", "prism"), ("spectrum", "rainbow", "twinkling", "advanced sunrise"), ("mcq", "assertion_reason", "sa"), "medium"),
            Subtopic("scattering of light", ("scattering", "tyndall effect"), ("Tyndall", "blue sky", "red sunset"), ("vsa", "sa", "case_study"), "medium"),
        )),
    Chapter(12, "Electricity",
        ("electricity", "electric current"),
        ("current", "potential difference", "ohm law", "resistance", "series", "parallel", "heating effect", "power"),
        (
            Subtopic("current and potential difference", ("current", "potential difference"), ("charge", "ampere", "volt", "circuit"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("ohm's law and resistance", ("ohm law", "resistance"), ("V=IR", "resistivity", "resistor"), ("mcq", "assertion_reason", "sa", "case_study"), "medium"),
            Subtopic("resistors in series and parallel", ("series parallel", "resistor combinations"), ("equivalent resistance", "series", "parallel"), ("sa", "la"), "hard"),
            Subtopic("heating effect and electric power", ("heating effect", "electric power"), ("Joule", "power", "energy", "fuse"), ("vsa", "sa", "la"), "medium"),
        )),
    Chapter(13, "Magnetic Effects of Electric Current",
        ("magnetic effects", "magnetism", "electric current magnetic"),
        ("magnetic field", "right hand thumb rule", "solenoid", "motor", "electromagnetic induction", "domestic circuit"),
        (
            Subtopic("magnetic field due to current", ("magnetic field", "right hand thumb rule"), ("field lines", "straight conductor", "circular loop", "solenoid"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("force on current-carrying conductor", ("motor principle", "fleming left hand"), ("force", "motor", "Fleming"), ("mcq", "assertion_reason", "sa"), "medium"),
            Subtopic("electromagnetic induction", ("induction", "generator", "fleming right hand"), ("induced current", "generator", "AC", "DC"), ("vsa", "sa", "la"), "hard"),
            Subtopic("domestic electric circuits", ("domestic circuit", "earthing"), ("fuse", "earthing", "live wire", "neutral wire"), ("vsa", "sa", "case_study"), "simple"),
        )),
    Chapter(14, "Sources of Energy",
        ("sources of energy", "energy sources"),
        ("fossil fuels", "thermal power", "hydro power", "biomass", "wind", "solar", "nuclear"),
        (
            Subtopic("good source of energy", ("characteristics of energy source",), ("efficient", "available", "pollution"), ("mcq", "vsa"), "simple"),
            Subtopic("conventional sources of energy", ("fossil fuels", "thermal power", "hydro power"), ("coal", "petroleum", "hydro", "biomass"), ("vsa", "sa"), "medium"),
            Subtopic("alternative and non-conventional sources", ("solar energy", "wind energy", "nuclear energy"), ("solar", "wind", "tidal", "geothermal", "nuclear"), ("sa", "case_study"), "medium"),
        )),
    Chapter(15, "Our Environment",
        ("our environment", "environment"),
        ("ecosystem", "food chain", "food web", "biomagnification", "ozone", "waste"),
        (
            Subtopic("ecosystem and food chains", ("food chain", "food web"), ("producer", "consumer", "decomposer", "trophic level"), ("mcq", "vsa", "sa", "case_study"), "medium"),
            Subtopic("biomagnification", ("biological magnification",), ("pesticide", "accumulation", "top consumer"), ("vsa", "sa"), "medium"),
            Subtopic("ozone layer and waste management", ("ozone depletion", "waste"), ("CFC", "ozone", "biodegradable", "non-biodegradable"), ("mcq", "assertion_reason", "sa"), "simple"),
        )),
    Chapter(16, "Sustainable Management of Natural Resources",
        ("sustainable management", "natural resources", "management of natural resources"),
        ("reduce reuse recycle", "forest", "water harvesting", "coal petroleum", "stakeholders"),
        (
            Subtopic("sustainable resource management", ("sustainable development", "three r"), ("reduce", "reuse", "recycle", "stakeholders"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("forest and wildlife conservation", ("forests", "wildlife"), ("biodiversity", "stakeholders", "conservation"), ("vsa", "sa", "case_study"), "medium"),
            Subtopic("water, coal and petroleum", ("water harvesting", "coal petroleum"), ("dams", "water harvesting", "fossil fuels"), ("sa", "la"), "medium"),
        )),
)

CHAPTER_NAME_BY_NUMBER = {chapter.number: chapter.name for chapter in CHAPTERS}


def resolve(query: str) -> tuple[Chapter, Subtopic | None]:
    query_norm = _normalize(query)
    best_chapter: Chapter | None = None
    best_subtopic: Subtopic | None = None
    best_score = 0.0

    for ch in CHAPTERS:
        ch_terms = {_normalize(t) for t in (ch.name, *ch.aliases, *ch.focus_terms)}
        score = _phrase_score(query_norm, ch_terms)
        if score > best_score:
            best_chapter, best_subtopic, best_score = ch, None, score

        for sub in ch.subtopics:
            sub_terms = {_normalize(t) for t in (sub.name, *sub.aliases, *sub.focus_terms)}
            score = _phrase_score(query_norm, ch_terms | sub_terms)
            if score > best_score:
                best_chapter, best_subtopic, best_score = ch, sub, score

    if best_chapter is None:
        best_chapter = CHAPTERS[0]
    return best_chapter, best_subtopic


def _phrase_score(query: str, terms: set[str]) -> float:
    score = 0.0
    for term in terms:
        if not term:
            continue
        if term == query:
            score += 4.0
        elif term in query:
            score += 2.0
    return score


def normalize_question_type(question_type: str) -> str:
    return QUESTION_TYPE_ALIASES.get(question_type, question_type)


def marks_for_type(question_type: str) -> int:
    question_type = normalize_question_type(question_type)
    return TYPE_MARKS_MAP.get(question_type, 3)


def hardness_from_marks(marks: int) -> str:
    for level, (lo, hi) in HARDNESS_MARKS.items():
        if lo <= marks <= hi:
            return level
    return "medium"


def list_chapters() -> list[dict[str, Any]]:
    return [
        {
            "number": ch.number,
            "name": ch.name,
            "aliases": list(ch.aliases),
            "subtopics": [s.name for s in ch.subtopics],
            "question_types": list(ch.suggested_types),
        }
        for ch in CHAPTERS
    ]


def list_question_types() -> list[dict[str, Any]]:
    return [
        {"type": t, "marks": TYPE_MARKS_MAP[t],
         "description": _TYPE_DESC[t], "example": _TYPE_EXAMPLE[t]}
        for t in CBSE_QUESTION_TYPES
    ]


_TYPE_DESC = {
    "mcq": "Multiple Choice Question - select correct option",
    "assertion_reason": "Assertion (A) and Reason (R) - mark correct option",
    "vsa": "Very Short Answer - 2-mark science response",
    "sa": "Short Answer - explanation, diagram, or application",
    "la": "Long Answer - detailed explanation or multi-part reasoning",
    "case_study": "Case Study - source-based unit with sub-questions",
}

_TYPE_EXAMPLE = {
    "mcq": "Which gas is evolved when zinc reacts with dilute hydrochloric acid?",
    "assertion_reason": "Assertion (A): Silver chloride turns grey in sunlight. Reason (R): It decomposes to silver.",
    "vsa": "Why is respiration considered an exothermic reaction?",
    "sa": "Explain how stomata regulate exchange of gases in plants.",
    "la": "Describe an activity to show that acids react with metal carbonates to evolve carbon dioxide.",
    "case_study": "A household circuit contains appliances connected in parallel... (sub-questions)",
}


def hardness_marks_range(hardness: str) -> tuple[int, int]:
    return HARDNESS_MARKS.get(hardness, (2, 3))
