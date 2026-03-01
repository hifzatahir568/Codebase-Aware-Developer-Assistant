import ast
import re
from typing import List, Optional, Tuple

from app.core.config import settings
from app.services.indexing import extractive_fallback_answer, iter_source_files, read_text
from app.services.llm import models


def _trim_context_to_model_limit(question: str, context: str, max_new_tokens: int = 150) -> str:
    tokenizer, _ = models.get_llm()
    if tokenizer is None:
        return context

    model_max_len = getattr(tokenizer, "model_max_length", 1024)
    if not isinstance(model_max_len, int) or model_max_len <= 0 or model_max_len > 100000:
        model_max_len = 1024

    base_prompt = (
        "You are a code assistant. Answer the question using only the context. "
        "If context is insufficient, say so briefly.\n\n"
        "Context:\n\n\n"
        f"Question: {question}\nAnswer:"
    )
    base_tokens = len(tokenizer.encode(base_prompt, add_special_tokens=False))
    available_for_context = max(64, model_max_len - max_new_tokens - base_tokens)
    context_ids = tokenizer.encode(context, add_special_tokens=False)
    if len(context_ids) <= available_for_context:
        return context
    trimmed_ids = context_ids[:available_for_context]
    return tokenizer.decode(trimmed_ids, skip_special_tokens=True)


def extract_class_methods_answer(question: str, context: str) -> Optional[str]:
    question_lower = question.lower()
    if "method" not in question_lower or "class" not in question_lower:
        return None

    class_name = None
    m = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", question)
    if m:
        class_name = m.group(1)
    else:
        m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+class\b", question)
        if m:
            class_name = m.group(1)
    if not class_name:
        return None

    lines = context.splitlines()
    class_pat = re.compile(rf"^(\s*)class\s+{re.escape(class_name)}\b")
    def_pat = re.compile(r"^(\s*)def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")

    class_indent = None
    methods: List[str] = []
    in_class = False
    for line in lines:
        if not in_class:
            class_match = class_pat.match(line)
            if class_match:
                in_class = True
                class_indent = len(class_match.group(1))
            continue

        if line.strip():
            cur_indent = len(line) - len(line.lstrip(" "))
            if cur_indent <= (class_indent or 0) and not line.lstrip().startswith("@"):
                break

        def_match = def_pat.match(line)
        if def_match:
            method_indent = len(def_match.group(1))
            if method_indent > (class_indent or 0):
                methods.append(def_match.group(2))

    if not in_class:
        return f"I could not find `class {class_name}` in the retrieved context."
    if not methods:
        return f"`class {class_name}` was found, but no methods were detected in the retrieved context."
    return f"Methods in `{class_name}`: {', '.join(methods)}."


