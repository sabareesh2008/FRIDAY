"""Programming language metadata, syntax, extensions, and execution commands."""
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

@dataclass
class LanguageSpec:
    name: str
    extension: str
    default_filename: str
    comment_single: str
    comment_start: str
    comment_end: str
    compile_cmd: Optional[str]
    run_cmd: str
    aliases: Set[str]

LANGUAGES: Dict[str, LanguageSpec] = {
    "java": LanguageSpec(
        name="Java",
        extension=".java",
        default_filename="Solution.java",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd="javac {file}",
        run_cmd="java {stem}",
        aliases={"java", "jdk", "jvm"}
    ),
    "python": LanguageSpec(
        name="Python",
        extension=".py",
        default_filename="solution.py",
        comment_single="#",
        comment_start='"""',
        comment_end='"""',
        compile_cmd=None,
        run_cmd="python {file}",
        aliases={"python", "py", "python3"}
    ),
    "cpp": LanguageSpec(
        name="C++",
        extension=".cpp",
        default_filename="solution.cpp",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd="g++ -O2 {file} -o {stem}.exe",
        run_cmd="{stem}.exe",
        aliases={"cpp", "c++", "cplusplus"}
    ),
    "c": LanguageSpec(
        name="C",
        extension=".c",
        default_filename="solution.c",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd="gcc -O2 {file} -o {stem}.exe",
        run_cmd="{stem}.exe",
        aliases={"c", "clang"}
    ),
    "javascript": LanguageSpec(
        name="JavaScript",
        extension=".js",
        default_filename="solution.js",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd=None,
        run_cmd="node {file}",
        aliases={"javascript", "js", "node", "nodejs"}
    ),
    "typescript": LanguageSpec(
        name="TypeScript",
        extension=".ts",
        default_filename="solution.ts",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd="npx tsc {file}",
        run_cmd="node {stem}.js",
        aliases={"typescript", "ts"}
    ),
    "go": LanguageSpec(
        name="Go",
        extension=".go",
        default_filename="main.go",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd=None,
        run_cmd="go run {file}",
        aliases={"go", "golang"}
    ),
    "rust": LanguageSpec(
        name="Rust",
        extension=".rs",
        default_filename="main.rs",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd="rustc {file}",
        run_cmd="{stem}.exe",
        aliases={"rust", "rs"}
    ),
    "csharp": LanguageSpec(
        name="C#",
        extension=".cs",
        default_filename="Program.cs",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd="csc {file}",
        run_cmd="{stem}.exe",
        aliases={"c#", "csharp", "cs", "dotnet"}
    ),
    "html": LanguageSpec(
        name="HTML",
        extension=".html",
        default_filename="index.html",
        comment_single="<!--",
        comment_start="<!--",
        comment_end="-->",
        compile_cmd=None,
        run_cmd="start {file}",
        aliases={"html", "html5", "webpage"}
    ),
    "sql": LanguageSpec(
        name="SQL",
        extension=".sql",
        default_filename="query.sql",
        comment_single="--",
        comment_start="/*",
        comment_end="*/",
        compile_cmd=None,
        run_cmd="",
        aliases={"sql", "mysql", "postgresql", "sqlite"}
    ),
    "kotlin": LanguageSpec(
        name="Kotlin",
        extension=".kt",
        default_filename="Solution.kt",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd="kotlinc {file} -include-runtime -d {stem}.jar",
        run_cmd="java -jar {stem}.jar",
        aliases={"kotlin", "kt"}
    ),
    "php": LanguageSpec(
        name="PHP",
        extension=".php",
        default_filename="index.php",
        comment_single="//",
        comment_start="/*",
        comment_end="*/",
        compile_cmd=None,
        run_cmd="php {file}",
        aliases={"php"}
    ),
    "ruby": LanguageSpec(
        name="Ruby",
        extension=".rb",
        default_filename="solution.rb",
        comment_single="#",
        comment_start="=begin",
        comment_end="=end",
        compile_cmd=None,
        run_cmd="ruby {file}",
        aliases={"ruby", "rb"}
    ),
}

def detect_language(query: str) -> Optional[LanguageSpec]:
    """Detects programming language from text, file extension, or keywords."""
    q = query.lower()
    
    # Check by extension in query (e.g., .java, .py)
    for lang in LANGUAGES.values():
        if f"{lang.extension} " in q or q.endswith(lang.extension):
            return lang

    # Check words
    words = set(re.findall(r"[a-z0-9#+]+", q))
    for key, lang in LANGUAGES.items():
        if words & lang.aliases:
            return lang

    return None

def normalize_filename(name: str, lang: LanguageSpec) -> str:
    """Ensures file name has the right extension for the language."""
    clean = name.strip().strip('"\'')
    if not clean:
        return lang.default_filename
    if not clean.lower().endswith(lang.extension):
        clean = clean + lang.extension
    return clean
