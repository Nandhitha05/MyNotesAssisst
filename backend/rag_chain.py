import os
import re

from web_search import web_search_docs


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
            temperature=0.3,
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )


# Mode rules describe HOW to format the answer; the wrapper prompt sets WHERE
# the answer must come from (PDF / web / general knowledge).
MODE_RULES = {
    "1mark": """Answer in 1-MARK style.

- If options are present (a/b/c/d, 1/2/3/4), pick the correct one.
- Otherwise: one or two precise sentences.
- ALWAYS include a one-line justification.

Format:
Answer: <answer or chosen option>
Justification: <one-line reason>
""",

    "2marks": """Answer in 2-MARKS style. Be substantive — at least 5-7 lines of actual content.

Required sections (use these exact headings):

**Definition**
1-2 crisp sentences defining the concept.

**Explanation**
3-4 sentences expanding on it. Use simple language.

**Example**
A concrete example. If the topic is programming-related, include a short fenced code block (```language ... ```).

**Applications**
2-3 bullet points of real-world uses.

**Advantages & Disadvantages**
- Advantage: <one line>
- Advantage: <one line>
- Disadvantage: <one line>
""",

    "long": """Answer in LONG-ANSWER (essay) style. Aim for 800-1200 words. Be thorough.

Use this structure:

# <Topic>

## Introduction
3-5 sentences setting up the topic and why it matters.

## Key Concepts
Use ### sub-headings for each major concept. Define terms in **bold**.

## Working / Process
Step-by-step explanation. Include a textual flow chart, e.g.
`Input -> Preprocessing -> Model -> Post-processing -> Output`

## Code Example
If the topic is programming, algorithms, or anything where code clarifies the idea, include a fenced code block in the appropriate language.

## Real-world Applications
4-6 bullet points of where this is used in practice.

## Advantages
4-5 bullet points.

## Disadvantages / Limitations
3-4 bullet points.

## Comparison (if relevant)
A small markdown table comparing this with related concepts.

## Conclusion
3-4 sentences wrapping up.
""",

    "seminar": """Prepare a complete SEMINAR plan. Be detailed.

1. **Title**
2. **Abstract** (4-5 lines)
3. **Learning Objectives** (5-6 bullets)
4. **Detailed Content** — multiple sections with sub-sections; include textual flow charts (`A -> B -> C`) and fenced code blocks where useful
5. **Real-world Examples / Case Studies** (at least 3)
6. **Diagrams** (described textually; e.g. "Block diagram: User -> Frontend -> API -> DB")
7. **Advantages & Limitations**
8. **Conclusion**
9. **References** (cite sources used)
10. **Anticipated Q&A** (5 likely audience questions with full answers)
""",

    "presentation": """Prepare a PRESENTATION (slide-deck outline).

Slide 1 - Title
- Title
- Subtitle / presenter line

Slide 2 - Agenda
- 5-6 bullets

Slide 3..N - Content slides (one per major idea)
- Slide title
- 4-5 concise bullets
- Speaker notes: 2-3 sentences

Required slides: Introduction, Key Concepts, Working / Process (with textual flow), Code Example (if applicable), Examples, Advantages, Limitations, Conclusion, References, Thank You / Q&A.
""",

    "auto": """Answer the user's question well.

- Be clear and complete. Match depth to the question — short questions get short answers, "explain" / "how does X work" questions get longer structured answers.
- Use sub-headings, bullets, and **bold** for key terms.
- If the topic is programming-related, include a fenced code block.
- For processes, include a textual flow chart: `A -> B -> C`.
- Include at least one concrete example and one real-world application.
""",
}


PDF_HEADER = """You are MyNotesAssist, a study assistant. Answer using ONLY the PDF context provided below.

If the answer is genuinely not present in the context, reply with EXACTLY this single line and nothing else:
NOT_IN_PDF

(The system will then search trusted study sites for you.)
"""

WEB_HEADER = """You are MyNotesAssist, a study assistant. The user's PDF didn't cover this topic, so here is content fetched from trusted study sites (GeeksforGeeks, JavaTPoint, TutorialsPoint, Programiz, Wikipedia, W3Schools, Scaler).

Answer using ONLY these web sources. Be thorough and student-friendly. Cite the source titles inline where helpful, e.g. "(GeeksforGeeks)".
"""

GENERAL_HEADER = """You are MyNotesAssist, a friendly study companion.

The user's PDFs and trusted study sites didn't directly cover this question, so answer from your own general knowledge.

- If it's an academic/technical question, follow the requested format thoroughly (definition, example, applications, code, etc.).
- If it's a casual or conversational question (small talk, opinions, jokes, life advice, "how are you"), reply warmly in 1-3 natural sentences — skip the formal sections.
- Be accurate. If you genuinely don't know, say so.
"""


