"use client";

import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Copy,
  Download,
  Eye,
  FileText,
  History,
  Lock,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Search,
  Settings,
  SlidersHorizontal,
  Trash2,
  Unlock,
  X
} from "lucide-react";
import katex from "katex";
import type { CSSProperties } from "react";
import { useEffect, useRef, useState } from "react";

type QuestionType = "mcq" | "assertion_reason" | "vsa" | "sa" | "la" | "case_study";
type Subject = "maths" | "science";
type Difficulty = "simple" | "medium" | "hard";
type PaperLevel = "standard" | "medium" | "challenging";
type PaperVariant = "basic" | "standard";
type PaperTemplateId = "custom" | "default" | "cbse_class10_standard" | "cbse_class10_science";
type QuestionStatus = "generated" | "edited" | "regenerated" | "locked" | "needs_review";
type WorkspaceSection = "builder" | "drafts" | "library" | "trash" | "exports";
type CoverageMode = "chapter" | "chapter_subtopics";
type DifficultyScope = "overall" | "granular";
type ChallengeOverride = "inherit" | PaperLevel;

type Chapter = {
  number: number;
  name: string;
  subtopics: string[];
  question_types: QuestionType[];
};

type Question = {
  id: string;
  question: string;
  answer: string;
  solution?: {
    steps?: string[];
    derivation?: string;
  };
  topic: string;
  subtopic?: string;
  marks: number;
  type: QuestionType;
  difficulty: Difficulty;
  options?: string[];
  metadata?: Record<string, unknown>;
  status?: QuestionStatus;
  locked?: boolean;
  history?: QuestionVersion[];
};

type QuestionVersion = {
  id: string;
  label: string;
  timestamp: string;
  question: Question;
};

type GenerateResponse = {
  questions: Question[];
  count: number;
  generated_at: string;
};

type CoverageSubtopicWeight = {
  name: string;
  weight: number;
};

type CoverageChapterWeight = {
  chapterName: string;
  weight: number;
  subtopics: CoverageSubtopicWeight[];
};

type CoveragePlan = {
  mode: CoverageMode;
  chapters: CoverageChapterWeight[];
};

type ChallengeSubtopicSetting = {
  name: string;
  challenge: ChallengeOverride;
};

type ChallengeChapterSetting = {
  chapterName: string;
  challenge: ChallengeOverride;
  subtopics: ChallengeSubtopicSetting[];
};

type ChallengePlan = {
  chapters: ChallengeChapterSetting[];
};

type PaperSettings = {
  subject: Subject;
  paperTitle: string;
  selectedChapters: string[];
  subtopics: string[];
  coveragePlan?: CoveragePlan;
  challengePlan?: ChallengePlan;
  difficultyScope?: DifficultyScope;
  paperTemplate?: PaperTemplateId;
  questionMix: Record<QuestionType, number>;
  paperLevel: PaperLevel;
  paperVariant: PaperVariant;
  usePyqPatterns: boolean;
  view: "paper" | "solutions";
};

type GenerationProgressJob = {
  id: string;
  label: string;
  detail: string;
  count: number;
  status: "queued" | "running" | "complete" | "failed";
  error?: string;
};

type GenerationProgress = {
  activeLabel: string;
  completedQuestions: number;
  totalQuestions: number;
  jobs: GenerationProgressJob[];
};

type DraftRecord = {
  id: string;
  generationId: string;
  title: string;
  updatedAt: string;
  settings: PaperSettings;
  questions: Question[];
};

type QuestionLibraryItem = Question & {
  libraryId: string;
  storedAt: string;
  generationLabel: string;
};

type TrashedQuestionRecord = {
  trashId: string;
  deletedAt: string;
  expiresAt: string;
  deletedFromTitle: string;
  generationId?: string;
  originalIndex: number;
  question: Question;
};

const DRAFT_STORAGE_KEY = "schengine.paperDrafts.v1";
const QUESTION_LIBRARY_STORAGE_KEY = "schengine.questionLibrary.v1";
const QUESTION_TRASH_STORAGE_KEY = "schengine.questionTrash.v1";
const INSPECTOR_WIDTH_STORAGE_KEY = "schengine.inspectorWidth.v1";
const TRASH_RETENTION_DAYS = 30;
const DEFAULT_INSPECTOR_WIDTH = 376;
const MIN_INSPECTOR_WIDTH = 320;
const MAX_INSPECTOR_WIDTH = 760;

const questionTypes: { type: QuestionType; label: string; section: string; marks: number }[] = [
  { type: "mcq", label: "MCQ", section: "A", marks: 1 },
  { type: "assertion_reason", label: "Assertion-Reason", section: "A", marks: 1 },
  { type: "vsa", label: "VSA", section: "B", marks: 2 },
  { type: "sa", label: "SA", section: "C", marks: 3 },
  { type: "la", label: "LA", section: "D", marks: 5 },
  { type: "case_study", label: "Case Study", section: "E", marks: 4 }
];

const defaultQuestionMix: Record<QuestionType, number> = {
  mcq: 1,
  assertion_reason: 0,
  vsa: 0,
  sa: 0,
  la: 0,
  case_study: 0
};

const cbseClass10StandardMix: Record<QuestionType, number> = {
  mcq: 18,
  assertion_reason: 2,
  vsa: 5,
  sa: 6,
  la: 4,
  case_study: 3
};

const cbseClass10ScienceMix: Record<QuestionType, number> = {
  mcq: 18,
  assertion_reason: 2,
  vsa: 6,
  sa: 7,
  la: 3,
  case_study: 3
};

const paperLevelOptions: { value: PaperLevel; label: string }[] = [
  { value: "standard", label: "Standard" },
  { value: "medium", label: "Medium" },
  { value: "challenging", label: "Challenging" }
];

const subjectOptions: { value: Subject; label: string }[] = [
  { value: "maths", label: "Maths" },
  { value: "science", label: "Science" }
];

const challengeOverrideOptions: { value: ChallengeOverride; label: string }[] = [
  { value: "inherit", label: "Inherit" },
  ...paperLevelOptions
];

const paperTemplates: {
  id: PaperTemplateId;
  subject?: Subject;
  label: string;
  description: string;
  questionMix: Record<QuestionType, number>;
  paperTitle?: string;
  paperLevel?: PaperLevel;
  paperVariant?: PaperVariant;
  selectAllChapters?: boolean;
}[] = [
  {
    id: "default",
    label: "Default",
    description: "Quick one-question draft",
    questionMix: defaultQuestionMix
  },
  {
    id: "cbse_class10_standard",
    subject: "maths",
    label: "CBSE Class 10 Standard",
    description: "38 questions / 80 marks / all chapters",
    questionMix: cbseClass10StandardMix,
    paperTitle: "CBSE Class 10 Mathematics Standard",
    paperLevel: "standard",
    paperVariant: "standard",
    selectAllChapters: true
  },
  {
    id: "cbse_class10_science",
    subject: "science",
    label: "CBSE Class 10 Science",
    description: "39 questions / 80 marks / all chapters",
    questionMix: cbseClass10ScienceMix,
    paperTitle: "CBSE Class 10 Science",
    paperLevel: "standard",
    selectAllChapters: true
  }
];