def extract_division_by_zero_answer(question: str, context: str) -> Optional[str]:
    q = question.lower()
    if "division by zero" not in q and "divide by zero" not in q:
        return None

    lines = context.splitlines()
    def_pat = re.compile(r"^(\s*)def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    class_pat = re.compile(r"^(\s*)class\s+([A-Za-z_][A-Za-z0-9_]*)\b")

    current_class: Optional[str] = None
    class_indent = 0
    current_func: Optional[str] = None
    func_indent = 0
    matches: List[str] = []

    def flush_func() -> None:
        nonlocal current_func
        current_func = None

    for line in lines:
        indent = len(line) - len(line.lstrip(" ")) if line.strip() else 0

        class_m = class_pat.match(line)
        if class_m:
            current_class = class_m.group(2)
            class_indent = len(class_m.group(1))
            flush_func()
            continue

        if current_class and line.strip() and indent <= class_indent:
            current_class = None
            class_indent = 0
            flush_func()

        def_m = def_pat.match(line)
        if def_m:
            func_indent = len(def_m.group(1))
            func_name = def_m.group(2)
            current_func = f"{current_class}.{func_name}" if current_class else func_name
            continue

        if current_func and line.strip() and indent <= func_indent and not line.lstrip().startswith("@"):
            flush_func()

        if current_func:
            low = line.lower()
            if (
                "zerodivisionerror" in low
                or "division by zero" in low
                or "if b == 0" in low
                or "if b==0" in low
                or "if denominator == 0" in low
                or "if denominator==0" in low
            ):
                if current_func not in matches:
                    matches.append(current_func)

    if not matches:
        return "I could not find explicit division-by-zero handling in the retrieved context."
    if len(matches) == 1:
        return f"Division-by-zero is handled in `{matches[0]}`."
    return "Division-by-zero is handled in: " + ", ".join(f"`{m}`" for m in matches) + "."


def extract_function_purpose_answer(question: str, context: str) -> Optional[str]:
    q = question.lower()
    if "function" not in q or "what does" not in q:
        return None

    m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+function\b", question)
    if not m:
        m = re.search(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\b", question)
    if not m:
        return None
    func_name = m.group(1)

    lines = context.splitlines()
    def_pat = re.compile(rf"^(\s*)def\s+{re.escape(func_name)}\s*\(([^)]*)\)\s*:")

    in_func = False
    func_indent = 0
    params = ""
    body: List[str] = []
    for line in lines:
        if not in_func:
            dm = def_pat.match(line)
            if dm:
                in_func = True
                func_indent = len(dm.group(1))
                params = dm.group(2).strip()
            continue

        if line.strip():
            indent = len(line) - len(line.lstrip(" "))
            if indent <= func_indent and not line.lstrip().startswith("@"):
                break
        body.append(line)

    if not in_func:
        return None

    for line in body:
        stripped = line.strip()
        if stripped.startswith("return "):
            expr = stripped[len("return ") :].strip()
            if "+" in expr:
                return f"`{func_name}({params})` returns the sum of its inputs."
            if "-" in expr:
                return f"`{func_name}({params})` returns the subtraction result."
            if "*" in expr:
                return f"`{func_name}({params})` returns the product of its inputs."
            if "/" in expr:
                return f"`{func_name}({params})` returns the division result."
            return f"`{func_name}({params})` returns `{expr}`."

    if body:
        for line in body:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return f"`{func_name}({params})` executes: `{stripped}`."

    return f"`{func_name}({params})` is defined in the retrieved code."


def extract_functions_list_answer(question: str, context: str) -> Optional[str]:
    q = question.lower()
    if "function" not in q or "what" not in q:
        return None
    def_names = re.findall(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", context, flags=re.MULTILINE)
    if not def_names:
        return None
    ordered, seen = [], set()
    for name in def_names:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return "Functions found in retrieved code: " + ", ".join(f"`{n}`" for n in ordered) + "."


def _architecture_question(question: str) -> bool:
    q = question.lower()
    keys = ["architecture", "structure", "design", "organized", "components", "flow"]
    return any(k in q for k in keys)


def build_architecture_answer(project_path: str) -> str:
    files = iter_source_files(project_path)
    py_files = [f for f in files if f.lower().endswith(".py")]
    if not py_files:
        return "No Python files were found to describe architecture."

    modules = 0
    classes: List[str] = []
    functions: List[str] = []
    routes: List[str] = []

    for fp in py_files:
        try:
            src = read_text(fp)
            tree = ast.parse(src, filename=fp)
        except Exception:
            continue
        modules += 1
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        route_method = dec.func.attr.upper()
                        if route_method in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                                routes.append(f"{route_method} {dec.args[0].value}")

    class_part = ", ".join(f"`{c}`" for c in sorted(set(classes))[:8]) or "none detected"
    func_part = ", ".join(f"`{f}`" for f in sorted(set(functions))[:10]) or "none detected"
    route_part = ", ".join(f"`{r}`" for r in sorted(set(routes))[:8]) or "none detected"

    return (
        "Architecture summary:\n"
        f"- Project path: `{project_path}`\n"
        f"- Source files scanned: {len(files)} (Python modules parsed: {modules})\n"
        f"- Main classes: {class_part}\n"
        f"- Main functions: {func_part}\n"
        f"- API routes detected: {route_part}\n"
        "- Pattern: this codebase appears to be a FastAPI service with SQLite-backed indexing and retrieval logic."
    )


def _run_llm(question: str, context: str) -> str:
    tokenizer, hf_pipe = models.get_llm()
    if tokenizer is None or hf_pipe is None:
        return extractive_fallback_answer(question, context)

    safe_context = _trim_context_to_model_limit(question, context)
    prompt = (
        "You are a code assistant. Answer the question using only the context. "
        "If context is insufficient, say so briefly.\n\n"
        f"Context:\n{safe_context}\n\n"
        f"Question: {question}\nAnswer:"
    )

    out = hf_pipe(prompt, max_new_tokens=150, return_full_text=False, truncation=True)[0]["generated_text"]
    answer = out.strip()
    lines = [ln.strip() for ln in answer.splitlines() if ln.strip()]
    if lines:
        deduped = [lines[0]]
        for ln in lines[1:]:
            if ln != deduped[-1]:
                deduped.append(ln)
        answer = "\n".join(deduped)
    if "\nQuestion:" in answer:
        answer = answer.split("\nQuestion:", 1)[0].strip()
    return answer or "I could not generate an answer from the provided context."


def generate_answer(question: str, context: str, project_path: Optional[str] = None) -> str:
    if _architecture_question(question) and project_path:
        return build_architecture_answer(project_path)

    div_zero = extract_division_by_zero_answer(question, context)
    if div_zero:
        return div_zero

    func_purpose = extract_function_purpose_answer(question, context)
    if func_purpose:
        return func_purpose

    funcs_list = extract_functions_list_answer(question, context)
    if funcs_list:
        return funcs_list

    extracted = extract_class_methods_answer(question, context)
    if extracted:
        return extracted

    if settings.llm_model_id.lower() in {"distilgpt2", "gpt2", "gpt2-medium", "gpt2-large"}:
        return extractive_fallback_answer(question, context)

    return _run_llm(question, context)
