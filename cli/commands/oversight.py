"""
Oversight CLI Commands

aibrain oversight report --period daily|weekly|quarterly
"""

import click
from pathlib import Path


@click.group()
def oversight():
    """Oversight system commands (COO + HR metrics)."""
    pass


@oversight.command()
@click.option(
    '--period',
    type=click.Choice(['daily', 'weekly', 'quarterly']),
    default='daily',
    help='Report period'
)
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['console', 'markdown', 'json']),
    default='console',
    help='Output format'
)
@click.option(
    '--days-back',
    type=int,
    default=30,
    help='Days of history to analyze'
)
@click.option(
    '--output',
    '-o',
    type=click.Path(),
    help='Output file (stdout if not specified)'
)
def report(period: str, output_format: str, days_back: int, output: str):
    """
    Generate oversight report.
    
    Examples:
        aibrain oversight report --period daily
        aibrain oversight report --period weekly --format markdown > reports/weekly.md
        aibrain oversight report --period quarterly
    """
    try:
        from governance.oversight import generate_report
        
        # Generate report
        report_text = generate_report(period=period, days_back=days_back)
        
        # Output
        if output:
            Path(output).write_text(report_text)
            click.echo(f"✅ Report saved to: {output}")
        else:
            click.echo(report_text)
            
    except Exception as e:
        click.echo(f"❌ Error generating report: {e}", err=True)
        raise click.Abort()