# Patterns the LLM uses to signal "I don't have this in the PDF".
NOT_AVAILABLE_PATTERNS = [
    r"^\s*NOT_IN_PDF\s*$",
    r"this information is not available in the uploaded documents",
    r"not (?:found|present|available) in the (?:provided )?context",
    r"the (?:provided )?context does not (?:contain|mention|cover|include)",
    r"the (?:given )?(?:document|pdf)s? (?:do(?:es)? not|don'?t) (?:contain|mention|cover|include)",
]


def _is_not_available(text: str) -> bool:
    if not text:
        return True
    t = text.strip().lower()
    for p in NOT_AVAILABLE_PATTERNS:
        if re.search(p, t):
            return True
    return False


def _content_to_text(content) -> str:
    """Coerce LangChain message content (str | list[parts]) into a clean string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict):
                if p.get("type") == "text" and "text" in p:
                    parts.append(p["text"])
                elif "text" in p:
                    parts.append(p["text"])
        return "\n".join(s for s in parts if s).strip()
    return str(content)


def detect_mode(query: str) -> str:
    q = query.lower()
    if re.search(r"\b1\s*mark\b|\bone\s*mark\b", q):
        return "1mark"
    if re.search(r"\b2\s*marks?\b|\btwo\s*marks?\b", q):
        return "2marks"
    if re.search(r"\blong\s*answer\b|\b(5|10|15|16)\s*marks?\b|\bessay\b|\bdetailed\b|\belaborate\b|\bexplain in detail\b", q):
        return "long"
    if "seminar" in q:
        return "seminar"
    if "presentation" in q or "ppt" in q or "slide" in q:
        return "presentation"
    return "auto"


GREETING_PATTERNS = [
    r"^\s*(hi+|hello+|hey+|yo|hola|namaste|namaskar|vanakkam)[\s!.,]*$",
    r"^\s*good\s+(morning|afternoon|evening|night)[\s!.,]*$",
    r"^\s*(thanks|thank\s*you|thx|ty|tysm|thankyou)[\s!.,]*$",
    r"^\s*(bye|goodbye|see\s*you|cya|gn)[\s!.,]*$",
    r"^\s*(ok|okay|okk+|cool|nice|great|awesome|got\s*it|fine)[\s!.,]*$",
]

META_PATTERNS = [
    r"who\s+are\s+you",
    r"what\s+(can|do)\s+you\s+(do|help|offer)",
    r"what.?s\s+your\s+name",
    r"how\s+are\s+you",
    r"\bhelp\b",
    r"how\s+(do|to|can)\s+(i|you)\s+use",
    r"how\s+does\s+this\s+work",
]


def detect_chat(query: str) -> bool:
    q = query.lower().strip()
    if not q:
        return False
    if len(q.split()) <= 4:
        for p in GREETING_PATTERNS:
            if re.match(p, q):
                return True
    for p in META_PATTERNS:
        if re.search(p, q):
            return True
    return False


CHAT_PROMPT = """You are MyNotesAssist — a warm, friendly study companion for college students.

The user said something conversational (a greeting, thanks, goodbye, or a meta question about you).
Reply briefly and naturally in 1-3 sentences. Be human, never robotic.

