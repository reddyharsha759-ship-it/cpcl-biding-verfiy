"""
Rulebook Loader & Document Ingestion Engine
Supports structured JSON rule sets, Markdown policies, and PDF regulatory documents.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Optional

from app.models.rule_schemas import RuleBook, RuleClause, RuleCondition, RuleSeverity


DEFAULT_RULES_DIR = Path(__file__).parent / "default_rules"


class RulebookLoader:
    """Loads, parses, and converts statutory rulebooks into standardized RuleClause objects."""

    @classmethod
    def load_default_rulebooks(cls) -> List[RuleBook]:
        """Loads all default statutory rulebooks from the default_rules directory."""
        rulebooks: List[RuleBook] = []
        if not DEFAULT_RULES_DIR.exists():
            return rulebooks

        for file_path in DEFAULT_RULES_DIR.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rb = cls.parse_dict(data)
                    rulebooks.append(rb)
            except Exception as e:
                print(f"Error loading rulebook {file_path}: {e}")

        return rulebooks

    @classmethod
    def parse_dict(cls, data: dict) -> RuleBook:
        """Parses a dictionary into a validated RuleBook instance."""
        clauses_data = data.get("clauses", [])
        parsed_clauses: List[RuleClause] = []

        rb_id = data.get("id", "CUSTOM_RB")
        rb_title = data.get("title", "Statutory Rulebook")

        for c in clauses_data:
            c["rulebook_id"] = c.get("rulebook_id", rb_id)
            c["rulebook_title"] = c.get("rulebook_title", rb_title)
            parsed_clauses.append(RuleClause(**c))

        return RuleBook(
            id=rb_id,
            title=rb_title,
            authority=data.get("authority", "Government of India"),
            version=data.get("version", "1.0"),
            category=data.get("category", "General"),
            summary=data.get("summary", ""),
            effective_date=data.get("effective_date", "2020-01-01"),
            clauses=parsed_clauses,
            total_clauses=len(parsed_clauses),
        )

    @classmethod
    def parse_markdown_policy(cls, text: str, rulebook_id: str, title: str, authority: str) -> RuleBook:
        """
        Parses Markdown procurement text with standard header sections (### Rule / ### Clause)
        into structured clauses.
        """
        sections = re.split(r"(?=^\s*###?\s+)", text, flags=re.MULTILINE)
        clauses: List[RuleClause] = []

        for idx, sec in enumerate(sections):
            sec = sec.strip()
            if not sec:
                continue

            lines = sec.split("\n")
            header = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:]).strip()

            if not body:
                continue

            clause_num = f"Clause {idx + 1}"
            match = re.search(r"(Rule\s+[\w\(\)]+|Clause\s+[\w\(\)\.]+)", header, re.IGNORECASE)
            if match:
                clause_num = match.group(1)

            clause_id = f"{rulebook_id}_C{idx + 1}"
            clauses.append(
                RuleClause(
                    id=clause_id,
                    rulebook_id=rulebook_id,
                    rulebook_title=title,
                    clause_number=clause_num,
                    title=header,
                    category="Policy Guideline",
                    legal_text=body,
                    severity=RuleSeverity.MANDATORY,
                    keywords=[w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", header + " " + body)[:10]],
                )
            )

        return RuleBook(
            id=rulebook_id,
            title=title,
            authority=authority,
            version="1.0",
            category="Custom Ingested Policy",
            summary=f"Parsed from Markdown source containing {len(clauses)} clauses.",
            clauses=clauses,
            total_clauses=len(clauses),
        )