const fallbackChapters: Chapter[] = [
  {
    number: 1,
    name: "Real Numbers",
    subtopics: ["euclid division lemma", "fundamental theorem of arithmetic", "irrational numbers", "rational numbers and decimal expansions"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la"]
  },
  {
    number: 2,
    name: "Polynomials",
    subtopics: ["geometrical meaning of zeros", "relationship between zeros and coefficients", "division algorithm for polynomials"],
    question_types: ["mcq", "vsa", "sa", "la"]
  },
  {
    number: 3,
    name: "Pair of Linear Equations in Two Variables",
    subtopics: ["graphical method", "substitution method", "elimination method", "cross-multiplication method", "equations reducible to linear form"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la", "case_study"]
  },
  {
    number: 4,
    name: "Quadratic Equations",
    subtopics: ["standard form and roots", "factorisation method", "quadratic formula", "nature of roots"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la", "case_study"]
  },
  {
    number: 5,
    name: "Arithmetic Progressions",
    subtopics: ["general term of an AP", "sum of n terms of an AP", "arithmetic mean"],
    question_types: ["mcq", "vsa", "sa", "la"]
  },
  {
    number: 6,
    name: "Triangles",
    subtopics: ["similarity of triangles", "basic proportionality theorem", "criteria for similarity", "pythagoras theorem"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la", "case_study"]
  },
  {
    number: 7,
    name: "Coordinate Geometry",
    subtopics: ["distance formula", "section formula", "area of triangle"],
    question_types: ["mcq", "vsa", "sa", "la", "case_study"]
  },
  {
    number: 8,
    name: "Introduction to Trigonometry",
    subtopics: ["trigonometric ratios", "trigonometric identities", "complementary angles"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la"]
  },
  {
    number: 9,
    name: "Some Applications of Trigonometry",
    subtopics: ["angle of elevation", "angle of depression"],
    question_types: ["sa", "la", "case_study"]
  },
  {
    number: 10,
    name: "Circles",
    subtopics: ["tangent to a circle", "number of tangents from a point"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la"]
  },
  {
    number: 11,
    name: "Constructions",
    subtopics: ["division of line segment", "construction of tangents", "construction of similar triangles"],
    question_types: ["vsa", "sa", "la"]
  },
  {
    number: 12,
    name: "Areas Related to Circles",
    subtopics: ["area of sector", "area of segment", "areas of combinations of figures"],
    question_types: ["mcq", "vsa", "sa", "la", "case_study"]
  },
  {
    number: 13,
    name: "Surface Areas and Volumes",
    subtopics: ["surface area of solids", "volume of solids", "conversion of solids", "frustum of cone", "combination of solids"],
    question_types: ["mcq", "vsa", "sa", "la", "case_study"]
  },
  {
    number: 14,
    name: "Statistics",
    subtopics: ["mean of grouped data", "mode of grouped data", "median of grouped data", "ogive"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la", "case_study"]
  },
  {
    number: 15,
    name: "Probability",
    subtopics: ["probability basics", "complementary events", "applications of probability"],
    question_types: ["mcq", "assertion_reason", "vsa", "sa", "la", "case_study"]
  }
];

const initialQuestions: Question[] = [
  {
    id: "draft-1",
    question: "The discriminant of the quadratic equation $3x^2 - 4x + 1 = 0$ is",
    answer: "(C)",
    solution: {
      steps: [
        "Identify $a = 3$, $b = -4$, and $c = 1$.",
        "Use $D = b^2 - 4ac$.",
        "So $D = (-4)^2 - 4(3)(1) = 4$."
      ],
      derivation: "$D = b^2 - 4ac \\\\ D = 16 - 12 = 4$"
    },
    topic: "Quadratic Equations",
    subtopic: "Nature of Roots",
    marks: 1,
    type: "mcq",
    difficulty: "simple",
    options: ["(A) 1", "(B) 2", "(C) 4", "(D) 16"],
    status: "generated",
    locked: false,
    metadata: {
      model: "sample",
      retrieved_sources: ["Chapter_4 (Quadratic Equations).pdf"]
    },
    history: []
  }
];

export default function PaperBuilderPage() {
  const [subject, setSubject] = useState<Subject>("maths");
  const [chapters, setChapters] = useState<Chapter[]>(fallbackChapters);
  const [paperTitle, setPaperTitle] = useState("CBSE Class 10 Mathematics");
  const [selectedChapters, setSelectedChapters] = useState<string[]>(["Quadratic Equations"]);
  const [selectedSubtopics, setSelectedSubtopics] = useState<string[]>([]);
  const [coveragePlan, setCoveragePlan] = useState<CoveragePlan>(() =>
    createCoveragePlan(
      fallbackChapters.filter((chapter) => ["Quadratic Equations"].includes(chapter.name)),
      "chapter_subtopics"
    )
  );
  const [paperTemplate, setPaperTemplate] = useState<PaperTemplateId>("default");
  const [questionMix, setQuestionMix] = useState<Record<QuestionType, number>>(defaultQuestionMix);
  const [paperLevel, setPaperLevel] = useState<PaperLevel>("standard");
  const [difficultyScope, setDifficultyScope] = useState<DifficultyScope>("overall");
  const [challengePlan, setChallengePlan] = useState<ChallengePlan>(() =>
    createChallengePlan(
      fallbackChapters.filter((chapter) => ["Quadratic Equations"].includes(chapter.name))
    )
  );
  const [paperVariant, setPaperVariant] = useState<PaperVariant>("standard");
  const [usePyqPatterns, setUsePyqPatterns] = useState(true);
  const [questions, setQuestions] = useState<Question[]>(initialQuestions);
  const [selectedId, setSelectedId] = useState(initialQuestions[0].id);
  const [view, setView] = useState<"paper" | "solutions">("paper");
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState<"question-paper" | "answer-key" | null>(null);
  const [chapterMenuOpen, setChapterMenuOpen] = useState(false);
  const [coverageEditorOpen, setCoverageEditorOpen] = useState(false);
  const [coverageDraft, setCoverageDraft] = useState<CoveragePlan | null>(null);
  const [challengeDraft, setChallengeDraft] = useState<ChallengePlan | null>(null);
  const [expandedCoverageChapter, setExpandedCoverageChapter] = useState<string | null>("Quadratic Equations");
  const [activeDropdown, setActiveDropdown] = useState<"chapters" | null>(null);
  const [workspaceSection, setWorkspaceSection] = useState<WorkspaceSection>("builder");
  const [drafts, setDrafts] = useState<DraftRecord[]>([]);
  const [questionLibrary, setQuestionLibrary] = useState<QuestionLibraryItem[]>([]);
  const [questionTrash, setQuestionTrash] = useState<TrashedQuestionRecord[]>([]);
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress | null>(null);
  const [notice, setNotice] = useState("Draft saved locally");
  const [currentGenerationId, setCurrentGenerationId] = useState("");
  const [inspectorWidth, setInspectorWidth] = useState(DEFAULT_INSPECTOR_WIDTH);
  const chapterDropdownRef = useRef<HTMLDivElement | null>(null);
  const inspectorResizeRef = useRef<{ startX: number; startWidth: number } | null>(null);
  const [regeneration, setRegeneration] = useState<{
    source: Question;
    candidate?: Question;
    mode: "refine" | "replace";
    instruction: string;
    loading: boolean;
  } | null>(null);

  const selectedQuestion = questions.find((q) => q.id === selectedId) ?? questions[0];
  const selectedChapterRows = selectedChapters
    .map((name) => chapters.find((chapter) => chapter.name === name))
    .filter((chapter): chapter is Chapter => Boolean(chapter));
  const totalRequestedQuestions = questionTypes.reduce((sum, item) => sum + (questionMix[item.type] ?? 0), 0);
  const normalizedCoveragePlan = normalizeCoveragePlan(selectedChapterRows, coveragePlan);
  const normalizedChallengePlan = normalizeChallengePlan(selectedChapterRows, challengePlan);
  const coverageSummary = summarizeCoveragePlan(selectedChapterRows, normalizedCoveragePlan);
  const difficultySummary = summarizeChallengePlan(difficultyScope, paperLevel, normalizedChallengePlan);
  const coveragePreviewPlan = coverageDraft ? normalizeCoveragePlan(selectedChapterRows, coverageDraft) : null;
  const challengePreviewPlan = challengeDraft ? normalizeChallengePlan(selectedChapterRows, challengeDraft) : null;
  const coveragePreviewEstimate = coveragePreviewPlan
    ? estimateCoverage(questionMix, selectedChapterRows, coveragePreviewPlan)
    : null;
  const totalMarks = questions.reduce((sum, q) => sum + Number(q.marks || 0), 0);
  const validationIssues = questions.filter((q) => !q.question || !q.answer || (q.type === "mcq" && (q.options?.length ?? 0) !== 4));
  const availableTemplates = paperTemplates.filter((template) => !template.subject || template.subject === subject);
  const builderGridStyle = {
    "--inspector-width": `${inspectorWidth}px`
  } as CSSProperties & Record<"--inspector-width", string>;

  useEffect(() => {
    fetch(`/api/v1/chapters?subject=${subject}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data: { chapters?: Chapter[] } | null) => {
        if (data?.chapters?.length) {
          setChapters(data.chapters);
          const defaultChapter = data.chapters[0];
          setSelectedChapters(defaultChapter ? [defaultChapter.name] : []);
          setSelectedSubtopics([]);
          setCoveragePlan(createCoveragePlan(defaultChapter ? [defaultChapter] : [], "chapter_subtopics"));
          setChallengePlan(createChallengePlan(defaultChapter ? [defaultChapter] : []));
          setExpandedCoverageChapter(defaultChapter?.name ?? null);
          setPaperTitle(subject === "science" ? "CBSE Class 10 Science" : "CBSE Class 10 Mathematics");
          setPaperTemplate("default");
          setQuestionMix(defaultQuestionMix);
        }
      })
      .catch(() => undefined);
  }, [subject]);

  useEffect(() => {
    setDrafts(loadStoredList<DraftRecord>(DRAFT_STORAGE_KEY));
    setQuestionLibrary(loadStoredList<QuestionLibraryItem>(QUESTION_LIBRARY_STORAGE_KEY));
    setQuestionTrash(pruneExpiredTrash(loadStoredList<TrashedQuestionRecord>(QUESTION_TRASH_STORAGE_KEY)));
    const storedInspectorWidth = Number(window.localStorage.getItem(INSPECTOR_WIDTH_STORAGE_KEY));
    if (Number.isFinite(storedInspectorWidth)) {
      setInspectorWidth(clampInspectorWidth(storedInspectorWidth, window.innerWidth));
    }
  }, []);

  useEffect(() => {
    saveStoredList(QUESTION_TRASH_STORAGE_KEY, pruneExpiredTrash(questionTrash));
  }, [questionTrash]);

  useEffect(() => {
    window.localStorage.setItem(INSPECTOR_WIDTH_STORAGE_KEY, String(inspectorWidth));
  }, [inspectorWidth]);

  useEffect(() => {
    if (!chapterMenuOpen) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (target instanceof Node) {
        if (chapterDropdownRef.current?.contains(target)) {
          return;
        }
      }
      setChapterMenuOpen(false);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [chapterMenuOpen]);

  useEffect(() => {
    setCoveragePlan((current) => {
      const next = normalizeCoveragePlan(selectedChapterRows, current);
      return areCoveragePlansEqual(current, next) ? current : next;
    });
    setChallengePlan((current) => {
      const next = normalizeChallengePlan(selectedChapterRows, current);
      return areChallengePlansEqual(current, next) ? current : next;
    });
    setExpandedCoverageChapter((current) => {
      if (current && selectedChapterRows.some((chapter) => chapter.name === current)) {
        return current;
      }
      return selectedChapterRows[0]?.name ?? null;
    });
  }, [
    chapters.map((chapter) => `${chapter.number}:${chapter.name}`).join("||"),
    selectedChapters.join("||")
  ]);

  function currentSettings(): PaperSettings {
    return {
      subject,
      paperTitle,
      selectedChapters,
      subtopics: [...selectedSubtopics],
      coveragePlan,
      challengePlan,
      difficultyScope,
      paperTemplate,
      questionMix: { ...questionMix },
      paperLevel,
      paperVariant,
      usePyqPatterns,
      view
    };
  }

  function applySettings(settings: PaperSettings & { subtopic?: string }) {
    setSubject(settings.subject ?? "maths");
    const nextSelectedChapters = settings.selectedChapters ?? [];
    const nextSelectedRows = nextSelectedChapters
      .map((name) => chapters.find((chapter) => chapter.name === name))
      .filter((chapter): chapter is Chapter => Boolean(chapter));
    setPaperTitle(settings.paperTitle || (settings.subject === "science" ? "CBSE Class 10 Science" : "CBSE Class 10 Mathematics"));
    setSelectedChapters(nextSelectedChapters);
    // Backward compat: old drafts had single "subtopic" string
    if (settings.subtopics) {
      setSelectedSubtopics(settings.subtopics);
    } else if (settings.subtopic) {
      setSelectedSubtopics(settings.subtopic ? [settings.subtopic] : []);
    } else {
      setSelectedSubtopics([]);
    }
    setCoveragePlan(
      settings.coveragePlan
        ? normalizeCoveragePlan(nextSelectedRows, settings.coveragePlan)
        : createCoveragePlan(nextSelectedRows)
    );
    setChallengePlan(
      settings.challengePlan
        ? normalizeChallengePlan(nextSelectedRows, settings.challengePlan)
        : createChallengePlan(nextSelectedRows)
    );
    setDifficultyScope(settings.difficultyScope ?? "overall");
    setPaperTemplate(settings.paperTemplate ?? "custom");
    setQuestionMix({ ...defaultQuestionMix, ...(settings.questionMix ?? {}) });
    setPaperLevel(settings.paperLevel ?? "standard");
    setPaperVariant(settings.paperVariant ?? "standard");
    setUsePyqPatterns(settings.usePyqPatterns ?? true);
    setView(settings.view ?? "paper");
  }

  function startInspectorResize(event: React.PointerEvent<HTMLButtonElement>) {
    inspectorResizeRef.current = {
      startX: event.clientX,
      startWidth: inspectorWidth
    };
    event.currentTarget.setPointerCapture(event.pointerId);
    document.body.classList.add("resizing-inspector");
  }

  function resizeInspector(event: React.PointerEvent<HTMLButtonElement>) {
    const current = inspectorResizeRef.current;
    if (!current) return;
    const delta = current.startX - event.clientX;
    setInspectorWidth(clampInspectorWidth(current.startWidth + delta, window.innerWidth));
  }

  function stopInspectorResize(event: React.PointerEvent<HTMLButtonElement>) {
    if (!inspectorResizeRef.current) return;
    inspectorResizeRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    document.body.classList.remove("resizing-inspector");
  }

  function saveCurrentDraft() {
    const now = new Date().toISOString();
    const normalizedQuestions = questions.map(normalizeQuestionRecord);
    const genId = currentGenerationId || generateGenerationId();
    setCurrentGenerationId(genId);
    const draft: DraftRecord = {
      id: crypto.randomUUID(),
      generationId: genId,
      title: paperTitle.trim() || "Untitled Paper",
      updatedAt: now,
      settings: currentSettings(),
      questions: normalizedQuestions
    };
    setDrafts((current) => {
      const next = [draft, ...current].slice(0, 50);
      saveStoredList(DRAFT_STORAGE_KEY, next);
      return next;
    });
    setNotice(`Draft saved (${genId})`);
    setWorkspaceSection("drafts");
  }

  function openCoverageEditor() {
    if (!selectedChapterRows.length) {
      setNotice("Select at least one chapter");
      return;
    }
    setCoverageDraft(cloneCoveragePlan(normalizedCoveragePlan));
    setChallengeDraft(cloneChallengePlan(normalizedChallengePlan));
    setExpandedCoverageChapter((current) => {
      if (current && selectedChapterRows.some((chapter) => chapter.name === current)) {
        return current;
      }
      return selectedChapterRows[0]?.name ?? null;
    });
    setCoverageEditorOpen(true);
  }

  function closeCoverageEditor() {
    setCoverageEditorOpen(false);
    setCoverageDraft(null);
    setChallengeDraft(null);
  }

  function updateCoverageDraftMode(mode: CoverageMode) {
    setCoverageDraft((current) => current ? { ...current, mode } : current);
  }

  function updateCoverageDraftChapterWeight(chapterName: string, weight: number) {
    setCoverageDraft((current) => current ? {
      ...current,
      chapters: current.chapters.map((chapter) =>
        chapter.chapterName === chapterName
          ? { ...chapter, weight: clampWeight(weight) }
          : chapter
      )
    } : current);
  }

  function updateCoverageDraftSubtopicWeight(chapterName: string, subtopicName: string, weight: number) {
    setCoverageDraft((current) => current ? {
      ...current,
      chapters: current.chapters.map((chapter) =>
        chapter.chapterName === chapterName
          ? {
              ...chapter,
              subtopics: chapter.subtopics.map((subtopic) =>
                subtopic.name === subtopicName
                  ? { ...subtopic, weight: clampWeight(weight) }
                  : subtopic
              )
            }
          : chapter
      )
    } : current);
  }

  function updateChallengeDraftChapter(chapterName: string, challenge: ChallengeOverride) {
    setChallengeDraft((current) => current ? {
      ...current,
      chapters: current.chapters.map((chapter) =>
        chapter.chapterName === chapterName
          ? { ...chapter, challenge }
          : chapter
      )
    } : current);
  }

  function updateChallengeDraftSubtopic(chapterName: string, subtopicName: string, challenge: ChallengeOverride) {
    setChallengeDraft((current) => current ? {
      ...current,
      chapters: current.chapters.map((chapter) =>
        chapter.chapterName === chapterName
          ? {
              ...chapter,
              subtopics: chapter.subtopics.map((subtopic) =>
                subtopic.name === subtopicName
                  ? { ...subtopic, challenge }
                  : subtopic
              )
            }
          : chapter
      )
    } : current);
  }

  function applyEqualCoverageSplit() {
    setCoverageDraft((current) => current ? createCoveragePlan(selectedChapterRows, current.mode) : current);
  }

  function resetCoverageSubtopics() {
    setCoverageDraft((current) => current ? {
      ...current,
      chapters: current.chapters.map((chapter) => {
        const chapterRow = selectedChapterRows.find((row) => row.name === chapter.chapterName);
        const weights = createPercentageWeights(chapterRow?.subtopics.length ?? 0);
        return {
          ...chapter,
          subtopics: (chapterRow?.subtopics ?? []).map((subtopic, index) => ({
            name: subtopic,
            weight: weights[index] ?? 0
          }))
        };
      })
    } : current);
  }

  function applyCoverageEditor() {
    if (!coverageDraft) return;
    if (!isCoveragePlanValid(coverageDraft, selectedChapterRows)) {
      setNotice("Chapter and subtopic totals must equal 100%");
      return;
    }
    setCoveragePlan(normalizeCoveragePlan(selectedChapterRows, coverageDraft));
    if (challengeDraft) {
      setChallengePlan(normalizeChallengePlan(selectedChapterRows, challengeDraft));
    }
    setPaperTemplate("custom");
    setCoverageEditorOpen(false);
    setCoverageDraft(null);
    setChallengeDraft(null);
    setNotice("Chapter settings updated");
  }

  function openDraft(draft: DraftRecord) {
    applySettings(draft.settings);
    const normalizedQuestions = draft.questions.map(normalizeQuestionRecord);
    setQuestions(normalizedQuestions);
    setSelectedId(normalizedQuestions[0]?.id ?? "");
    setCurrentGenerationId(draft.generationId || "");
    setWorkspaceSection("builder");
    setNotice(`Loaded draft ${draft.generationId || ""} saved ${formatDateTime(draft.updatedAt)}`);
  }

  function deleteDraft(draft: DraftRecord) {
    setDrafts((current) => {
      const next = current.filter((item) => item.id !== draft.id);
      saveStoredList(DRAFT_STORAGE_KEY, next);
      return next;
    });
    setNotice("Draft deleted");
  }

  function addQuestionsToLibrary(rows: Question[], generationLabel: string) {
    if (!rows.length) return;
    const storedAt = new Date().toISOString();
    const records = rows.map((question): QuestionLibraryItem => ({
      ...normalizeQuestionRecord(question),
      libraryId: crypto.randomUUID(),
      storedAt,
      generationLabel
    }));
    setQuestionLibrary((current) => {
      const next = [...records, ...current].slice(0, 500);
      saveStoredList(QUESTION_LIBRARY_STORAGE_KEY, next);
      return next;
    });
  }

  function insertFromLibrary(item: QuestionLibraryItem) {
    const { libraryId: _libraryId, storedAt: _storedAt, generationLabel: _generationLabel, ...question } = item;
    const clone: Question = {
      ...question,
      id: crypto.randomUUID(),
      status: "edited",
      locked: false,
      history: appendVersion(question, "Inserted from library")
    };
    setQuestions((rows) => [...rows, clone]);
    setSelectedId(clone.id);
    setWorkspaceSection("builder");
    setNotice("Question inserted from library");
  }

  function clearSelections() {
    setSelectedChapters([]);
    setSelectedSubtopics([]);
    setQuestionMix(emptyQuestionMix());
    setChapterMenuOpen(false);
    setCoverageEditorOpen(false);
    setCoverageDraft(null);
    setChallengeDraft(null);
    setChallengePlan(createChallengePlan([]));
    setDifficultyScope("overall");
    setPaperTemplate("custom");
    setNotice("Selections cleared");
  }

  function applyPaperTemplate(templateId: PaperTemplateId) {
    setPaperTemplate(templateId);
    if (templateId === "custom") {
      return;
    }
    const template = paperTemplates.find((item) => item.id === templateId);
    if (!template) {
      return;
    }
    setQuestionMix({ ...template.questionMix });
    if (template.paperTitle) {
      setPaperTitle(template.paperTitle);
    }
    if (template.paperLevel) {
      setPaperLevel(template.paperLevel);
      setDifficultyScope("overall");
    }
    if (template.paperVariant) {
      setPaperVariant(template.paperVariant);
    }
    if (template.selectAllChapters) {
      setSelectedChapters(chapters.map((chapter) => chapter.name));
      setSelectedSubtopics([]);
    }
    setNotice(`${template.label} template applied`);
  }

  function updateQuestionMix(type: QuestionType, value: number) {
    setQuestionMix((current) => ({ ...current, [type]: value }));
    setPaperTemplate("custom");
  }

  async function generateDraft() {
    const selectedTypes = questionTypes
      .map((item) => ({ ...item, count: questionMix[item.type] ?? 0 }))
      .filter((item) => item.count > 0);
    if (!selectedTypes.length) {
      setNotice("Select at least one question type");
      return;
    }
    if (!selectedChapterRows.length) {
      setNotice("Select at least one chapter");
      return;
    }

    const allocationWarnings: string[] = [];
    const jobs = selectedTypes.flatMap((item) => {
      const nextJobs = buildGenerationJobs({
        count: item.count,
        item,
        chapters: selectedChapterRows,
        coveragePlan: normalizedCoveragePlan
      });
      if (!nextJobs.length) {
        allocationWarnings.push(`${item.label}: no selected chapters support this type`);
      }
      return nextJobs;
    });
    const totalQuestionCount = jobs.reduce((sum, job) => sum + job.allocation.count, 0);
    if (!totalQuestionCount) {
      setNotice(allocationWarnings[0] ?? "No eligible chapter allocation found");
      return;
    }

    const genId = generateGenerationId();
    setCurrentGenerationId(genId);
    setLoading(true);
    setQuestions([]);
    setSelectedId("");
    setView("paper");
    setWorkspaceSection("builder");
    setGenerationProgress({
      activeLabel: "Preparing generation plan",
      completedQuestions: 0,
      totalQuestions: totalQuestionCount,
      jobs: jobs.map((job) => ({
        id: job.id,
        label: job.subtopic
          ? `${job.item.label} / ${job.allocation.chapter.name} / ${formatTitleCase(job.subtopic)}`
          : `${job.item.label} / ${job.allocation.chapter.name}`,
        detail: `${job.allocation.count} question${job.allocation.count === 1 ? "" : "s"}`,
        count: job.allocation.count,
        status: "queued"
      }))
    });
    setNotice(allocationWarnings.length ? `${allocationWarnings[0]}. Generating remaining supported types.` : "Generating draft");
    try {
      const generated: Question[] = [];
      for (const job of jobs) {
        const item = job.item;
        const allocation = job.allocation;
        const chapterTopic = job.subtopic
          ? `${allocation.chapter.name} ${job.subtopic}`
          : allocation.chapter.name;
        const jobPaperLevel = resolveJobPaperLevel({
          scope: difficultyScope,
          overall: paperLevel,
          plan: normalizedChallengePlan,
          chapterName: allocation.chapter.name,
          subtopicName: job.subtopic
        });
        const activeLabel = `Generating ${item.label} from ${allocation.chapter.name}`;
        setNotice(activeLabel);
        setGenerationProgress((current) => current ? {
          ...current,
          activeLabel,
          jobs: current.jobs.map((progressJob) =>
            progressJob.id === job.id ? { ...progressJob, status: "running" } : progressJob
          )
        } : current);
        const payload = {
          subject,
          topic: chapterTopic,
          question_type: item.type,
          count: allocation.count,
          paper_level: jobPaperLevel,
          paper_variant: paperVariant,
          use_pyq_patterns: usePyqPatterns
        };
        const response = await fetch("/api/v1/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!response.ok) {
          const errorText = await response.text();
          setGenerationProgress((current) => current ? {
            ...current,
            activeLabel: "Generation failed",
            jobs: current.jobs.map((progressJob) =>
              progressJob.id === job.id ? { ...progressJob, status: "failed", error: errorText } : progressJob
            )
          } : current);
          throw new Error(errorText);
        }
        const data = (await response.json()) as GenerateResponse;
        const normalized = data.questions.map((question) =>
          withClientState("generated")({
            ...question,
            subtopic: job.subtopic ? question.subtopic ?? job.subtopic : question.subtopic
          })
        );
        generated.push(...normalized);
        setGenerationProgress((current) => current ? {
          ...current,
          completedQuestions: Math.min(current.totalQuestions, current.completedQuestions + normalized.length),
          activeLabel: `${item.label} from ${allocation.chapter.name} complete`,
          jobs: current.jobs.map((progressJob) =>
            progressJob.id === job.id ? { ...progressJob, status: "complete" } : progressJob
          )
        } : current);
      }
      setQuestions(generated);
      setSelectedId(generated[0]?.id ?? "");
      addQuestionsToLibrary(generated, `Paper generation (${genId})`);
      setWorkspaceSection("builder");
      setGenerationProgress(null);
      setNotice(
        allocationWarnings.length
          ? `Generated ${generated.length} question${generated.length === 1 ? "" : "s"} [${genId}] with some unsupported chapter/type combinations skipped`
          : `Generated ${generated.length} question${generated.length === 1 ? "" : "s"} [${genId}]`
      );
    } catch (error) {
      setGenerationProgress((current) => current ? { ...current, activeLabel: "Generation failed" } : current);
      setNotice(error instanceof Error ? error.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function exportPdf(kind: "question-paper" | "answer-key", action: "download" | "preview" = "download") {
    if (!questions.length) return;
    const previewWindow = action === "preview" ? window.open("", "_blank") : null;
    if (previewWindow) {
      previewWindow.opener = null;
      previewWindow.document.write("<title>Preparing PDF preview</title><body style=\"font-family: sans-serif; padding: 24px;\">Preparing PDF preview...</body>");
      previewWindow.document.close();
    }
    const genId = currentGenerationId || generateGenerationId();
    setExporting(kind);
    setNotice(action === "preview" ? "Preparing PDF preview" : kind === "question-paper" ? "Exporting question paper" : "Exporting answer key");
    try {
      const response = await fetch(`/api/v1/export/${kind}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          questions: questions.map(normalizeQuestionRecord),
          title: paperTitle,
          subject,
          time_allowed: "3 Hours",
          max_marks: String(totalMarks || 80),
          generation_id: genId
        })
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const pdfFilename = `${genId}_${kind.replace("-", "_")}.pdf`;
      if (action === "preview") {
        if (previewWindow) {
          previewWindow.location.href = url;
          setNotice("PDF preview opened");
        } else {
          const link = document.createElement("a");
          link.href = url;
          link.download = pdfFilename;
          link.click();
          setNotice("Popup blocked, PDF downloaded instead");
        }
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      } else {
        const link = document.createElement("a");
        link.href = url;
        link.download = pdfFilename;
        link.click();
        URL.revokeObjectURL(url);
        setNotice(`${kind === "question-paper" ? "Question paper" : "Answer key"} exported (${genId})`);
      }
    } catch (error) {
      previewWindow?.close();
      setNotice(error instanceof Error ? error.message : "PDF export failed");
    } finally {
      setExporting(null);
    }
  }

  function updateSelected(patch: Partial<Question>) {
    if (!selectedId) return;
    setQuestions((rows) =>
      rows.map((row) =>
        row.id === selectedId && !row.locked
          ? {
              ...row,
              ...patch,
              status: "edited"
            }
          : row
      )
    );
    setNotice("Edited locally");
  }

  function toggleLock(question: Question) {
    setQuestions((rows) =>
      rows.map((row) =>
        row.id === question.id
          ? {
              ...row,
              locked: !row.locked,
              status: row.locked ? "edited" : "locked"
            }
          : row
      )
    );
  }

  function deleteQuestion(question: Question) {
    const deletedAt = new Date().toISOString();
    const originalIndex = questions.findIndex((row) => row.id === question.id);
    const trashedRecord: TrashedQuestionRecord = {
      trashId: crypto.randomUUID(),
      deletedAt,
      expiresAt: addDays(deletedAt, TRASH_RETENTION_DAYS),
      deletedFromTitle: paperTitle.trim() || "Untitled Paper",
      generationId: currentGenerationId || undefined,
      originalIndex: Math.max(0, originalIndex),
      question: normalizeQuestionRecord(question)
    };

    setQuestions((rows) => {
      const next = rows.filter((row) => row.id !== question.id);
      if (selectedId === question.id) {
        setSelectedId(next[0]?.id ?? "");
      }
      return next;
    });
    setQuestionTrash((rows) => [trashedRecord, ...pruneExpiredTrash(rows)]);
    setNotice(`Moved "${labelFor(question.type)}" question to trash`);
  }

  function duplicateQuestion(question: Question) {
    const clone = {
      ...question,
      id: crypto.randomUUID(),
      status: "edited" as QuestionStatus,
      locked: false,
      history: appendVersion(question, "Duplicated from")
    };
    setQuestions((rows) => [...rows, clone]);
    setSelectedId(clone.id);
  }

  function restoreTrashedQuestion(item: TrashedQuestionRecord) {
    let restoredId = item.question.id;
    setQuestions((rows) => {
      const nextQuestion = withClientState(item.question.status ?? "edited")({
        ...item.question,
        id: rows.some((row) => row.id === item.question.id) ? crypto.randomUUID() : item.question.id,
        history: item.question.history ?? []
      });
      restoredId = nextQuestion.id;
      const next = [...rows];
      const insertAt = Math.min(Math.max(0, item.originalIndex), next.length);
      next.splice(insertAt, 0, nextQuestion);
      return next;
    });
    setSelectedId(restoredId);
    setWorkspaceSection("builder");
    setQuestionTrash((rows) => rows.filter((row) => row.trashId !== item.trashId));
    setNotice("Question restored from trash");
  }

  function permanentlyDeleteTrashedQuestion(item: TrashedQuestionRecord) {
    setQuestionTrash((rows) => rows.filter((row) => row.trashId !== item.trashId));
    setNotice("Question permanently deleted");
  }

  function emptyTrash() {
    setQuestionTrash([]);
    setNotice("Trash emptied");
  }

  async function regenerateCandidate() {
    if (!regeneration) return;
    setRegeneration({ ...regeneration, loading: true });
    try {
      const source = regeneration.source;
      const promptTopic =
        regeneration.mode === "refine"
          ? `${source.topic} ${source.subtopic ?? ""} ${regeneration.instruction}`.trim()
          : `${source.topic} ${regeneration.instruction || "different setup"}`.trim();
      const response = await fetch("/api/v1/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject,
          topic: promptTopic,
          question_type: source.type,
          count: 1,
          difficulty: source.difficulty,
          paper_level: paperLevel,
          paper_variant: paperVariant,
          use_pyq_patterns: usePyqPatterns
        })
      });
      if (!response.ok) throw new Error(await response.text());
      const data = (await response.json()) as GenerateResponse;
      const candidate = withClientState("regenerated")(data.questions[0]);
      addQuestionsToLibrary([candidate], regeneration.mode === "refine" ? "Question regeneration" : "Different question regeneration");
      setRegeneration({ ...regeneration, candidate, loading: false });
    } catch {
      setRegeneration({ ...regeneration, loading: false });
      setNotice("Regeneration failed");
    }
  }

  function acceptCandidate(keepBoth = false) {
    if (!regeneration?.candidate) return;
    const source = regeneration.source;
    const candidate = {
      ...regeneration.candidate,
      id: keepBoth ? regeneration.candidate.id : source.id,
      history: appendVersion(source, "Regenerated from")
    };
    setQuestions((rows) =>
      keepBoth ? [...rows, candidate] : rows.map((row) => (row.id === source.id ? candidate : row))
    );
    setSelectedId(candidate.id);
    setRegeneration(null);
    setNotice(keepBoth ? "Candidate added" : "Question replaced");
  }

  return (
    <main className="app-shell">
      <aside className="nav-rail">
        <div className="brand-mark">SE</div>
        <IconButton active={workspaceSection === "builder"} title="Paper Builder" onClick={() => setWorkspaceSection("builder")}>
          <ClipboardList size={19} />
        </IconButton>
        <IconButton active={workspaceSection === "drafts"} title="Drafts" onClick={() => setWorkspaceSection("drafts")}>
          <FileText size={19} />
        </IconButton>
        <IconButton active={workspaceSection === "library"} title="Question Library" onClick={() => setWorkspaceSection("library")}>
          <BookOpen size={19} />
        </IconButton>
        <IconButton active={workspaceSection === "trash"} title="Trash" onClick={() => setWorkspaceSection("trash")}>
          <Trash2 size={19} />
        </IconButton>
        <div className="nav-spacer" />
        <IconButton title="Settings">
          <Settings size={19} />
        </IconButton>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <input className="title-input" value={paperTitle} onChange={(event) => setPaperTitle(event.target.value)} />
            <div className="muted-line notice-line" key={notice}>{notice}</div>
          </div>
          <div className="top-actions">
            <div className="search-box">
              <Search size={16} />
              <input placeholder="Search questions" />
            </div>
            <button className="secondary-button" onClick={saveCurrentDraft}>
              <Save size={16} />
              Save Draft
            </button>
            <Segmented
              value={view}
              options={[
                { value: "paper", label: "Question Paper" },
                { value: "solutions", label: "Solutions" }
              ]}
              onChange={(value) => setView(value as "paper" | "solutions")}
            />
            <button className="secondary-button" onClick={() => exportPdf("question-paper", "preview")} disabled={!!exporting || !questions.length}>
              <Eye size={16} />
              PDF Preview
            </button>
            <button className="secondary-button" onClick={() => exportPdf("question-paper")} disabled={!!exporting || !questions.length}>
              <Download size={16} className={exporting === "question-paper" ? "spin" : ""} />
              Paper PDF
            </button>
            <button className="secondary-button" onClick={() => exportPdf("answer-key")} disabled={!!exporting || !questions.length}>
              <Download size={16} className={exporting === "answer-key" ? "spin" : ""} />
              Answer PDF
            </button>
            <button className="primary-button" onClick={generateDraft} disabled={loading}>
              <RefreshCw size={16} className={loading ? "spin" : ""} />
              {loading ? "Generating" : "Generate"}
            </button>
          </div>
        </header>

        <div className="builder-grid" style={builderGridStyle}>
          <aside className="setup-rail">
            <PanelTitle title="Paper setup" />
            <Field label="Subject">
              <Segmented
                value={subject}
                options={subjectOptions}
                onChange={(value) => setSubject(value as Subject)}
              />
            </Field>
            <Field label="Chapters">
              <div
                className={activeDropdown === "chapters" ? "chapter-dropdown active-menu" : "chapter-dropdown"}
                ref={chapterDropdownRef}
                onMouseEnter={() => setActiveDropdown("chapters")}
                onFocus={() => setActiveDropdown("chapters")}
              >
                <button type="button" className="chapter-trigger" onClick={() => setChapterMenuOpen((open) => !open)}>
                  <span>{chapterSelectionLabel(selectedChapters)}</span>
                  <span>{chapterMenuOpen ? "Close" : "Select"}</span>
                </button>
                {chapterMenuOpen ? (
                  <div className="chapter-menu">
                {chapters.map((chapter) => {
                  const checked = selectedChapters.includes(chapter.name);
                  return (
                    <label className={checked ? "chapter-option checked" : "chapter-option"} key={chapter.name}>
                      <input
                        type="checkbox"
                        checked={checked}
	                        onChange={() => {
	                          setSelectedChapters((current) => {
	                            if (current.includes(chapter.name)) {
	                              return current.filter((name) => name !== chapter.name);
	                            }
	                            return [...current, chapter.name];
	                          });
	                          setSelectedSubtopics([]);
                        }}
                      />
                      <span>{chapter.number}. {chapter.name}</span>
                    </label>
                  );
                })}
	                  </div>
	                ) : null}
	              </div>
	              <div className="inline-actions">
	                <button type="button" onClick={() => setSelectedChapters(chapters.map((chapter) => chapter.name))}>Select all</button>
	                <button type="button" onClick={() => {
	                  setSelectedChapters([]);
	                  setSelectedSubtopics([]);
	                }}>Clear chapters</button>
	              </div>
	            </Field>
            <Field label="Coverage">
              <div className="coverage-summary-card">
                <div className="coverage-summary-copy">
                  <strong>{coverageSummary.title}</strong>
                  <span>{coverageSummary.detail}</span>
                </div>
                <button
                  type="button"
                  className="secondary-button coverage-edit-button"
                  onClick={openCoverageEditor}
                  disabled={!selectedChapterRows.length}
                >
                  <SlidersHorizontal size={16} />
                  Edit
                </button>
              </div>
              {coverageSummary.lines.length ? (
                <div className="coverage-summary-list">
                  {coverageSummary.lines.map((line) => (
                    <div className="coverage-summary-line" key={line}>
                      <span>{line}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="template-note">Choose chapters first, then set chapter and subtopic weightage in one place.</span>
              )}
            </Field>
            <Field label="Template">
              <DropdownSelect
                value={paperTemplate}
                options={[
                  { value: "custom", label: "Custom" },
                  ...availableTemplates.map((template) => ({ value: template.id, label: template.label }))
                ]}
                onChange={(value) => applyPaperTemplate(value as PaperTemplateId)}
              />
              <span className="template-note">
                {paperTemplate === "custom"
                  ? "Use manual question counts."
                  : availableTemplates.find((template) => template.id === paperTemplate)?.description}
              </span>
            </Field>
            <Field label="Difficulty">
              <div className="difficulty-card">
                <Segmented
                  value={difficultyScope}
                  options={[
                    { value: "overall", label: "Overall" },
                    { value: "granular", label: "Granular" }
                  ]}
                  onChange={(value) => setDifficultyScope(value as DifficultyScope)}
                />
                {difficultyScope === "overall" ? (
                  <Segmented
                    value={paperLevel}
                    options={paperLevelOptions}
                    onChange={(value) => setPaperLevel(value as PaperLevel)}
                  />
                ) : (
                  <div className="difficulty-summary">
                    <div>
                      <strong>{difficultySummary.title}</strong>
                      <span>{difficultySummary.detail}</span>
                    </div>
                    <button
                      type="button"
                      className="secondary-button coverage-edit-button"
                      onClick={openCoverageEditor}
                      disabled={!selectedChapterRows.length}
                    >
                      <SlidersHorizontal size={16} />
                      Edit
                    </button>
                  </div>
                )}
              </div>
            </Field>
            {subject === "maths" ? (
              <Field label="Board variant">
                <Segmented
                  value={paperVariant}
                  options={[
                    { value: "basic", label: "Basic" },
                    { value: "standard", label: "Standard" }
                  ]}
                  onChange={(value) => setPaperVariant(value as PaperVariant)}
                />
              </Field>
            ) : (
              <Field label="Board variant">
                <span className="template-note">Science uses one common CBSE pattern with standard, medium and challenging difficulty levels.</span>
              </Field>
            )}
            <label className="toggle-row">
              <input type="checkbox" checked={usePyqPatterns} onChange={(event) => setUsePyqPatterns(event.target.checked)} />
              <span>Use PYQ pattern context</span>
            </label>

            <div className="mix-table">
              <div className="mix-heading">Question mix</div>
              {questionTypes.map((item) => (
                <div className="mix-row" key={item.type}>
                  <span>{item.label}</span>
                  <span>Sec {item.section} / {item.marks}m</span>
                  <Stepper
                    value={questionMix[item.type] ?? 0}
                    min={0}
                    max={40}
                    onChange={(value) => updateQuestionMix(item.type, value)}
                  />
	                </div>
		              ))}
		              <div className="inline-actions">
		                <button type="button" onClick={() => {
                    setQuestionMix(emptyQuestionMix());
                    setPaperTemplate("custom");
                  }}>Clear mix</button>
	              </div>
	            </div>
	            <div className="setup-actions">
	              <button className="secondary-button setup-secondary-button" onClick={clearSelections}>
	                Clear Selection
	              </button>
	              <button className="secondary-button setup-secondary-button" onClick={saveCurrentDraft}>
	                <Save size={16} />
	                Save Draft
	              </button>
	              <button className="primary-button setup-generate-button" onClick={generateDraft} disabled={loading}>
	                <RefreshCw size={16} className={loading ? "spin" : ""} />
                {loading ? "Generating" : "Generate Draft"}
              </button>
            </div>
          </aside>

	          <section className="paper-canvas">
	            {workspaceSection === "builder" ? (
	              generationProgress ? (
	                <GenerationProgressPanel progress={generationProgress} loading={loading} />
	              ) : (
	                <>
	                  <div className="summary-strip">
	                    <Metric label="Questions" value={questions.length} />
	                    <Metric label="Marks" value={totalMarks} />
	                    <Metric label="Issues" value={validationIssues.length} warn={validationIssues.length > 0} />
	                    <Metric label="Locked" value={questions.filter((q) => q.locked).length} />
	                  </div>
	                  {view === "paper" ? (
	                    <PaperHeader title={paperTitle} totalMarks={totalMarks} count={questions.length} />
	                  ) : null}
	                  {view === "paper" ? ["A", "B", "C", "D", "E"].map((section) => {
	                    const rows = questions.filter((q) => sectionFor(q.type) === section);
	                    if (!rows.length) return null;
	                    return (
	                      <section className="paper-section" key={section}>
	                        <div className="section-header">
	                          <div>
	                            <span className="section-chip">Section {section}</span>
	                            <strong>{sectionTitle(section)}</strong>
	                          </div>
	                          <span>{rows.reduce((sum, q) => sum + q.marks, 0)} marks</span>
	                        </div>
	                        <div className="question-list">
	                          {rows.map((question, index) => (
	                            <article
	                              key={question.id}
	                              className={question.id === selectedId ? "question-row selected" : "question-row"}
	                              onClick={() => setSelectedId(question.id)}
	                            >
	                              <div className="question-number">{index + 1}</div>
	                              <div className="question-main">
	                                <div className="row-meta">
	                                  <Badge>{labelFor(question.type)}</Badge>
	                                  <Badge>{question.marks} marks</Badge>
	                                  <Badge muted>{question.status ?? "generated"}</Badge>
	                                  {question.locked ? <Badge success>Locked</Badge> : null}
	                                </div>
	                                <div className="question-line">
	                                  <p><LatexText text={question.question} /></p>
	                                  <span className="print-marks">[{question.marks}]</span>
	                                </div>
	                                {question.options?.length ? (
	                                  <div className="paper-options">
	                                    {question.options.map((option) => (
	                                      <span key={option}><LatexText text={option} /></span>
	                                    ))}
	                                  </div>
	                                ) : null}
	                                <span className="muted-line">{question.topic}{question.subtopic ? ` / ${formatTitleCase(question.subtopic)}` : ""}</span>
	                              </div>
	                              <div className="row-actions">
	                                <IconButton title="Edit" onClick={() => {
	                                  setSelectedId(question.id);
	                                  setWorkspaceSection("builder");
	                                }}>
	                                  <Pencil size={16} />
	                                </IconButton>
	                                <IconButton title="Regenerate" onClick={() => setRegeneration({ source: question, mode: "refine", instruction: "", loading: false })}>
	                                  <RefreshCw size={16} />
	                                </IconButton>
	                                <IconButton title="Duplicate" onClick={() => duplicateQuestion(question)}>
	                                  <Copy size={16} />
	                                </IconButton>
	                                <IconButton title={question.locked ? "Unlock" : "Lock"} onClick={() => toggleLock(question)}>
	                                  {question.locked ? <Unlock size={16} /> : <Lock size={16} />}
	                                </IconButton>
	                                <IconButton title="Delete" onClick={() => deleteQuestion(question)}>
	                                  <Trash2 size={16} />
	                                </IconButton>
	                              </div>
	                            </article>
	                          ))}
	                        </div>
	                      </section>
	                    );
	                  }) : (
	                    <SolutionBooklet questions={questions} title={paperTitle} onSelect={setSelectedId} selectedId={selectedId} />
	                  )}
	                </>
	              )
	            ) : null}

	            {workspaceSection === "drafts" ? (
	              <DraftsSection drafts={drafts} onOpen={openDraft} onDelete={deleteDraft} onSaveCurrent={saveCurrentDraft} />
	            ) : null}

	            {workspaceSection === "library" ? (
	              <QuestionLibrarySection items={questionLibrary} onInsert={insertFromLibrary} />
	            ) : null}

	            {workspaceSection === "trash" ? (
	              <TrashSection
                  items={questionTrash}
                  onRestore={restoreTrashedQuestion}
                  onDeletePermanently={permanentlyDeleteTrashedQuestion}
                  onEmpty={emptyTrash}
                />
	            ) : null}

	          </section>

          <aside className="inspector">
            <button
              type="button"
              className="inspector-resize-handle"
              aria-label="Resize question editor"
              title="Drag to resize editor"
              onPointerDown={startInspectorResize}
              onPointerMove={resizeInspector}
              onPointerUp={stopInspectorResize}
              onPointerCancel={stopInspectorResize}
            />
            {selectedQuestion ? (
              <QuestionInspector key={selectedQuestion.id} question={selectedQuestion} onChange={updateSelected} />
            ) : (
              <div className="inspector-empty-wrap">
              <div className="empty-state inspector-empty-state">Choose a question to edit</div>
              </div>
            )}
          </aside>
        </div>
	      </section>

      {coverageEditorOpen && coverageDraft ? (
        <div className="modal-backdrop" onClick={closeCoverageEditor}>
          <div className="coverage-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Chapter Settings</h2>
                <p>
                  {difficultyScope === "granular"
                    ? "Distribute the paper and set difficulty only where a chapter or subtopic needs a different level."
                    : "Distribute the paper across selected chapters, then refine subtopics only where you need more control."}
                </p>
              </div>
              <button className="icon-button" onClick={closeCoverageEditor} type="button">
                <X size={18} />
              </button>
            </div>

            <div className="coverage-toolbar">
              <Segmented
                value={coverageDraft.mode}
                options={[
                  { value: "chapter", label: "Chapter only" },
                  { value: "chapter_subtopics", label: "Chapter + subtopics" }
                ]}
                onChange={(value) => updateCoverageDraftMode(value as CoverageMode)}
              />
              <div className="coverage-toolbar-actions">
                <button type="button" className="secondary-button" onClick={applyEqualCoverageSplit}>
                  Equal split
                </button>
                <button type="button" className="secondary-button" onClick={resetCoverageSubtopics}>
                  Reset subtopics
                </button>
              </div>
            </div>

            <div className="coverage-drawer-body">
              {selectedChapterRows.map((chapter) => {
                const chapterPlan = findCoverageChapter(coverageDraft, chapter.name);
                const chapterChallenge = findChallengeChapter(challengePreviewPlan ?? normalizedChallengePlan, chapter.name);
                const chapterEstimate = coveragePreviewEstimate?.chapterCounts[chapter.name] ?? 0;
                const chapterSubtopicEstimates = coveragePreviewEstimate?.subtopicCounts[chapter.name] ?? {};
                const isExpanded = expandedCoverageChapter === chapter.name;
                const supportsAllSelectedTypes = questionTypes
                  .filter((item) => (questionMix[item.type] ?? 0) > 0)
                  .every((item) => chapter.question_types.includes(item.type));
                if (!chapterPlan) return null;
                return (
                  <section className="coverage-chapter-card" key={chapter.name}>
                    <div className="coverage-chapter-row">
                      <div className="coverage-chapter-main">
                        {coverageDraft.mode === "chapter_subtopics" ? (
                          <button
                            type="button"
                            className="coverage-expand-button"
                            onClick={() => setExpandedCoverageChapter((current) => current === chapter.name ? null : chapter.name)}
                          >
                            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                          </button>
                        ) : (
                          <span className="coverage-expand-placeholder" />
                        )}
                        <div>
                          <strong>{chapter.number}. {chapter.name}</strong>
                          <span>
                            {chapterEstimate} estimated question{chapterEstimate === 1 ? "" : "s"}
                            {!supportsAllSelectedTypes ? " • selective by type" : ""}
                          </span>
                        </div>
                      </div>
                      <div className="coverage-row-controls">
                        {difficultyScope === "granular" && chapterChallenge ? (
                          <ChallengeSelect
                            value={chapterChallenge.challenge}
                            onChange={(value) => updateChallengeDraftChapter(chapter.name, value)}
                          />
                        ) : null}
                        <WeightInput
                          value={chapterPlan.weight}
                          onChange={(value) => updateCoverageDraftChapterWeight(chapter.name, value)}
                          disabled={selectedChapterRows.length <= 1}
                        />
                      </div>
                    </div>

                    {coverageDraft.mode === "chapter_subtopics" && isExpanded ? (
                      <div className="coverage-subtopics">
                        {chapterPlan.subtopics.map((subtopic) => {
                          const subtopicEstimate = chapterSubtopicEstimates[subtopic.name] ?? 0;
                          const subtopicChallenge = chapterChallenge?.subtopics.find((item) => item.name === subtopic.name);
                          return (
                            <div className="coverage-subtopic-row" key={`${chapter.name}-${subtopic.name}`}>
                              <div>
                                <strong>{formatTitleCase(subtopic.name)}</strong>
                                <span>{subtopicEstimate} estimated question{subtopicEstimate === 1 ? "" : "s"}</span>
                              </div>
                              <div className="coverage-row-controls">
                                {difficultyScope === "granular" && subtopicChallenge ? (
                                  <ChallengeSelect
                                    value={subtopicChallenge.challenge}
                                    onChange={(value) => updateChallengeDraftSubtopic(chapter.name, subtopic.name, value)}
                                  />
                                ) : null}
                                <WeightInput
                                  value={subtopic.weight}
                                  onChange={(value) => updateCoverageDraftSubtopicWeight(chapter.name, subtopic.name, value)}
                                  disabled={chapterPlan.subtopics.length <= 1}
                                />
                              </div>
                            </div>
                          );
                        })}
                        <div className={sumWeights(chapterPlan.subtopics.map((subtopic) => subtopic.weight)) === 100 ? "coverage-total-line" : "coverage-total-line invalid"}>
                          <span>Subtopic total</span>
                          <strong>{sumWeights(chapterPlan.subtopics.map((subtopic) => subtopic.weight))}%</strong>
                        </div>
                      </div>
                    ) : null}
                  </section>
                );
              })}
            </div>

            <div className="coverage-footer">
              <div className="coverage-footer-stats">
              </div>
              <div className="modal-actions">
                <button className="secondary-button" onClick={closeCoverageEditor} type="button">
                  Cancel
                </button>
                <button
                  className="primary-button"
                  onClick={applyCoverageEditor}
                  type="button"
                  disabled={!isCoveragePlanValid(coverageDraft, selectedChapterRows)}
                >
                  Apply weightage
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

	      {regeneration ? (
	        <div className="modal-backdrop" onClick={() => setRegeneration(null)}>
          <div className="regen-modal" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Regenerate question</h2>
                <p>Choose whether to refine the current item or replace it with a different setup.</p>
              </div>
              <button className="icon-button" onClick={() => setRegeneration(null)}>
                <X size={18} />
              </button>
            </div>
            <Segmented
              value={regeneration.mode}
              options={[
                { value: "refine", label: "Refine" },
                { value: "replace", label: "Different" }
              ]}
              onChange={(value) => setRegeneration({ ...regeneration, mode: value as "refine" | "replace" })}
            />
            <textarea
              value={regeneration.instruction}
              placeholder="Example: simplify calculations, make it board-style, use a real-life setup"
              onChange={(event) => setRegeneration({ ...regeneration, instruction: event.target.value })}
            />
            <div className="compare-grid">
              <ComparePanel title="Current" question={regeneration.source} />
              <ComparePanel title="Candidate" question={regeneration.candidate} loading={regeneration.loading} />
            </div>
            <div className="modal-actions">
              <button className="secondary-button" onClick={regenerateCandidate}>
                <RefreshCw size={16} className={regeneration.loading ? "spin" : ""} />
                Generate candidate
              </button>
              <button className="secondary-button" disabled={!regeneration.candidate} onClick={() => acceptCandidate(true)}>
                <Plus size={16} />
                Keep both
              </button>
              <button className="primary-button" disabled={!regeneration.candidate} onClick={() => acceptCandidate(false)}>
                <CheckCircle2 size={16} />
                Replace current
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

function PaperHeader({ title, totalMarks, count }: { title: string; totalMarks: number; count: number }) {
  return (
    <section className="paper-header">
      <h1>{title}</h1>
      <div className="paper-meta">
        <span>Time Allowed: 3 Hours</span>
        <span>Maximum Marks: {totalMarks || 80}</span>
      </div>
      <div className="instructions-block">
        <strong>General Instructions:</strong>
        <ol>
          <li>This question paper contains {count || "all"} questions. All questions are compulsory.</li>
          <li>Questions are grouped into sections A through E.</li>
          <li>Use of calculators is NOT permitted.</li>
        </ol>
      </div>
    </section>
  );
}

function SolutionBooklet({
  questions,
  title,
  selectedId,
  onSelect
}: {
  questions: Question[];
  title: string;
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="solution-booklet">
      <div className="paper-header compact">
        <h1>{title} - Answer Key</h1>
        <div className="paper-meta">
          <span>{questions.length} questions</span>
          <span>{questions.reduce((sum, question) => sum + question.marks, 0)} marks</span>
        </div>
      </div>
      {questions.map((question, index) => (
        <article
          key={question.id}
          className={question.id === selectedId ? "solution-row selected" : "solution-row"}
          onClick={() => onSelect(question.id)}
        >
          <div className="solution-heading">
            <strong>Question {index + 1}</strong>
            <Badge>{labelFor(question.type)}</Badge>
            <Badge>{question.marks} marks</Badge>
          </div>
          <p><LatexText text={question.question} /></p>
          <div className="answer-line">
            <strong>Answer:</strong>
            <LatexText text={question.answer || "Not provided"} />
          </div>
          {question.solution?.steps?.length ? (
            <ol className="solution-steps">
              {question.solution.steps.map((step, stepIndex) => (
                <li key={`${question.id}-step-${stepIndex}`}>
                  <LatexText text={step} />
                </li>
              ))}
            </ol>
          ) : (
            <div className="muted-line">No solution steps provided.</div>
          )}
          {question.solution?.derivation ? (
            <div className="derivation-line">
              <LatexText text={question.solution.derivation} />
            </div>
          ) : null}
        </article>
      ))}
    </section>
  );
}

function GenerationProgressPanel({ progress, loading }: { progress: GenerationProgress; loading: boolean }) {
  const percent = progress.totalQuestions
    ? Math.round((progress.completedQuestions / progress.totalQuestions) * 100)
    : 0;
  const completedJobs = progress.jobs.filter((job) => job.status === "complete").length;
  const failed = progress.jobs.some((job) => job.status === "failed");

  return (
    <section className="generation-panel">
      <div className="generation-card">
        <div className="generation-head">
          <div>
            <span className="eyebrow">Question generation</span>
            <h2>{failed ? "Generation needs attention" : loading ? progress.activeLabel : "Generation paused"}</h2>
            <p>{progress.completedQuestions} of {progress.totalQuestions} questions generated across {progress.jobs.length} batches.</p>
          </div>
          <div className={failed ? "generation-status failed" : "generation-status"}>
            {failed ? <AlertTriangle size={18} /> : <RefreshCw size={18} className={loading ? "spin" : ""} />}
            <span>{failed ? "Failed" : loading ? "Running" : "Waiting"}</span>
          </div>
        </div>

        <div className="generation-meter" aria-label={`${percent}% complete`}>
          <span style={{ width: `${percent}%` }} />
        </div>

        <div className="generation-stats">
          <Metric label="Generated" value={progress.completedQuestions} />
          <Metric label="Target" value={progress.totalQuestions} />
          <Metric label="Batches" value={completedJobs} />
          <Metric label="Queued" value={progress.jobs.filter((job) => job.status === "queued").length} />
        </div>

        <div className="generation-log">
          {progress.jobs.map((job) => (
            <div className={`generation-log-row ${job.status}`} key={job.id}>
              <div className="generation-log-icon">
                {job.status === "complete" ? <CheckCircle2 size={16} /> : null}
                {job.status === "running" ? <RefreshCw size={16} className="spin" /> : null}
                {job.status === "failed" ? <AlertTriangle size={16} /> : null}
                {job.status === "queued" ? <span /> : null}
              </div>
              <div>
                <strong>{job.label}</strong>
                <span>{job.error || job.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DraftsSection({
  drafts,
  onOpen,
  onDelete,
  onSaveCurrent
}: {
  drafts: DraftRecord[];
  onOpen: (draft: DraftRecord) => void;
  onDelete: (draft: DraftRecord) => void;
  onSaveCurrent: () => void;
}) {
  return (
    <section className="library-panel">
      <div className="library-header">
        <div>
          <span className="eyebrow">Drafts</span>
          <h2>Saved paper drafts</h2>
          <p>Drafts include paper setup, generated questions, edits, and solutions.</p>
        </div>
        <button className="primary-button" onClick={onSaveCurrent}>
          <Save size={16} />
          Save Current
        </button>
      </div>

      {drafts.length ? (
        <div className="library-list">
          {drafts.map((draft) => (
              <article className="library-row" key={draft.id}>
                <div className="library-row-main">
                  <div className="row-meta visible">
                    <Badge>{draft.questions.length} questions</Badge>
                    <Badge>{draft.questions.reduce((sum, question) => sum + Number(question.marks || 0), 0)} marks</Badge>
                    {draft.generationId ? <Badge muted>{draft.generationId}</Badge> : null}
                  </div>
                  <h3>{draft.title}</h3>
                  <span className="muted-line">Saved {formatDateTime(draft.updatedAt)}</span>
                </div>
              <div className="library-actions">
                <button className="secondary-button" onClick={() => onOpen(draft)}>
                  <FileText size={16} />
                  Open
                </button>
                <button className="secondary-button" onClick={() => onDelete(draft)}>
                  <Trash2 size={16} />
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">No drafts saved yet</div>
      )}
    </section>
  );
}

function QuestionLibrarySection({ items, onInsert }: { items: QuestionLibraryItem[]; onInsert: (item: QuestionLibraryItem) => void }) {
  return (
    <section className="library-panel">
      <div className="library-header">
        <div>
          <span className="eyebrow">Question Library</span>
          <h2>Generated question history</h2>
          <p>Every generated question and regenerated candidate is stored here for reuse.</p>
        </div>
        <Badge>{items.length} saved</Badge>
      </div>

      {items.length ? (
        <div className="library-list">
          {items.map((item) => (
            <article className="library-row" key={item.libraryId}>
              <div className="library-row-main">
                <div className="row-meta visible">
                  <Badge>{labelFor(item.type)}</Badge>
                  <Badge>{item.marks} marks</Badge>
                  <Badge muted>{item.generationLabel}</Badge>
                </div>
                <p><LatexText text={item.question} /></p>
                <span className="muted-line">{item.topic}{item.subtopic ? ` / ${formatTitleCase(item.subtopic)}` : ""} / {formatDateTime(item.storedAt)}</span>
              </div>
              <div className="library-actions">
                <button className="secondary-button" onClick={() => onInsert(item)}>
                  <Plus size={16} />
                  Insert
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">Generated questions will appear here</div>
      )}
    </section>
  );
}

function TrashSection({
  items,
  onRestore,
  onDeletePermanently,
  onEmpty
}: {
  items: TrashedQuestionRecord[];
  onRestore: (item: TrashedQuestionRecord) => void;
  onDeletePermanently: (item: TrashedQuestionRecord) => void;
  onEmpty: () => void;
}) {
  const activeItems = pruneExpiredTrash(items);

  return (
    <section className="library-panel">
      <div className="library-header">
        <div>
          <span className="eyebrow">Trash</span>
          <h2>Deleted questions</h2>
          <p>Deleted questions stay here for 30 days. Restore them back into the builder or remove them permanently.</p>
        </div>
        <div className="library-actions visible">
          <Badge>{activeItems.length} item{activeItems.length === 1 ? "" : "s"}</Badge>
          <button className="secondary-button" onClick={onEmpty} disabled={!activeItems.length}>
            <Trash2 size={16} />
            Empty Trash
          </button>
        </div>
      </div>

      {activeItems.length ? (
        <div className="library-list">
          {activeItems.map((item) => (
            <article className="library-row" key={item.trashId}>
              <div className="library-row-main">
                <div className="row-meta visible">
                  <Badge>{labelFor(item.question.type)}</Badge>
                  <Badge>{item.question.marks} marks</Badge>
                  <Badge muted>{item.deletedFromTitle}</Badge>
                </div>
                <p><LatexText text={item.question.question} /></p>
                <span className="muted-line">
                  Deleted {formatDateTime(item.deletedAt)} • expires {formatRetentionDate(item.expiresAt)}
                </span>
              </div>
              <div className="library-actions visible">
                <button className="secondary-button" onClick={() => onRestore(item)}>
                  <RefreshCw size={16} />
                  Restore
                </button>
                <button className="secondary-button danger-button" onClick={() => onDeletePermanently(item)}>
                  <Trash2 size={16} />
                  Delete Permanently
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">Deleted questions will stay here for 30 days before automatic cleanup.</div>
      )}
    </section>
  );
}

function ExportsSection({
  disabled,
  exporting,
  onPreview,
  onPaper,
  onAnswer
}: {
  disabled: boolean;
  exporting: "question-paper" | "answer-key" | null;
  onPreview: () => void;
  onPaper: () => void;
  onAnswer: () => void;
}) {
  return (
    <section className="library-panel export-panel">
      <div className="library-header">
        <div>
          <span className="eyebrow">Exports</span>
          <h2>PDF output</h2>
          <p>Preview and downloads use the backend PDF renderer, matching the CLI-style paper format.</p>
        </div>
      </div>
      <div className="export-actions-grid">
        <button className="secondary-button" onClick={onPreview} disabled={disabled}>
          <Eye size={16} />
          Preview Question Paper
        </button>
        <button className="secondary-button" onClick={onPaper} disabled={disabled}>
          <Download size={16} className={exporting === "question-paper" ? "spin" : ""} />
          Download Question Paper
        </button>
        <button className="secondary-button" onClick={onAnswer} disabled={disabled}>
          <Download size={16} className={exporting === "answer-key" ? "spin" : ""} />
          Download Answer Key
        </button>
      </div>
    </section>
  );
}

function QuestionInspector({ question, onChange }: { question: Question; onChange: (patch: Partial<Question>) => void }) {
  const [tab, setTab] = useState<"question" | "solution" | "metadata" | "history">("question");
  const locked = question.locked;
  return (
    <div className="inspector-inner">
      <div className="inspector-header">
        <div>
          <span className="eyebrow">Question editor</span>
          <h2>{labelFor(question.type)}</h2>
        </div>
        {locked ? <Lock size={18} /> : <Save size={18} />}
      </div>
      <Segmented
        value={tab}
        options={[
          { value: "question", label: "Question" },
          { value: "solution", label: "Solution" },
          { value: "metadata", label: "Meta" },
          { value: "history", label: "History" }
        ]}
        onChange={(value) => setTab(value as typeof tab)}
      />

      {tab === "question" ? (
        <div className="form-stack">
          <Field label="Question text">
            <textarea disabled={locked} value={question.question} onChange={(event) => onChange({ question: event.target.value })} />
          </Field>
          <Field label="Marks">
            <input disabled={locked} type="number" min={1} max={5} value={question.marks} onChange={(event) => onChange({ marks: Number(event.target.value) })} />
          </Field>
          {question.type === "mcq" ? (
            <Field label="Options">
              <div className="option-list">
                {(question.options ?? ["", "", "", ""]).map((option, index) => (
                  <input
                    key={index}
                    disabled={locked}
                    value={option}
                    onChange={(event) => {
                      const next = [...(question.options ?? ["", "", "", ""])];
                      next[index] = event.target.value;
                      onChange({ options: next });
                    }}
                  />
                ))}
              </div>
            </Field>
          ) : null}
          <Field label="Answer">
            <input disabled={locked} value={question.answer} onChange={(event) => onChange({ answer: event.target.value })} />
          </Field>
        </div>
      ) : null}

      {tab === "solution" ? (
        <div className="form-stack">
          <Field label="Solution steps">
            <textarea
              disabled={locked}
              value={(question.solution?.steps ?? []).join("\n")}
              onChange={(event) => onChange({ solution: { ...question.solution, steps: event.target.value.split("\n") } })}
            />
          </Field>
          <Field label="Derivation">
            <textarea
              disabled={locked}
              value={question.solution?.derivation ?? ""}
              onChange={(event) => onChange({ solution: { ...question.solution, derivation: event.target.value } })}
            />
          </Field>
        </div>
      ) : null}

      {tab === "metadata" ? (
        <pre className="metadata-view">{JSON.stringify(question.metadata ?? {}, null, 2)}</pre>
      ) : null}

      {tab === "history" ? (
        <div className="history-list">
          {(question.history ?? []).length ? (
            question.history?.map((item) => (
              <div className="history-row" key={item.id}>
                <History size={16} />
                <div>
                  <strong>{item.label}</strong>
                  <span>{item.timestamp}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">No previous versions</div>
          )}
        </div>
      ) : null}
    </div>
  );
}

function LatexText({ text }: { text: string }) {
  const blocks = splitTableBlocks(normalizeDisplayText(text));
  return (
    <>
      {blocks.map((block, index) => {
        if (block.type === "table") {
          return <MarkdownTable key={`table-${index}`} rows={block.rows} />;
        }
        return renderLatexContent(block.source, `plain-${index}`);
      })}
    </>
  );
}

type TextBlock =
  | { type: "text"; source: string }
  | { type: "table"; rows: string[][] };

function renderLatexContent(source: string, keyPrefix: string) {
  const parts = tokenizeLatex(source);
  return parts.map((part, index) => {
    if (part.type === "math") {
      return <MathNode key={`${keyPrefix}-math-${index}`} source={part.source} display={part.display} />;
    }
    return renderPlainText(part.source, `${keyPrefix}-plain-${index}`);
  });
}

function MarkdownTable({ rows }: { rows: string[][] }) {
  if (!rows.length) return null;
  const [head, ...body] = rows;
  return (
    <div className="latex-table-wrap">
      <table className="latex-table">
        <thead>
          <tr>
            {head.map((cell, index) => (
              <th key={`head-${index}`}>{renderLatexContent(cell, `table-head-${index}`)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <td key={`cell-${rowIndex}-${cellIndex}`}>{renderLatexContent(cell, `table-${rowIndex}-${cellIndex}`)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function splitTableBlocks(text: string): TextBlock[] {
  const lines = text.split("\n");
  const blocks: TextBlock[] = [];
  let buffer: string[] = [];

  const flushText = () => {
    const source = buffer.join("\n").trim();
    if (source) {
      blocks.push({ type: "text", source });
    }
    buffer = [];
  };

  for (let index = 0; index < lines.length;) {
    if (looksLikeTableStart(lines, index)) {
      flushText();
      const tableLines = [lines[index], lines[index + 1]];
      index += 2;
      while (index < lines.length && isPipeTableRow(lines[index])) {
        tableLines.push(lines[index]);
        index += 1;
      }
      const rows = parseMarkdownTable(tableLines);
      if (rows.length) {
        blocks.push({ type: "table", rows });
      }
      continue;
    }
    buffer.push(lines[index]);
    index += 1;
  }
  flushText();
  return blocks;
}

function looksLikeTableStart(lines: string[], index: number) {
  return isPipeTableRow(lines[index]) && index + 1 < lines.length && isMarkdownTableSeparator(lines[index + 1]);
}

function isPipeTableRow(line: string) {
  const trimmed = line.trim();
  return trimmed.includes("|") && splitTableRow(trimmed).length >= 2;
}

function isMarkdownTableSeparator(line: string) {
  const cells = splitTableRow(line.trim());
  return cells.length >= 2 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function parseMarkdownTable(lines: string[]) {
  return lines
    .filter((line, index) => index !== 1 && isPipeTableRow(line))
    .map((line) => splitTableRow(line).map((cell) => cell.trim()))
    .filter((row) => row.length >= 2);
}

function splitTableRow(line: string) {
  return line
    .replace(/^\s*\|/, "")
    .replace(/\|\s*$/, "")
    .split("|");
}

function normalizeDisplayText(text: string) {
  return String(text ?? "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/\\newline\b/g, "\n")
    .replace(/\\n(?!abla|eq|eqq|ot|u\b)/g, "\n")
    .replace(/\\t(?!imes|heta|an|o\b|ext|frac|ilde|riangle|au\b)/g, " ");
}

function renderPlainText(source: string, keyPrefix: string) {
  return tokenizeLooseMath(cleanPlainText(source)).map((part, index) => {
    if (part.type === "math") {
      return <MathNode key={`${keyPrefix}-${index}`} source={part.source} display={false} />;
    }
    return <span key={`${keyPrefix}-${index}`}>{part.source}</span>;
  });
}

function cleanPlainText(text: string) {
  return normalizeDisplayText(text)
    .replace(/\bimes\b/g, "\\times")
    .replace(/\\{2,}/g, " ")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ");
}

function tokenizeLooseMath(text: string): { type: "text" | "math"; source: string; display: boolean }[] {
  const tokens: { type: "text" | "math"; source: string; display: boolean }[] = [];
  const looseTerm = String.raw`(?:\\frac\{[^{}]+\}\{[^{}]+\}|\\sqrt\{[^{}]+\}|[-+]?\d+(?:\.\d+)?[A-Za-z]?(?:\^\{?\d+\}?)?|[-+]?[A-Za-z](?:\^\{?\d+\}?|_\{?[A-Za-z0-9]+\}?)?)`;
  const looseOperator = String.raw`(?:>=|<=|\\times|\\div|\\cdot|\\pm|[+\-*/=<>])`;
  const pattern = new RegExp(
    `(${looseTerm}(?:\\s*${looseOperator}\\s*${looseTerm})+|(?:\\d+\\s*)?[A-Za-z](?:\\^\\{?\\d+\\}?|_\\{?[A-Za-z0-9]+\\}?))`,
    "g"
  );
  let lastIndex = 0;
  for (const match of text.matchAll(pattern)) {
    const raw = match[0];
    const index = match.index ?? 0;
    if (index > lastIndex) {
      tokens.push({ type: "text", source: text.slice(lastIndex, index), display: false });
    }
    if (isLooseMathCandidate(raw)) {
      tokens.push({ type: "math", source: raw.trim(), display: false });
    } else {
      tokens.push({ type: "text", source: raw, display: false });
    }
    lastIndex = index + raw.length;
  }
  if (lastIndex < text.length) {
    tokens.push({ type: "text", source: text.slice(lastIndex), display: false });
  }
  return tokens;
}

function isLooseMathCandidate(source: string) {
  const compact = source.replace(/\s+/g, "");
  return /[=^_]|\d|\\frac|\\sqrt/.test(compact) && !/^[A-Za-z]-[A-Za-z]$/.test(compact);
}

function cleanGeneratedText(text: string) {
  const normalized = normalizeDisplayText(text);
  if (containsMarkdownTable(normalized)) {
    return normalized
      .replace(/\bimes\b/g, "\\times")
      .replace(/[ \t]+/g, " ")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .join("\n")
      .trim();
  }
  return cleanPlainText(text).trim();
}

function containsMarkdownTable(text: string) {
  const lines = normalizeDisplayText(text).split("\n");
  return lines.some((_, index) => looksLikeTableStart(lines, index));
}

function cleanDerivationText(text: string) {
  return normalizeDisplayText(text)
    .replace(/\\{3,}/g, "\\\\")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .join(" \\\\ ")
    .trim();
}

function MathNode({ source, display }: { source: string; display: boolean }) {
  source = normalizeDisplayText(source);
  const lines = source.split(/\\\\/).map((line) => line.trim()).filter(Boolean);
  if (lines.length > 1) {
    return (
      <span className="latex-lines">
        {lines.map((line, index) => (
          <MathNode key={`${line}-${index}`} source={line} display={false} />
        ))}
      </span>
    );
  }

  try {
    return (
      <span
        className={display ? "latex-display" : "latex-inline"}
        dangerouslySetInnerHTML={{
          __html: katex.renderToString(source, {
            displayMode: display,
            throwOnError: false,
            strict: false
          })
        }}
      />
    );
  } catch {
    return <span className="latex-inline fallback">{source}</span>;
  }
}

function tokenizeLatex(text: string): { type: "text" | "math"; source: string; display: boolean }[] {
  const tokens: { type: "text" | "math"; source: string; display: boolean }[] = [];
  const pattern = /(\$\$[\s\S]+?\$\$|\$[^$]+\$|\\\([\s\S]+?\\\)|\\\[[\s\S]+?\\\])/g;
  let lastIndex = 0;
  for (const match of text.matchAll(pattern)) {
    const raw = match[0];
    const index = match.index ?? 0;
    if (index > lastIndex) {
      tokens.push({ type: "text", source: text.slice(lastIndex, index), display: false });
    }
    if (raw.startsWith("$$")) {
      tokens.push({ type: "math", source: raw.slice(2, -2), display: true });
    } else if (raw.startsWith("\\[")) {
      tokens.push({ type: "math", source: raw.slice(2, -2), display: true });
    } else if (raw.startsWith("\\(")) {
      tokens.push({ type: "math", source: raw.slice(2, -2), display: false });
    } else {
      tokens.push({ type: "math", source: raw.slice(1, -1), display: false });
    }
    lastIndex = index + raw.length;
  }
  if (lastIndex < text.length) {
    tokens.push({ type: "text", source: text.slice(lastIndex), display: false });
  }
  return tokens;
}

function ComparePanel({ title, question, loading }: { title: string; question?: Question; loading?: boolean }) {
  return (
    <div className="compare-panel">
      <h3>{title}</h3>
      {loading ? (
        <div className="empty-state">Generating candidate</div>
      ) : question ? (
        <>
          <p><LatexText text={question.question} /></p>
          <span className="muted-line">{labelFor(question.type)} / {question.marks} marks</span>
          <strong>Answer: {question.answer}</strong>
        </>
      ) : (
        <div className="empty-state">No candidate yet</div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="field">
      <span>{label}</span>
      {children}
    </div>
  );
}

function Segmented({
  value,
  options,
  onChange
}: {
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="segmented">
      {options.map((option) => (
        <button key={option.value} className={option.value === value ? "active" : ""} onClick={() => onChange(option.value)} type="button">
          {option.label}
        </button>
      ))}
    </div>
  );
}

function DropdownSelect<T extends string>({
  value,
  options,
  onChange,
  disabled
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);
  const selected = options.find((option) => option.value === value) ?? options[0];

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (target instanceof Node && dropdownRef.current?.contains(target)) {
        return;
      }
      setOpen(false);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [open]);

  return (
    <div className={open ? "chapter-dropdown dropdown-select active-menu" : "chapter-dropdown dropdown-select"} ref={dropdownRef}>
      <button
        type="button"
        className="chapter-trigger dropdown-trigger"
        onClick={() => setOpen((current) => !current)}
        disabled={disabled}
      >
        <span>{selected?.label ?? "Select"}</span>
        <span>{open ? "Close" : "Select"}</span>
      </button>
      {open ? (
        <div className="chapter-menu dropdown-select-menu">
          {options.map((option) => (
            <button
              type="button"
              className={option.value === value ? "chapter-option checked" : "chapter-option"}
              key={option.value}
              onClick={() => {
                onChange(option.value);
                setOpen(false);
              }}
            >
              <span>{option.label}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function Stepper({ value, min, max, onChange }: { value: number; min: number; max: number; onChange: (value: number) => void }) {
  return (
    <div className="stepper">
      <button type="button" onClick={() => onChange(Math.max(min, value - 1))}>-</button>
      <input value={value} readOnly />
      <button type="button" onClick={() => onChange(Math.min(max, value + 1))}>+</button>
    </div>
  );
}

function WeightInput({ value, onChange, disabled }: { value: number; onChange: (value: number) => void; disabled?: boolean }) {
  return (
    <label className={disabled ? "weight-input disabled" : "weight-input"}>
      <input
        type="number"
        min={0}
        max={100}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        disabled={disabled}
      />
      <span>%</span>
    </label>
  );
}

function ChallengeSelect({ value, onChange }: { value: ChallengeOverride; onChange: (value: ChallengeOverride) => void }) {
  return (
    <DropdownSelect
      value={value}
      options={challengeOverrideOptions}
      onChange={onChange}
    />
  );
}

function IconButton({ children, title, active, onClick }: { children: React.ReactNode; title: string; active?: boolean; onClick?: () => void }) {
  return (
    <button className={active ? "icon-button active" : "icon-button"} title={title} type="button" onClick={(event) => {
      event.stopPropagation();
      onClick?.();
    }}>
      {children}
    </button>
  );
}

function PanelTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="panel-title">
      {subtitle ? <span className="eyebrow">{subtitle}</span> : null}
      <h2>{title}</h2>
    </div>
  );
}

function Metric({ label, value, warn }: { label: string; value: number; warn?: boolean }) {
  return (
    <div className={warn ? "metric warn" : "metric"}>
      {warn ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Badge({ children, muted, success }: { children: React.ReactNode; muted?: boolean; success?: boolean }) {
  return <span className={success ? "badge success" : muted ? "badge muted" : "badge"}>{children}</span>;
}

function normalizeQuestionRecord(question: Question): Question {
  return {
    ...question,
    question: cleanGeneratedText(question.question),
    answer: cleanGeneratedText(question.answer),
    topic: cleanGeneratedText(question.topic),
    subtopic: question.subtopic ? cleanGeneratedText(question.subtopic) : question.subtopic,
    options: question.options?.map(cleanGeneratedText),
    solution: question.solution
      ? {
          ...question.solution,
          steps: question.solution.steps?.map(cleanGeneratedText).filter(Boolean),
          derivation: question.solution.derivation ? cleanDerivationText(question.solution.derivation) : question.solution.derivation
        }
      : question.solution
  };
}

function withClientState(status: QuestionStatus) {
  return (question: Question): Question => normalizeQuestionRecord({
    ...question,
    id: question.id || crypto.randomUUID(),
    status,
    locked: false,
    history: question.history ?? []
  });
}

function emptyQuestionMix(): Record<QuestionType, number> {
  return questionTypes.reduce((accumulator, item) => {
    accumulator[item.type] = 0;
    return accumulator;
  }, {} as Record<QuestionType, number>);
}

function splitGenerationCount(count: number, maxBatchSize = 10): number[] {
  const batches: number[] = [];
  let remaining = Math.max(0, count);
  while (remaining > 0) {
    const next = Math.min(maxBatchSize, remaining);
    batches.push(next);
    remaining -= next;
  }
  return batches;
}

function loadStoredList<T>(key: string): T[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) as T[] : [];
  } catch {
    return [];
  }
}

function saveStoredList<T>(key: string, rows: T[]) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(rows));
  } catch {
    // Local persistence is best-effort; generation and export should keep working.
  }
}

function clampInspectorWidth(width: number, viewportWidth?: number) {
  const viewportMax = viewportWidth
    ? Math.max(MIN_INSPECTOR_WIDTH, viewportWidth - 60 - 300 - 420)
    : MAX_INSPECTOR_WIDTH;
  return Math.min(Math.max(width, MIN_INSPECTOR_WIDTH), Math.min(MAX_INSPECTOR_WIDTH, viewportMax));
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function addDays(value: string, days: number) {
  const date = new Date(value);
  date.setDate(date.getDate() + days);
  return date.toISOString();
}

function pruneExpiredTrash(items: TrashedQuestionRecord[]) {
  const now = Date.now();
  return items.filter((item) => {
    const expiresAt = new Date(item.expiresAt).getTime();
    return Number.isFinite(expiresAt) && expiresAt > now;
  });
}

function formatRetentionDate(value: string) {
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) return value;
  const msRemaining = target.getTime() - Date.now();
  if (msRemaining <= 0) return "today";
  const daysRemaining = Math.ceil(msRemaining / (1000 * 60 * 60 * 24));
  return `${formatDateTime(value)} (${daysRemaining} day${daysRemaining === 1 ? "" : "s"} left)`;
}

function clampWeight(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function sumWeights(weights: number[]) {
  return weights.reduce((sum, weight) => sum + clampWeight(weight), 0);
}

function createPercentageWeights(length: number) {
  if (length <= 0) return [];
  const base = Math.floor(100 / length);
  const remainder = 100 - (base * length);
  return Array.from({ length }, (_, index) => base + (index < remainder ? 1 : 0));
}

function createCoveragePlan(chapters: Chapter[], mode?: CoverageMode): CoveragePlan {
  const chapterWeights = createPercentageWeights(chapters.length);
  return {
    mode: mode ?? (chapters.length <= 1 ? "chapter_subtopics" : "chapter"),
    chapters: chapters.map((chapter, chapterIndex) => ({
      chapterName: chapter.name,
      weight: chapterWeights[chapterIndex] ?? 0,
      subtopics: chapter.subtopics.map((subtopic, subtopicIndex) => ({
        name: subtopic,
        weight: createPercentageWeights(chapter.subtopics.length)[subtopicIndex] ?? 0
      }))
    }))
  };
}

function createChallengePlan(chapters: Chapter[]): ChallengePlan {
  return {
    chapters: chapters.map((chapter) => ({
      chapterName: chapter.name,
      challenge: "inherit",
      subtopics: chapter.subtopics.map((subtopic) => ({
        name: subtopic,
        challenge: "inherit"
      }))
    }))
  };
}

function cloneCoveragePlan(plan: CoveragePlan): CoveragePlan {
  return {
    mode: plan.mode,
    chapters: plan.chapters.map((chapter) => ({
      ...chapter,
      subtopics: chapter.subtopics.map((subtopic) => ({ ...subtopic }))
    }))
  };
}

function cloneChallengePlan(plan: ChallengePlan): ChallengePlan {
  return {
    chapters: plan.chapters.map((chapter) => ({
      ...chapter,
      subtopics: chapter.subtopics.map((subtopic) => ({ ...subtopic }))
    }))
  };
}

function distributeByWeight<T>(count: number, items: { target: T; weight: number }[]) {
  if (count <= 0 || !items.length) return [] as { target: T; count: number }[];

  const safeWeights = items.map((item) => Math.max(0, item.weight));
  const totalWeight = safeWeights.reduce((sum, weight) => sum + weight, 0);
  const workingWeights = totalWeight > 0 ? safeWeights : Array.from({ length: items.length }, () => 1);
  const workingTotal = workingWeights.reduce((sum, weight) => sum + weight, 0);

  const allocations = items.map((item, index) => {
    const raw = count * (workingWeights[index] / workingTotal);
    const floor = Math.floor(raw);
    return {
      target: item.target,
      count: floor,
      remainder: raw - floor,
      index
    };
  });

  let remaining = count - allocations.reduce((sum, allocation) => sum + allocation.count, 0);
  allocations
    .sort((left, right) => {
      if (right.remainder !== left.remainder) return right.remainder - left.remainder;
      return left.index - right.index;
    })
    .forEach((allocation) => {
      if (remaining <= 0) return;
      allocation.count += 1;
      remaining -= 1;
    });

  return allocations
    .sort((left, right) => left.index - right.index)
    .filter((allocation) => allocation.count > 0)
    .map(({ target, count: allocationCount }) => ({ target, count: allocationCount }));
}

function rebalanceWeightEntries<T extends { weight: number }>(items: T[]) {
  if (!items.length) return items;
  const normalized = distributeByWeight(100, items.map((item) => ({ target: item, weight: clampWeight(item.weight) })));
  const nextWeights = new Map(normalized.map((entry) => [entry.target, entry.count]));
  return items.map((item) => ({
    ...item,
    weight: nextWeights.get(item) ?? 0
  }));
}

function normalizeCoveragePlan(chapters: Chapter[], plan?: CoveragePlan | null): CoveragePlan {
  const basePlan = plan ? cloneCoveragePlan(plan) : createCoveragePlan(chapters);
  const defaultPlan = createCoveragePlan(chapters, basePlan.mode);

  const mergedChapters = defaultPlan.chapters.map((chapter) => {
    const existingChapter = basePlan.chapters.find((item) => item.chapterName === chapter.chapterName);
    const mergedSubtopics = chapter.subtopics.map((subtopic) => {
      const existingSubtopic = existingChapter?.subtopics.find((item) => item.name === subtopic.name);
      return {
        name: subtopic.name,
        weight: existingSubtopic ? clampWeight(existingSubtopic.weight) : subtopic.weight
      };
    });
    return {
      chapterName: chapter.chapterName,
      weight: existingChapter ? clampWeight(existingChapter.weight) : chapter.weight,
      subtopics: rebalanceWeightEntries(mergedSubtopics)
    };
  });

  return {
    mode: basePlan.mode,
    chapters: rebalanceWeightEntries(mergedChapters)
  };
}

function normalizeChallengePlan(chapters: Chapter[], plan?: ChallengePlan | null): ChallengePlan {
  const basePlan = plan ? cloneChallengePlan(plan) : createChallengePlan(chapters);
  const defaultPlan = createChallengePlan(chapters);

  return {
    chapters: defaultPlan.chapters.map((chapter) => {
      const existingChapter = basePlan.chapters.find((item) => item.chapterName === chapter.chapterName);
      return {
        chapterName: chapter.chapterName,
        challenge: existingChapter?.challenge ?? "inherit",
        subtopics: chapter.subtopics.map((subtopic) => {
          const existingSubtopic = existingChapter?.subtopics.find((item) => item.name === subtopic.name);
          return {
            name: subtopic.name,
            challenge: existingSubtopic?.challenge ?? "inherit"
          };
        })
      };
    })
  };
}

function areCoveragePlansEqual(left?: CoveragePlan | null, right?: CoveragePlan | null) {
  if (!left || !right) return left === right;
  if (left.mode !== right.mode || left.chapters.length !== right.chapters.length) return false;
  return left.chapters.every((chapter, chapterIndex) => {
    const rightChapter = right.chapters[chapterIndex];
    if (!rightChapter || chapter.chapterName !== rightChapter.chapterName || chapter.weight !== rightChapter.weight) {
      return false;
    }
    if (chapter.subtopics.length !== rightChapter.subtopics.length) return false;
    return chapter.subtopics.every((subtopic, subtopicIndex) => {
      const rightSubtopic = rightChapter.subtopics[subtopicIndex];
      return Boolean(
        rightSubtopic &&
        subtopic.name === rightSubtopic.name &&
        subtopic.weight === rightSubtopic.weight
      );
    });
  });
}

function areChallengePlansEqual(left?: ChallengePlan | null, right?: ChallengePlan | null) {
  if (!left || !right) return left === right;
  if (left.chapters.length !== right.chapters.length) return false;
  return left.chapters.every((chapter, chapterIndex) => {
    const rightChapter = right.chapters[chapterIndex];
    if (!rightChapter || chapter.chapterName !== rightChapter.chapterName || chapter.challenge !== rightChapter.challenge) {
      return false;
    }
    if (chapter.subtopics.length !== rightChapter.subtopics.length) return false;
    return chapter.subtopics.every((subtopic, subtopicIndex) => {
      const rightSubtopic = rightChapter.subtopics[subtopicIndex];
      return Boolean(
        rightSubtopic &&
        subtopic.name === rightSubtopic.name &&
        subtopic.challenge === rightSubtopic.challenge
      );
    });
  });
}

function isCoveragePlanValid(plan: CoveragePlan, chapters: Chapter[]) {
  if (!chapters.length) return false;
  if (sumWeights(plan.chapters.map((chapter) => chapter.weight)) !== 100) return false;
  if (plan.mode !== "chapter_subtopics") return true;
  return plan.chapters.every((chapter) => sumWeights(chapter.subtopics.map((subtopic) => subtopic.weight)) === 100);
}

function findCoverageChapter(plan: CoveragePlan, chapterName: string) {
  return plan.chapters.find((chapter) => chapter.chapterName === chapterName);
}

function findChallengeChapter(plan: ChallengePlan, chapterName: string) {
  return plan.chapters.find((chapter) => chapter.chapterName === chapterName);
}

function summarizeCoveragePlan(chapters: Chapter[], plan: CoveragePlan) {
  if (!chapters.length) {
    return {
      title: "No chapters selected",
      detail: "Choose chapters to start distributing the paper",
      lines: [] as string[]
    };
  }

  const equalChapterSplit = isEqualWeightSet(plan.chapters.map((chapter) => chapter.weight));
  const customizedSubtopicCount = plan.mode === "chapter_subtopics"
    ? plan.chapters.filter((chapter) => !isEqualWeightSet(chapter.subtopics.map((subtopic) => subtopic.weight))).length
    : 0;

  return {
    title: equalChapterSplit && !customizedSubtopicCount
      ? plan.mode === "chapter_subtopics"
        ? "Equal chapter + subtopic split"
        : "Equal chapter split"
      : plan.mode === "chapter_subtopics"
        ? "Manual chapter + subtopic weightage"
        : "Manual chapter weightage",
    detail: `${chapters.length} chapter${chapters.length === 1 ? "" : "s"} selected${customizedSubtopicCount ? ` • ${customizedSubtopicCount} chapter${customizedSubtopicCount === 1 ? "" : "s"} with custom subtopics` : ""}`,
    lines: plan.chapters
      .filter((chapter) => chapter.weight > 0)
      .sort((left, right) => right.weight - left.weight)
      .slice(0, 4)
      .map((chapter) => `${chapter.chapterName} ${chapter.weight}%`)
  };
}

function summarizeChallengePlan(scope: DifficultyScope, overall: PaperLevel, plan: ChallengePlan) {
  if (scope === "overall") {
    return {
      title: `Overall ${paperLevelLabel(overall)}`,
      detail: "One difficulty level applies to every generated question"
    };
  }

  const chapterOverrides = plan.chapters.filter((chapter) => chapter.challenge !== "inherit").length;
  const subtopicOverrides = plan.chapters.reduce(
    (sum, chapter) => sum + chapter.subtopics.filter((subtopic) => subtopic.challenge !== "inherit").length,
    0
  );
  const overrideCount = chapterOverrides + subtopicOverrides;

  return {
    title: overrideCount ? "Granular overrides active" : "Granular inherits overall",
    detail: overrideCount
      ? `${chapterOverrides} chapter and ${subtopicOverrides} subtopic override${subtopicOverrides === 1 ? "" : "s"}`
      : `Unset rows use ${paperLevelLabel(overall)}`
  };
}

function resolveJobPaperLevel({
  scope,
  overall,
  plan,
  chapterName,
  subtopicName
}: {
  scope: DifficultyScope;
  overall: PaperLevel;
  plan: ChallengePlan;
  chapterName: string;
  subtopicName?: string | null;
}): PaperLevel {
  if (scope === "overall") return overall;
  const chapter = findChallengeChapter(plan, chapterName);
  const subtopic = subtopicName
    ? chapter?.subtopics.find((item) => item.name === subtopicName)
    : null;
  if (subtopic?.challenge && subtopic.challenge !== "inherit") return subtopic.challenge;
  if (chapter?.challenge && chapter.challenge !== "inherit") return chapter.challenge;
  return overall;
}

function paperLevelLabel(value: PaperLevel) {
  return paperLevelOptions.find((option) => option.value === value)?.label ?? formatTitleCase(value);
}

function isEqualWeightSet(weights: number[]) {
  if (weights.length <= 1) return true;
  return weights.every((weight) => weight === weights[0]);
}

function estimateCoverage(questionMix: Record<QuestionType, number>, chapters: Chapter[], coveragePlan: CoveragePlan) {
  const chapterCounts = Object.fromEntries(chapters.map((chapter) => [chapter.name, 0])) as Record<string, number>;
  const subtopicCounts = Object.fromEntries(
    chapters.map((chapter) => [
      chapter.name,
      Object.fromEntries(chapter.subtopics.map((subtopic) => [subtopic, 0]))
    ])
  ) as Record<string, Record<string, number>>;

  questionTypes
    .map((item) => ({ ...item, count: questionMix[item.type] ?? 0 }))
    .filter((item) => item.count > 0)
    .forEach((item) => {
      const jobs = buildGenerationJobs({
        count: item.count,
        item,
        chapters,
        coveragePlan
      });
      jobs.forEach((job) => {
        chapterCounts[job.allocation.chapter.name] = (chapterCounts[job.allocation.chapter.name] ?? 0) + job.allocation.count;
        if (job.subtopic) {
          subtopicCounts[job.allocation.chapter.name][job.subtopic] =
            (subtopicCounts[job.allocation.chapter.name][job.subtopic] ?? 0) + job.allocation.count;
        }
      });
    });

  return {
    totalQuestions: Object.values(chapterCounts).reduce((sum, count) => sum + count, 0),
    chapterCounts,
    subtopicCounts
  };
}

function buildGenerationJobs({
  count,
  item,
  chapters,
  coveragePlan
}: {
  count: number;
  item: { type: QuestionType; label: string; section: string; marks: number; count: number };
  chapters: Chapter[];
  coveragePlan: CoveragePlan;
}) {
  const eligibleChapters = chapters
    .filter((chapter) => chapter.question_types.includes(item.type))
    .map((chapter) => ({
      chapter,
      plan: findCoverageChapter(coveragePlan, chapter.name)
    }))
    .filter((entry): entry is { chapter: Chapter; plan: CoverageChapterWeight } => Boolean(entry.plan));

  return distributeByWeight(
    count,
    eligibleChapters.map((entry) => ({
      target: entry,
      weight: entry.plan.weight
    }))
  ).flatMap(({ target, count: chapterCount }, chapterIndex) => {
    if (coveragePlan.mode === "chapter_subtopics" && target.plan.subtopics.length) {
      return distributeByWeight(
        chapterCount,
        target.plan.subtopics.map((subtopic) => ({
          target: subtopic,
          weight: subtopic.weight
        }))
      ).flatMap(({ target: subtopic, count: subtopicCount }, subtopicIndex) =>
        splitGenerationCount(subtopicCount).map((batchCount, batchIndex) => ({
          id: `${item.type}-${target.chapter.number}-${chapterIndex}-${subtopicIndex}-${batchIndex}-${Math.random()}`,
          item,
          allocation: { chapter: target.chapter, count: batchCount },
          subtopic: subtopic.name
        }))
      );
    }

    return splitGenerationCount(chapterCount).map((batchCount, chunkIndex) => ({
      id: `${item.type}-${target.chapter.number}-${chapterIndex}-${chunkIndex}-${Math.random()}`,
      item,
      allocation: { chapter: target.chapter, count: batchCount },
      subtopic: null as string | null
    }));
  });
}

function chapterSelectionLabel(selected: string[]) {
  if (selected.length === 0) return "Select chapters";
  if (selected.length === 1) return selected[0];
  return `${selected.length} chapters selected`;
}

function subtopicSelectionLabel(selected: string[]) {
  if (selected.length === 0) return "All subtopics";
  if (selected.length === 1) return formatTitleCase(selected[0]);
  return `${selected.length} subtopics selected`;
}

function formatTitleCase(value: string) {
  return String(value ?? "")
    .split(" ")
    .filter(Boolean)
    .map((word) => {
      if (word === word.toUpperCase() && word.length > 1) return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}

function generateGenerationId(): string {
  const ts = Date.now().toString(36).toUpperCase().slice(-4);
  const rand = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `PAP-${ts}${rand}`;
}

function appendVersion(question: Question, label: string): QuestionVersion[] {
  return [
    ...(question.history ?? []),
    {
      id: crypto.randomUUID(),
      label,
      timestamp: new Date().toLocaleString(),
      question: { ...question, history: [] }
    }
  ];
}

function sectionFor(type: QuestionType) {
  return questionTypes.find((item) => item.type === type)?.section ?? "C";
}

function sectionTitle(section: string) {
  const titles: Record<string, string> = {
    A: "Objective questions",
    B: "Very short answer",
    C: "Short answer",
    D: "Long answer",
    E: "Case study"
  };
  return titles[section] ?? "Questions";
}

function labelFor(type: QuestionType) {
  return questionTypes.find((item) => item.type === type)?.label ?? type;
}
