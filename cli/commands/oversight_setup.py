from typing import Any

"""Setup function for oversight command (argparse integration)."""

def setup_parser(subparsers: Any) -> None:
    """Add oversight command to CLI."""
    oversight_parser = subparsers.add_parser(
        'oversight',
        help='Oversight system commands (COO + HR metrics)'
    )
    oversight_subparsers = oversight_parser.add_subparsers(
        dest='oversight_command',
        help='Oversight subcommand'
    )
    
    # Report command
    report_parser = oversight_subparsers.add_parser(
        'report',
        help='Generate oversight report'
    )
    report_parser.add_argument(
        '--period',
        choices=['daily', 'weekly', 'quarterly'],
        default='daily',
        help='Report period'
    )
    report_parser.add_argument(
        '--format',
        choices=['console', 'markdown', 'json'],
        default='console',
        help='Output format'
    )
    report_parser.add_argument(
        '--days-back',
        type=int,
        default=30,
        help='Days of history to analyze'
    )
    report_parser.add_argument(
        '--output',
        '-o',
        help='Output file (stdout if not specified)'
    )
    
    report_parser.set_defaults(func=_run_report)


def _run_report(args: Any) -> int:
    """Execute oversight report command."""
    try:
        from governance.oversight import generate_report
        from pathlib import Path
        
        # Generate report
        report_text = generate_report(period=args.period, days_back=args.days_back)
        
        # Output
        if args.output:
            Path(args.output).write_text(report_text)
            print(f"✅ Report saved to: {args.output}")
        else:
            print(report_text)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return 1
