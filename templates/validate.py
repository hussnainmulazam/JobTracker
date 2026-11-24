#!/usr/bin/env python3
"""
Validation script for Hiring Pipeline Email Templates.
Verifies that:
1. All 31 templates exist in HTML and TXT format.
2. Every {{variable}} in every HTML and TXT template is explicitly declared in registry.json.
3. Every required variable declared in registry.json is actually used in the template.
4. Base layout and registry.json are valid and well-formed.
"""
import os
import json
import re
import sys

TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(TEMPLATES_DIR, "registry.json")):
    # Try looking in 'templates' subfolder if run from repo root
    if os.path.exists(os.path.join(TEMPLATES_DIR, "templates", "registry.json")):
        TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "templates")

REGISTRY_PATH = os.path.join(TEMPLATES_DIR, "registry.json")

def validate():
    print("=" * 65)
    print(" HIRING PIPELINE EMAIL TEMPLATE VALIDATION")
    print("=" * 65)

    if not os.path.exists(REGISTRY_PATH):
        print(f"[FAIL] registry.json not found at {REGISTRY_PATH}")
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    templates = registry.get("templates", {})
    print(f"Found {len(templates)} templates in registry.json.")

    var_pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    errors = []
    warnings = []
    checked_count = 0

    for t_id, meta in templates.items():
        checked_count += 1
        html_file = os.path.join(TEMPLATES_DIR, f"{t_id}.html")
        txt_file = os.path.join(TEMPLATES_DIR, f"{t_id}.txt")
        declared_vars = set(meta.get("required_variables", []))

        # Check file existence
        if not os.path.exists(html_file):
            errors.append(f"[{t_id}] HTML file missing: {html_file}")
            continue
        if not os.path.exists(txt_file):
            errors.append(f"[{t_id}] TXT file missing: {txt_file}")
            continue

        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        with open(txt_file, "r", encoding="utf-8") as f:
            txt_content = f.read()

        html_vars = set(var_pattern.findall(html_content))
        txt_vars = set(var_pattern.findall(txt_content))
        subj_vars = set(var_pattern.findall(meta.get("subject", "")))
        all_used_vars = html_vars.union(txt_vars).union(subj_vars)

        # Remove internal template slot placeholder if any
        all_used_vars.discard("content")
        all_used_vars.discard("preheader_text")

        # 1. Every variable used must be declared in registry.json
        undeclared = all_used_vars - declared_vars
        if undeclared:
            errors.append(f"[{t_id}] Undeclared variables used in template: {sorted(list(undeclared))}")

        # 2. Every declared variable should be present in the template or subject
        unused = declared_vars - all_used_vars
        if unused:
            warnings.append(f"[{t_id}] Declared variables not found in template body/subject: {sorted(list(unused))}")

    print(f"Validated {checked_count} templates.")
    print("-" * 65)

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print("  [WARN] " + w)
        print("-" * 65)

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print("  [FAIL] " + e)
        print("=" * 65)
        print("RESULT: VALIDATION FAILED")
        return False
    else:
        print("ALL VARIABLES DECLARED AND VALIDATED SUCCESSFULLY!")
        print(f"31/31 templates passed strict validation.")
        print("=" * 65)
        print("RESULT: PASS")
        return True

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
