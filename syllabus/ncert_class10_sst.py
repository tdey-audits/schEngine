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
    "map_skill",
)

TYPE_MARKS_MAP: dict[str, int] = {
    "mcq": 1,
    "assertion_reason": 1,
    "vsa": 2,
    "sa": 3,
    "la": 5,
    "case_study": 4,
    "map_skill": 5,
}

QUESTION_TYPE_ALIASES = {
    "source_based": "case_study",
    "case_based": "case_study",
    "map": "map_skill",
    "map_based": "map_skill",
    "map_skill_based": "map_skill",
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
    stream: str
    aliases: tuple[str, ...]
    focus_terms: tuple[str, ...]
    subtopics: tuple[Subtopic, ...]
    suggested_types: tuple[str, ...] = CBSE_QUESTION_TYPES
    marks_distribution: tuple[int, ...] = (1, 2, 3, 4, 5)


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(1, "The Rise of Nationalism in Europe", "history",
        ("rise of nationalism", "nationalism in europe", "french revolution and nationalism"),
        ("nation state", "liberalism", "conservatism", "unification", "germany", "italy", "balkan"),
        (
            Subtopic("French Revolution and nationalism", ("french revolution",), ("liberty", "nation", "citizen"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("Unification of Germany and Italy", ("germany and italy",), ("bismarck", "garibaldi", "cavour"), ("mcq", "sa", "la", "map_skill"), "medium"),
            Subtopic("Nationalism and imperialism", ("balkan nationalism",), ("balkan", "imperialism", "conflict"), ("sa", "la"), "hard"),
        )),
    Chapter(2, "Nationalism in India", "history",
        ("indian nationalism", "freedom movement", "national movement"),
        ("non cooperation", "civil disobedience", "salt march", "satyagraha", "khilafat", "congress"),
        (
            Subtopic("Non-Cooperation Movement", ("non cooperation",), ("khilafat", "boycott", "swaraj"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("Civil Disobedience Movement", ("salt march", "dandi march"), ("salt", "poorna swaraj", "gandhiji"), ("sa", "la", "case_study"), "medium"),
            Subtopic("Participation of social groups", ("social groups",), ("peasants", "workers", "tribals", "women"), ("sa", "la"), "hard"),
        )),
    Chapter(3, "The Making of a Global World", "history",
        ("global world", "globalisation history", "world economy"),
        ("silk routes", "corn laws", "indentured labour", "great depression", "bretton woods"),
        (
            Subtopic("Pre-modern trade and routes", ("silk routes",), ("trade", "religion", "culture"), ("mcq", "vsa"), "simple"),
            Subtopic("Nineteenth century world economy", ("nineteenth century economy",), ("corn laws", "labour", "capital"), ("sa", "la"), "medium"),
            Subtopic("Inter-war economy and Bretton Woods", ("great depression", "bretton woods"), ("depression", "IMF", "World Bank"), ("sa", "case_study"), "hard"),
        )),
    Chapter(4, "The Age of Industrialisation", "history",
        ("age of industrialization", "industrial revolution", "industrialisation"),
        ("proto industrialisation", "factories", "workers", "manchester", "handloom", "market"),
        (
            Subtopic("Proto-industrialisation and factories", ("proto industrialisation",), ("merchant", "countryside", "factory"), ("mcq", "sa"), "medium"),
            Subtopic("Industrialisation in colonies", ("industrialisation in india",), ("weavers", "gomasthas", "manchester"), ("sa", "la"), "medium"),
            Subtopic("Market for goods", ("advertisements", "labels"), ("brand", "calendar", "nationalist message"), ("vsa", "case_study"), "simple"),
        )),
    Chapter(5, "Print Culture and the Modern World", "history",
        ("print culture", "modern world", "printing press"),
        ("gutenberg", "print revolution", "reformation", "newspapers", "novels", "censorship"),
        (
            Subtopic("Print revolution in Europe", ("gutenberg press",), ("books", "reading public", "reformation"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("Print in India", ("printing in india",), ("newspapers", "religious reform", "women readers"), ("sa", "la"), "medium"),
            Subtopic("Print and censorship", ("censorship",), ("vernacular press", "colonial state"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(6, "Resources and Development", "geography",
        ("resources", "resource planning", "development of resources"),
        ("renewable", "non renewable", "resource planning", "soil", "land degradation", "conservation"),
        (
            Subtopic("Types and planning of resources", ("resource planning",), ("potential", "developed", "stock", "reserve"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("Land resources and degradation", ("land degradation",), ("land use", "degradation", "conservation"), ("sa", "la"), "medium"),
            Subtopic("Soil resources", ("soil", "soil erosion"), ("alluvial", "black soil", "erosion"), ("mcq", "sa", "map_skill"), "medium"),
        )),
    Chapter(7, "Forest and Wildlife Resources", "geography",
        ("forest wildlife", "forest and wildlife", "biodiversity"),
        ("flora", "fauna", "conservation", "reserved forest", "protected forest", "community conservation"),
        (
            Subtopic("Biodiversity and conservation", ("biodiversity",), ("species", "extinct", "endangered"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("Types of forests", ("reserved protected unclassed forests",), ("reserved", "protected", "unclassed"), ("sa", "la"), "medium"),
            Subtopic("Community conservation", ("sacred groves",), ("joint forest management", "communities"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(8, "Water Resources", "geography",
        ("water resources", "dams", "rainwater harvesting"),
        ("scarcity", "multi purpose projects", "dams", "rainwater harvesting", "narmada", "tehri"),
        (
            Subtopic("Water scarcity", ("scarcity",), ("over exploitation", "pollution", "unequal access"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("Multi-purpose river projects", ("multi purpose projects", "dams"), ("flood control", "irrigation", "displacement"), ("sa", "la", "map_skill"), "medium"),
            Subtopic("Rainwater harvesting", ("rainwater",), ("tankas", "bamboo drip", "rooftop"), ("vsa", "case_study"), "simple"),
        )),
    Chapter(9, "Agriculture", "geography",
        ("agriculture", "crops", "farming"),
        ("subsistence", "commercial", "cropping seasons", "rice", "wheat", "sugarcane", "tea", "rubber"),
        (
            Subtopic("Types of farming", ("subsistence farming", "commercial farming"), ("primitive", "intensive", "plantation"), ("mcq", "sa"), "simple"),
            Subtopic("Cropping pattern", ("rabi kharif zaid",), ("rabi", "kharif", "zaid"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("Major crops and distribution", ("major crops",), ("rice", "wheat", "millets", "cotton", "jute"), ("sa", "la", "map_skill"), "medium"),
        )),
    Chapter(10, "Minerals and Energy Resources", "geography",
        ("minerals", "energy resources", "mineral resources"),
        ("iron ore", "manganese", "mica", "coal", "petroleum", "natural gas", "solar", "wind"),
        (
            Subtopic("Minerals and their distribution", ("mineral distribution",), ("ferrous", "non ferrous", "mica", "bauxite"), ("mcq", "sa", "map_skill"), "medium"),
            Subtopic("Conventional energy resources", ("coal petroleum",), ("coal", "petroleum", "natural gas", "electricity"), ("sa", "la", "map_skill"), "medium"),
            Subtopic("Non-conventional energy resources", ("solar wind nuclear",), ("solar", "wind", "tidal", "geothermal"), ("vsa", "sa"), "simple"),
        )),
    Chapter(11, "Manufacturing Industries", "geography",
        ("manufacturing", "industries", "industrial location"),
        ("agro based", "mineral based", "cotton textile", "iron steel", "pollution", "industrial location"),
        (
            Subtopic("Importance and location of industries", ("industrial location",), ("raw material", "labour", "market", "power"), ("mcq", "sa"), "medium"),
            Subtopic("Agro-based and mineral-based industries", ("textile industry", "iron and steel"), ("cotton", "sugar", "steel", "cement"), ("sa", "la", "map_skill"), "medium"),
            Subtopic("Industrial pollution", ("pollution",), ("air", "water", "thermal", "noise"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(12, "Lifelines of National Economy", "geography",
        ("lifelines", "transport communication trade", "national economy"),
        ("roads", "railways", "waterways", "airways", "ports", "communication", "trade", "tourism"),
        (
            Subtopic("Transport networks", ("roads railways waterways airways",), ("golden quadrilateral", "railways", "ports"), ("mcq", "sa", "map_skill"), "medium"),
            Subtopic("Communication and trade", ("communication trade",), ("telecommunication", "mass communication", "international trade"), ("vsa", "sa"), "simple"),
            Subtopic("Tourism as trade", ("tourism",), ("foreign exchange", "heritage", "employment"), ("vsa", "case_study"), "simple"),
        )),
    Chapter(13, "Power-sharing", "political",
        ("power sharing", "belgium sri lanka"),
        ("belgium", "sri lanka", "majoritarianism", "accommodation", "federal", "horizontal"),
        (
            Subtopic("Belgium and Sri Lanka", ("belgium sri lanka",), ("ethnic", "majoritarian", "accommodation"), ("mcq", "vsa", "case_study"), "medium"),
            Subtopic("Forms of power-sharing", ("forms of power sharing",), ("horizontal", "vertical", "pressure groups"), ("sa", "la"), "medium"),
        )),
    Chapter(14, "Federalism", "political",
        ("federalism", "federal system"),
        ("union list", "state list", "concurrent list", "decentralisation", "panchayati raj", "language policy"),
        (
            Subtopic("Features of federalism", ("federal features",), ("two levels", "jurisdiction", "constitution"), ("mcq", "sa"), "medium"),
            Subtopic("Federalism in India", ("indian federalism",), ("lists", "language policy", "coalition"), ("sa", "la"), "medium"),
            Subtopic("Decentralisation", ("local government", "panchayati raj"), ("panchayat", "municipality", "gram sabha"), ("vsa", "case_study"), "simple"),
        )),
    Chapter(15, "Democracy and Diversity", "political",
        ("democracy diversity", "social divisions"),
        ("social division", "social difference", "caste", "race", "politics of social divisions"),
        (
            Subtopic("Social differences and divisions", ("social differences",), ("overlapping", "cross cutting", "division"), ("mcq", "vsa", "sa"), "medium"),
            Subtopic("Politics of social divisions", ("social divisions in politics",), ("competition", "representation", "democracy"), ("sa", "case_study"), "medium"),
        )),
    Chapter(16, "Gender, Religion and Caste", "political",
        ("gender religion caste", "gender caste religion"),
        ("gender division", "communalism", "secular state", "caste inequalities", "caste politics"),
        (
            Subtopic("Gender and politics", ("gender division",), ("patriarchy", "representation", "women"), ("mcq", "sa"), "medium"),
            Subtopic("Religion and communalism", ("communalism",), ("secular", "majority", "minority"), ("sa", "la"), "medium"),
            Subtopic("Caste and politics", ("caste politics",), ("inequality", "vote bank", "representation"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(17, "Popular Struggles and Movements", "political",
        ("popular struggles", "movements", "pressure groups"),
        ("nepal", "bolivia", "pressure groups", "movements", "democracy"),
        (
            Subtopic("Movements in Nepal and Bolivia", ("nepal bolivia",), ("democracy", "water war", "protest"), ("mcq", "sa"), "medium"),
            Subtopic("Pressure groups and movements", ("pressure groups",), ("sectional", "public interest", "influence"), ("sa", "la"), "medium"),
        )),
    Chapter(18, "Political Parties", "political",
        ("political parties", "party system"),
        ("national party", "state party", "one party", "two party", "multi party", "defection", "affidavit"),
        (
            Subtopic("Functions and necessity of parties", ("functions of political parties",), ("contest elections", "policies", "opposition"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("Party systems and national parties", ("party systems", "national parties"), ("BJP", "INC", "BSP", "CPI", "state party"), ("sa", "la"), "medium"),
            Subtopic("Challenges and reforms", ("party reforms",), ("dynastic succession", "money power", "criminals"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(19, "Outcomes of Democracy", "political",
        ("outcomes democracy", "democratic outcomes"),
        ("accountable", "responsive", "legitimate", "economic growth", "inequality", "dignity"),
        (
            Subtopic("Accountable and legitimate government", ("accountable government",), ("transparency", "deliberation", "legitimacy"), ("mcq", "sa"), "medium"),
            Subtopic("Economic outcomes and inequality", ("economic outcomes",), ("growth", "poverty", "inequality"), ("sa", "la"), "medium"),
            Subtopic("Dignity and freedom", ("dignity",), ("women", "caste", "conflict"), ("vsa", "case_study"), "simple"),
        )),
    Chapter(20, "Challenges to Democracy", "political",
        ("challenges democracy", "democratic reforms"),
        ("foundational challenge", "challenge of expansion", "deepening democracy", "political reforms"),
        (
            Subtopic("Types of democratic challenges", ("foundational expansion deepening",), ("foundational", "expansion", "deepening"), ("mcq", "sa"), "medium"),
            Subtopic("Political reforms", ("democratic reforms",), ("law", "citizen", "right to information"), ("sa", "la", "case_study"), "medium"),
        )),
    Chapter(21, "Development", "economics",
        ("development", "income and goals"),
        ("per capita income", "national income", "human development", "sustainability", "public facilities"),
        (
            Subtopic("Different development goals", ("development goals",), ("income", "security", "freedom", "equality"), ("mcq", "vsa"), "simple"),
            Subtopic("Income and other criteria", ("per capita income",), ("average income", "literacy", "health"), ("sa", "la"), "medium"),
            Subtopic("Sustainable development", ("sustainability",), ("resources", "future generations"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(22, "Sectors of the Indian Economy", "economics",
        ("sectors", "indian economy", "primary secondary tertiary"),
        ("primary", "secondary", "tertiary", "organised", "unorganised", "public sector", "private sector"),
        (
            Subtopic("Primary, secondary and tertiary sectors", ("three sectors",), ("goods", "services", "GDP"), ("mcq", "sa"), "simple"),
            Subtopic("Organised and unorganised sectors", ("organised sector", "unorganised sector"), ("employment", "protection", "security"), ("sa", "la"), "medium"),
            Subtopic("Public and private sectors", ("public private sector",), ("welfare", "profit", "basic services"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(23, "Money and Credit", "economics",
        ("money credit", "credit", "banking"),
        ("double coincidence", "modern money", "deposits", "loans", "collateral", "self help groups"),
        (
            Subtopic("Money as a medium of exchange", ("medium of exchange",), ("barter", "double coincidence", "currency"), ("mcq", "vsa"), "simple"),
            Subtopic("Formal and informal credit", ("sources of credit",), ("banks", "moneylenders", "collateral", "interest"), ("sa", "la", "case_study"), "medium"),
            Subtopic("Self-help groups", ("shg", "self help group"), ("savings", "loans", "women"), ("vsa", "sa"), "simple"),
        )),
    Chapter(24, "Globalisation and the Indian Economy", "economics",
        ("globalisation", "indian economy", "multinational companies"),
        ("MNC", "foreign trade", "investment", "liberalisation", "WTO", "competition"),
        (
            Subtopic("Globalisation and MNCs", ("mncs",), ("production", "investment", "markets"), ("mcq", "sa"), "medium"),
            Subtopic("Foreign trade and integration", ("foreign trade",), ("trade barriers", "liberalisation", "WTO"), ("sa", "la"), "medium"),
            Subtopic("Impact of globalisation", ("impact",), ("consumers", "workers", "competition"), ("vsa", "case_study"), "medium"),
        )),
    Chapter(25, "Consumer Rights", "economics",
        ("consumer rights", "consumer awareness"),
        ("consumer movement", "COPRA", "right to information", "right to choose", "right to redressal", "standardisation"),
        (
            Subtopic("Consumer movement and exploitation", ("consumer movement",), ("adulteration", "false claims", "marketplace"), ("mcq", "vsa"), "simple"),
            Subtopic("Consumer rights and redressal", ("consumer redressal",), ("COPRA", "district forum", "compensation"), ("sa", "la"), "medium"),
            Subtopic("Standardisation and awareness", ("isi agmark hallmark",), ("ISI", "Agmark", "Hallmark"), ("vsa", "case_study"), "simple"),
        )),
)

CHAPTER_NAME_BY_STREAM_NUMBER = {
    (chapter.stream, chapter.number): chapter.name
    for chapter in CHAPTERS
}


def resolve(query: str) -> tuple[Chapter, Subtopic | None]:
    query_norm = _normalize(query)
    best_chapter: Chapter | None = None
    best_subtopic: Subtopic | None = None
    best_score = 0.0

    for ch in CHAPTERS:
        ch_terms = {_normalize(t) for t in (ch.name, ch.stream, *ch.aliases, *ch.focus_terms)}
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
            "stream": ch.stream,
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
    "vsa": "Very Short Answer - 2-mark social science response",
    "sa": "Short Answer - 3-mark explanation or comparison",
    "la": "Long Answer - 5-mark analytical or evaluative answer",
    "case_study": "Case Study - source-based unit with sub-questions",
    "map_skill": "Map Skill - 5-mark location, identification, or labelling task",
}

_TYPE_EXAMPLE = {
    "mcq": "Which one of the following is a feature of federalism?",
    "assertion_reason": "Assertion (A): Power-sharing reduces conflict. Reason (R): It gives all groups a stake in governance.",
    "vsa": "State two reasons why average income is used to compare countries.",
    "sa": "Explain any three features of the Non-Cooperation Movement.",
    "la": "Analyse the role of manufacturing industries in economic development.",
    "case_study": "Read the source on formal credit and answer the following questions.",
    "map_skill": "On the given outline map of India, locate and label major crop or industry centres.",
}


def hardness_marks_range(hardness: str) -> tuple[int, int]:
    return HARDNESS_MARKS.get(hardness, (2, 3))