If the moment fits, casually mention what you can do:
- Answer questions from PDFs they upload (1 mark, 2 marks, long answer, seminar, presentation)
- Fall back to trusted study sites (GeeksforGeeks, JavaTPoint, Wikipedia...) if the PDF doesn't cover it
- Generate summaries, structured notes, and quizzes from any uploaded document
- Just chat normally if they want — you don't only answer from documents
"""


class RAGChain:
    def __init__(self, vector_store):
        self.vs = vector_store
        self.llm = get_llm()

    @staticmethod
    def _build_context(docs):
        parts = []
        for d in docs:
            if d.metadata.get("page") == "web":
                title = d.metadata.get("title") or d.metadata.get("source", "web")
                url = d.metadata.get("source", "")
                label = f"[Web source: {title} | URL: {url}]"
            else:
                src = d.metadata.get("source", "unknown")
                page = d.metadata.get("page", "?")
                label = f"[Source: {src} | Page: {page}]"
            parts.append(f"{label}\n{d.page_content}")
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _sources(docs):
        seen = []
        for d in docs:
            if d.metadata.get("page") == "web":
                entry = {
                    "file": d.metadata.get("title") or d.metadata.get("host", "web"),
                    "url": d.metadata.get("source"),
                    "kind": "web",
                }
            else:
                entry = {
                    "file": d.metadata.get("source", "unknown"),
                    "page": d.metadata.get("page", "?"),
                    "kind": "pdf",
                }
            if entry not in seen:
                seen.append(entry)
        return seen

    def _invoke(self, prompt: str) -> str:
        resp = self.llm.invoke(prompt)
        content = getattr(resp, "content", resp)
        return _content_to_text(content)

    def _build_prompt(self, mode, source_kind, context, query):
        if source_kind == "pdf":
            header = PDF_HEADER
        elif source_kind == "web":
            header = WEB_HEADER
        else:
            header = GENERAL_HEADER
        rules = MODE_RULES.get(mode, MODE_RULES["auto"])
        ctx = f"=== CONTEXT ===\n{context}\n\n" if context else ""
        return (
            f"{header}\n\n"
            f"=== ANSWER FORMAT ===\n{rules}\n\n"
            f"{ctx}"
            f"=== QUESTION ===\n{query}\n"
        )

    def answer(self, query: str, mode: str = "auto") -> dict:
        if mode == "auto" and detect_chat(query):
            try:
                text = self._invoke(CHAT_PROMPT + "\n\nUser: " + query)
            except Exception:
                text = "Hi! I'm MyNotesAssist. Upload a PDF and ask away — or just chat with me. I'll check trusted study sites if your notes don't cover something."
            return {"answer": text, "sources": [], "mode": "chat", "source_kind": "chat"}

        if mode == "auto":
            mode = detect_mode(query)

        k = 10 if mode in ("seminar", "presentation", "long") else 6
        docs = self.vs.similarity_search(query, k=k)

        if docs:
            context = self._build_context(docs)
            prompt = self._build_prompt(mode, "pdf", context, query)
            text = self._invoke(prompt)
            if not _is_not_available(text):
                return {
                    "answer": text,
                    "sources": self._sources(docs),
                    "mode": mode,
                    "source_kind": "pdf",
                }

        web_docs = web_search_docs(query)
        if web_docs:
            context = self._build_context(web_docs)
            prompt = self._build_prompt(mode, "web", context, query)
            text = self._invoke(prompt)
            return {
                "answer": text,
                "sources": self._sources(web_docs),
                "mode": mode,
                "source_kind": "web",
            }

        # Final layer: answer from general knowledge so the assistant never refuses.
        prompt = self._build_prompt(mode, "general", "", query)
        text = self._invoke(prompt)
        return {
            "answer": text,
            "sources": [],
            "mode": mode,
            "source_kind": "general",
        }

    def summarize(self, filename: str) -> dict:
        docs = self.vs.get_document_chunks(filename)
        if not docs:
            return {"answer": f"No content found for {filename}.", "sources": []}
        docs = docs[:40]
        context = "\n\n".join(d.page_content for d in docs)
        prompt = (
            "Summarise the following document concisely.\n"
            "Include:\n"
            "- A 3-4 line abstract\n"
            "- Key bullet points\n"
            "- Main takeaways\n\n"
            f"Document content:\n{context}"
        )
        return {
            "answer": self._invoke(prompt),
            "sources": [{"file": filename, "page": "all", "kind": "pdf"}],
            "mode": "summary",
        }

    def generate_notes(self, filename: str) -> dict:
        docs = self.vs.get_document_chunks(filename)
        if not docs:
            return {"answer": f"No content found for {filename}.", "sources": []}
        docs = docs[:40]
        context = "\n\n".join(d.page_content for d in docs)
        prompt = (
            "Generate clean, well-structured study notes from the following content.\n\n"
            "Use:\n"
            "- Clear headings and sub-headings (markdown)\n"
            "- Bullet points\n"
            "- Definitions in **bold**\n"
            "- Fenced code blocks where the topic is programming-related\n"
            "- Examples wherever helpful\n"
            "- A short summary at the end\n\n"
            f"Content:\n{context}"
        )
        return {
            "answer": self._invoke(prompt),
            "sources": [{"file": filename, "page": "all", "kind": "pdf"}],
            "mode": "notes",
        }

    def generate_quiz(self, filename: str) -> dict:
        docs = self.vs.get_document_chunks(filename)
        if not docs:
            return {"answer": f"No content found for {filename}.", "sources": []}
        docs = docs[:30]
        context = "\n\n".join(d.page_content for d in docs)
        prompt = (
            "Create a quiz from the following content.\n"
            "Include:\n"
            "- 5 multiple-choice questions (4 options each, mark the correct one)\n"
            "- 3 short-answer questions with model answers\n"
            "- 1 long-answer question with an outline answer\n\n"
            f"Content:\n{context}"
        )
        return {
            "answer": self._invoke(prompt),
            "sources": [{"file": filename, "page": "all", "kind": "pdf"}],
            "mode": "quiz",
        }
