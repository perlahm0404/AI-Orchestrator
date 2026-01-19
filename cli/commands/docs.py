"""
CLI commands for documentation management.

Usage:
    aibrain docs route <topic>              # Show where to create a document
    aibrain docs template new <type> <title>  # Create from template
    aibrain docs template list              # List available templates
    aibrain docs validate [path]            # Validate frontmatter & links

Examples:
    aibrain docs route "karematch login feature"
    aibrain docs template new adr "tiered-memory-system"
    aibrain docs template new plan "login-redesign-2026" --repo karematch
    aibrain docs validate
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Template locations
VAULT_PATH = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-ORCHESTRATOR"
TEMPLATES_PATH = VAULT_PATH / "12-DOCUMENTATION-ARCHITECTURE/templates"


def docs_route_command(args: Any) -> int:
    """Show where to create a document based on topic."""
    topic = args.topic.lower()

    print(f"\n{'='*70}")
    print(f"📍 DOCUMENTATION ROUTING GUIDE")
    print(f"{'='*70}")
    print(f"\nTopic: {args.topic}\n")

    # Routing logic based on keywords
    routes = []

    # ADR
    if any(word in topic for word in ['architecture', 'decision', 'adr', 'design pattern', 'tech choice']):
        routes.append({
            'type': 'ADR (Architectural Decision Record)',
            'location': f'{VAULT_PATH}/05-DECISIONS/',
            'template': 'adr-template.md',
            'naming': 'ADR-{NNN}-{kebab-case-title}.md',
            'reason': 'Strategic architectural decision'
        })

    # RIS
    if any(word in topic for word in ['incident', 'bug', 'resolution', 'ris', 'fix', 'issue']):
        routes.append({
            'type': 'RIS (Resolution/Incident System)',
            'location': '/Users/tmac/1_REPOS/MissionControl/ris/resolutions/',
            'template': 'ris-template.md',
            'naming': '{repo}-ris-{id}-{kebab-case-title}.md',
            'reason': 'Incident resolution or bug fix documentation'
        })

    # KareMatch planning
    if any(word in topic for word in ['karematch', 'km']):
        if any(word in topic for word in ['feature', 'plan', 'implement', 'build']):
            routes.append({
                'type': 'Planning Document',
                'location': '/Users/tmac/1_REPOS/karematch/docs/08-planning/active/',
                'template': 'planning-template.md',
                'naming': '{feature-name}.md or plan-{YYYYMMDD}-{id}-{title}.md',
                'reason': 'KareMatch-specific feature planning'
            })
        if 'prd' in topic or 'product' in topic or 'requirements' in topic:
            routes.append({
                'type': 'PRD (Product Requirements Document)',
                'location': '/Users/tmac/1_REPOS/karematch/docs/08-planning/prd/',
                'template': 'prd-template.md',
                'naming': 'prd-{feature-name}.md',
                'reason': 'Product requirements for KareMatch'
            })

    # CredentialMate planning
    if any(word in topic for word in ['credentialmate', 'cm', 'credential']):
        if any(word in topic for word in ['feature', 'plan', 'implement', 'build']):
            routes.append({
                'type': 'Planning Document',
                'location': '/Users/tmac/1_REPOS/credentialmate/docs/planning/active/',
                'template': 'planning-template.md',
                'naming': '{feature-name}.md',
                'reason': 'CredentialMate-specific feature planning'
            })

    # Cross-repo coordination
    if any(word in topic for word in ['cross-repo', 'multi-repo', 'coordination', 'all repos']):
        routes.append({
            'type': 'Cross-Repo Session',
            'location': '/Users/tmac/1_REPOS/AI_Orchestrator/sessions/cross-repo/active/',
            'template': 'session-template.md',
            'naming': '{YYYYMMDD-HHMM}-{kebab-case-topic}.md',
            'reason': 'Work spanning multiple repositories'
        })

    # Knowledge Object
    if any(word in topic for word in ['knowledge', 'ko', 'learning', 'pattern', 'troubleshoot']):
        routes.append({
            'type': 'Knowledge Object',
            'location': '/Users/tmac/1_REPOS/AI_Orchestrator/knowledge/{category}/',
            'template': 'ko-template.md',
            'naming': 'ko-{NNN}-{kebab-case-title}.md or {category}/{topic}.md',
            'reason': 'Institutional learning or troubleshooting pattern'
        })

    # Session documentation
    if any(word in topic for word in ['session', 'research', 'exploration', 'investigation']):
        routes.append({
            'type': 'Session Documentation',
            'location': '{repo}/docs/sessions/active/ or AI_Orchestrator/sessions/cross-repo/active/',
            'template': 'session-template.md',
            'naming': '{YYYYMMDD-HHMM}-{kebab-case-topic}.md',
            'reason': 'Multi-step work, research, or implementation session'
        })

    # Governance
    if any(word in topic for word in ['governance', 'policy', 'rule', 'constraint']):
        routes.append({
            'type': 'Governance Policy',
            'location': '/Users/tmac/1_REPOS/MissionControl/governance/policies/',
            'template': 'N/A (YAML files)',
            'naming': '{domain}-policy.yaml',
            'reason': 'Constitutional governance definition'
        })

    # Strategic planning
    if any(word in topic for word in ['strategic', 'roadmap', 'vision', 'long-term']):
        routes.append({
            'type': 'Strategic Plan',
            'location': f'{VAULT_PATH}/06-PLANS/',
            'template': 'planning-template.md',
            'naming': '{plan-name}.md',
            'reason': 'Long-term strategic planning'
        })

    # If no routes found, provide general guidance
    if not routes:
        print("🤔 No specific route detected. Here are general guidelines:\n")
        print("1. Strategic/Architectural → Knowledge Vault (05-DECISIONS/)")
        print("2. Feature Planning → App repo (karematch/docs/08-planning/)")
        print("3. Incident/Bug → MissionControl (ris/resolutions/)")
        print("4. Cross-repo work → AI_Orchestrator (sessions/cross-repo/)")
        print("5. Governance → MissionControl (governance/)")
        print(f"\nFor detailed routing, see:")
        print(f"  {VAULT_PATH}/12-DOCUMENTATION-ARCHITECTURE/content-routing-table.md")
        return 0

    # Display routes
    for i, route in enumerate(routes, 1):
        print(f"{'─'*70}")
        print(f"\n{i}. {route['type']}")
        print(f"\n   📁 Location:")
        print(f"      {route['location']}")
        print(f"\n   📄 Template:")
        print(f"      {route['template']}")
        print(f"\n   🏷️  File Naming:")
        print(f"      {route['naming']}")
        print(f"\n   💡 Reason:")
        print(f"      {route['reason']}\n")

    print(f"{'='*70}\n")

    if len(routes) > 1:
        print("💡 Multiple routes detected. Choose based on your primary intent.\n")

    # Show quick command
    if routes:
        first_route = routes[0]
        print("📝 Create from template:")
        template_type = first_route['template'].replace('-template.md', '')
        print(f"   aibrain docs template new {template_type} \"your-title-here\"\n")

    return 0


def docs_template_list_command(args: Any) -> int:
    """List available templates."""
    print(f"\n{'='*70}")
    print(f"📋 AVAILABLE TEMPLATES")
    print(f"{'='*70}\n")

    templates = [
        {
            'type': 'adr',
            'name': 'ADR (Architectural Decision Record)',
            'file': 'adr-template.md',
            'use_when': 'Making architectural decisions',
            'location': 'Knowledge Vault/05-DECISIONS/'
        },
        {
            'type': 'planning',
            'name': 'Planning Document',
            'file': 'planning-template.md',
            'use_when': 'Planning features or projects',
            'location': 'App repo docs/planning/'
        },
        {
            'type': 'prd',
            'name': 'PRD (Product Requirements Document)',
            'file': 'prd-template.md',
            'use_when': 'Writing product requirements',
            'location': 'App repo docs/planning/prd/'
        },
        {
            'type': 'ko',
            'name': 'Knowledge Object',
            'file': 'ko-template.md',
            'use_when': 'Capturing institutional learning',
            'location': 'AI_Orchestrator/knowledge/'
        },
        {
            'type': 'session',
            'name': 'Session Documentation',
            'file': 'session-template.md',
            'use_when': 'Documenting work sessions',
            'location': 'Repo sessions/active/'
        },
        {
            'type': 'ris',
            'name': 'RIS (Resolution/Incident System)',
            'file': 'ris-template.md',
            'use_when': 'Logging incidents or resolutions',
            'location': 'MissionControl/ris/resolutions/'
        }
    ]

    for tmpl in templates:
        print(f"Type: {tmpl['type']}")
        print(f"Name: {tmpl['name']}")
        print(f"Use When: {tmpl['use_when']}")
        print(f"Location: {tmpl['location']}")
        print(f"\nCreate with:")
        print(f"  aibrain docs template new {tmpl['type']} \"your-title\"\n")
        print(f"{'─'*70}\n")

    return 0


def docs_template_new_command(args: Any) -> int:
    """Create a new document from template."""
    template_type = args.template_type
    title = args.title

    # Map template types to files
    template_map = {
        'adr': 'adr-template.md',
        'planning': 'planning-template.md',
        'plan': 'planning-template.md',
        'prd': 'prd-template.md',
        'ko': 'ko-template.md',
        'session': 'session-template.md',
        'ris': 'ris-template.md'
    }

    if template_type not in template_map:
        print(f"\n❌ Unknown template type: {template_type}")
        print(f"\n   Available types: {', '.join(template_map.keys())}")
        print(f"\n   Run 'aibrain docs template list' to see all templates\n")
        return 1

    template_file = template_map[template_type]
    template_path = TEMPLATES_PATH / template_file

    if not template_path.exists():
        print(f"\n❌ Template not found: {template_path}")
        print(f"\n   Expected location:")
        print(f"   {TEMPLATES_PATH}/{template_file}\n")
        return 1

    # Read template
    template_content = template_path.read_text()

    # Generate values
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    timestamp_str = today.strftime("%Y%m%d-%H%M")
    kebab_title = title.lower().replace(' ', '-').replace('_', '-')
    kebab_title = re.sub(r'[^a-z0-9-]', '', kebab_title)

    # Determine output location and filename
    repo = getattr(args, 'repo', None)

    if template_type == 'adr':
        # Get next ADR number
        adr_dir = VAULT_PATH / "05-DECISIONS"
        existing_adrs = list(adr_dir.glob("ADR-*.md"))
        numbers = []
        for adr in existing_adrs:
            match = re.search(r'ADR-(\d+)', adr.name)
            if match:
                numbers.append(int(match.group(1)))
        next_num = max(numbers, default=0) + 1

        filename = f"ADR-{next_num:03d}-{kebab_title}.md"
        output_dir = adr_dir

    elif template_type in ['planning', 'plan']:
        if repo == 'karematch':
            output_dir = Path("/Users/tmac/1_REPOS/karematch/docs/08-planning/active")
        elif repo == 'credentialmate':
            output_dir = Path("/Users/tmac/1_REPOS/credentialmate/docs/planning/active")
        else:
            output_dir = VAULT_PATH / "06-PLANS"

        filename = f"{kebab_title}.md"

    elif template_type == 'prd':
        if repo == 'karematch':
            output_dir = Path("/Users/tmac/1_REPOS/karematch/docs/08-planning/prd")
        elif repo == 'credentialmate':
            output_dir = Path("/Users/tmac/1_REPOS/credentialmate/docs/planning/prd")
        else:
            output_dir = VAULT_PATH / "06-PLANS"

        filename = f"prd-{kebab_title}.md"

    elif template_type == 'ko':
        # Get next KO number
        ko_dir = Path("/Users/tmac/1_REPOS/AI_Orchestrator/knowledge")
        existing_kos = list(ko_dir.glob("**/ko-*.md"))
        numbers = []
        for ko in existing_kos:
            match = re.search(r'ko-(\d+)', ko.name)
            if match:
                numbers.append(int(match.group(1)))
        ko_next_num = max(numbers, default=0) + 1

        category = getattr(args, 'category', 'patterns')
        output_dir = ko_dir / category
        filename = f"ko-{ko_next_num:03d}-{kebab_title}.md"

    elif template_type == 'session':
        if repo == 'karematch':
            output_dir = Path("/Users/tmac/1_REPOS/karematch/docs/sessions/active")
        elif repo == 'credentialmate':
            output_dir = Path("/Users/tmac/1_REPOS/credentialmate/docs/sessions/active")
        else:
            output_dir = Path("/Users/tmac/1_REPOS/AI_Orchestrator/sessions/cross-repo/active")

        filename = f"{timestamp_str}-{kebab_title}.md"

    elif template_type == 'ris':
        output_dir = Path("/Users/tmac/1_REPOS/MissionControl/ris/resolutions")
        ris_repo = repo or 'ai-orchestrator'

        # Get next RIS ID for this repo
        existing_ris = list(output_dir.glob(f"{ris_repo}-ris-*.md"))
        numbers = []
        for ris in existing_ris:
            match = re.search(r'ris-(\d+)', ris.name)
            if match:
                numbers.append(int(match.group(1)))
        next_id = max(numbers, default=0) + 1

        filename = f"{ris_repo}-ris-{next_id:03d}-{kebab_title}.md"

    else:
        print(f"\n❌ Output location not defined for template type: {template_type}\n")
        return 1

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Replace placeholders
    content = template_content

    # Common replacements
    content = content.replace('{{Title}}', title)
    content = content.replace('{{title}}', title)
    content = content.replace('{{YYYY-MM-DD}}', date_str)
    content = content.replace('{{date}}', date_str)
    content = content.replace('{{YYYYMMDD-HHMM}}', timestamp_str)
    content = content.replace('{{kebab-case-title}}', kebab_title)
    content = content.replace('{{repo}}', repo or 'ai-orchestrator')

    # Type-specific replacements
    if template_type == 'adr':
        content = content.replace('{{NNN}}', f'{next_num:03d}')
    elif template_type == 'ko':
        content = content.replace('{{NNN}}', f'{ko_next_num:03d}')
        content = content.replace('{{category}}', getattr(args, 'category', 'patterns'))

    # Write file
    output_path.write_text(content)

    print(f"\n✅ Created: {output_path}\n")
    print(f"   Template: {template_file}")
    print(f"   Type: {template_type}")
    print(f"   Title: {title}\n")
    print(f"📝 Next steps:")
    print(f"   1. Replace remaining {{placeholders}} in the file")
    print(f"   2. Update YAML frontmatter tags")
    print(f"   3. Add [[backlinks]] to related documents\n")

    return 0


def docs_validate_command(args: Any) -> int:
    """Validate documentation frontmatter and links."""
    path = args.path

    print(f"\n{'='*70}")
    print(f"🔍 DOCUMENTATION VALIDATION")
    print(f"{'='*70}\n")

    if path:
        # Validate single file
        file_path = Path(path)
        if not file_path.exists():
            print(f"❌ File not found: {path}\n")
            return 1

        issues = validate_file(file_path)

        if not issues:
            print(f"✅ {file_path.name} - No issues found\n")
            return 0
        else:
            print(f"❌ {file_path.name} - {len(issues)} issues found:\n")
            for issue in issues:
                print(f"   • {issue}")
            print()
            return 1

    else:
        # Validate all markdown files in common locations
        print("Scanning documentation...\n")

        locations = [
            Path("/Users/tmac/1_REPOS/AI_Orchestrator/sessions"),
            Path("/Users/tmac/1_REPOS/karematch/docs"),
            Path("/Users/tmac/1_REPOS/credentialmate/docs"),
            VAULT_PATH / "05-DECISIONS",
            VAULT_PATH / "06-PLANS",
            VAULT_PATH / "07-SESSIONS",
        ]

        total_files = 0
        total_issues = 0

        for location in locations:
            if not location.exists():
                continue

            for md_file in location.rglob("*.md"):
                # Skip templates
                if 'template' in md_file.name.lower():
                    continue

                total_files += 1
                issues = validate_file(md_file)

                if issues:
                    total_issues += len(issues)
                    print(f"❌ {md_file.relative_to(location.parent)}")
                    for issue in issues:
                        print(f"   • {issue}")
                    print()

        print(f"{'='*70}")
        print(f"📊 SUMMARY")
        print(f"{'='*70}\n")
        print(f"Files scanned: {total_files}")
        print(f"Issues found: {total_issues}\n")

        if total_issues == 0:
            print("✅ All documentation validated successfully!\n")
            return 0
        else:
            print(f"⚠️  {total_issues} issues need attention\n")
            return 1


def validate_file(file_path: Path) -> List[str]:
    """Validate a single markdown file. Returns list of issues."""
    issues = []

    try:
        content = file_path.read_text()
    except Exception as e:
        return [f"Cannot read file: {e}"]

    # Check for YAML frontmatter
    if not content.startswith('---'):
        issues.append("Missing YAML frontmatter")
        return issues

    # Extract frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        issues.append("Malformed YAML frontmatter")
        return issues

    frontmatter = parts[1]
    body = parts[2]

    # Check required fields
    required_fields = ['tags', 'type', 'status', 'created']
    for field in required_fields:
        if f'{field}:' not in frontmatter:
            issues.append(f"Missing required field: {field}")

    # Check for tags
    if 'tags:' in frontmatter:
        # Check if tags list is empty
        if re.search(r'tags:\s*\[\s*\]', frontmatter):
            issues.append("Tags list is empty")

    # Check for broken backlinks (simple check)
    backlinks = re.findall(r'\[\[([^\]]+)\]\]', body)
    for link in backlinks:
        # Check if it looks like a valid reference
        if not link.strip():
            issues.append(f"Empty backlink found")

    # Check for unresolved placeholders
    placeholders = re.findall(r'\{\{([^}]+)\}\}', content)
    if placeholders:
        issues.append(f"Unresolved placeholders: {', '.join(set(placeholders))}")

    return issues


def setup_parser(subparsers: Any) -> None:
    """Setup the docs command parser."""
    docs_parser = subparsers.add_parser(
        'docs',
        help='Documentation management commands'
    )

    docs_subparsers = docs_parser.add_subparsers(
        dest='docs_command',
        help='Docs subcommand'
    )

    # docs route
    route_parser = docs_subparsers.add_parser(
        'route',
        help='Show where to create a document'
    )
    route_parser.add_argument('topic', help='Document topic or description')
    route_parser.set_defaults(func=docs_route_command)

    # docs template
    template_parser = docs_subparsers.add_parser(
        'template',
        help='Template management'
    )
    template_subparsers = template_parser.add_subparsers(
        dest='template_command',
        help='Template subcommand'
    )

    # docs template list
    list_parser = template_subparsers.add_parser(
        'list',
        help='List available templates'
    )
    list_parser.set_defaults(func=docs_template_list_command)

    # docs template new
    new_parser = template_subparsers.add_parser(
        'new',
        help='Create document from template'
    )
    new_parser.add_argument('template_type', help='Template type (adr, planning, prd, ko, session, ris)')
    new_parser.add_argument('title', help='Document title')
    new_parser.add_argument('--repo', help='Repository (karematch, credentialmate, ai-orchestrator)')
    new_parser.add_argument('--category', help='Category for KO (patterns, debugging, testing, etc.)')
    new_parser.set_defaults(func=docs_template_new_command)

    # docs validate
    validate_parser = docs_subparsers.add_parser(
        'validate',
        help='Validate documentation frontmatter and links'
    )
    validate_parser.add_argument('path', nargs='?', help='File or directory to validate (optional)')
    validate_parser.set_defaults(func=docs_validate_command)

    # Set default to show help if no subcommand
    docs_parser.set_defaults(func=lambda args: docs_parser.print_help())
