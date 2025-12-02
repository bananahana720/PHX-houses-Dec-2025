"""HTML report generator using Jinja2 templates.

Generates interactive HTML reports for risk assessment and renovation analysis
using pre-designed Jinja2 templates.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..domain.entities import Property
from .base import Reporter


class HtmlReportGenerator(Reporter):
    """Generate HTML reports using Jinja2 templates.

    Supports multiple report types:
    - Risk assessment report
    - Renovation gap analysis report
    - Custom reports via templates

    Template directory defaults to project root/templates but can be configured.
    """

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        """Initialize HTML report generator.

        Args:
            template_dir: Path to Jinja2 templates directory.
                         Defaults to <project_root>/templates
        """
        if template_dir is None:
            # Default to project root templates directory
            project_root = Path(__file__).parent.parent.parent.parent
            template_dir = project_root / "templates"

        if not template_dir.exists():
            raise ValueError(f"Template directory not found: {template_dir}")

        self.template_dir = template_dir

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, properties: List[Property], output_path: Path) -> None:
        """Generate HTML report (legacy interface - use specific methods).

        This is a compatibility method. Use generate_risk_report() or
        generate_renovation_report() for specific report types.

        Args:
            properties: List of Property entities
            output_path: Output file path

        Raises:
            ValueError: If properties list is empty
        """
        if not properties:
            raise ValueError("Cannot generate report from empty properties list")

        # Default to risk report for legacy compatibility
        self.generate_risk_report(properties, output_path)

    def generate_risk_report(
        self, properties: List[Property], output_path: Path
    ) -> None:
        """Generate risk assessment HTML report.

        Produces an interactive table showing risk levels across categories:
        - Noise risk (highway proximity)
        - Infrastructure risk (building age)
        - Solar risk (lease complications)
        - Cooling cost risk (orientation)
        - School quality risk
        - Lot size margin risk

        Args:
            properties: List of Property entities with risk_assessments populated
            output_path: Output file path (.html)

        Raises:
            ValueError: If properties list is empty
        """
        if not properties:
            raise ValueError("Cannot generate risk report from empty properties list")

        # Sort by overall risk score (lowest = safest first)
        sorted_properties = sorted(
            properties,
            key=lambda p: sum(
                3 if r.level.value == "high" else (1 if r.level.value in ["medium", "unknown"] else 0)
                for r in p.risk_assessments
            ),
        )

        # Load and render template
        template = self.env.get_template("risk_report.html")
        html_content = template.render(properties=sorted_properties)

        # Write output
        output_path.write_text(html_content, encoding="utf-8")

    def generate_renovation_report(
        self, properties: List[Property], output_path: Path
    ) -> None:
        """Generate renovation gap analysis HTML report.

        Shows estimated renovation costs and true cost (list price + renovations).
        Color-codes properties by renovation cost percentage:
        - Green: <5% of list price
        - Yellow: 5-10% of list price
        - Red: >10% of list price

        Args:
            properties: List of Property entities with renovation_estimate populated
            output_path: Output file path (.html)

        Raises:
            ValueError: If properties list is empty
        """
        if not properties:
            raise ValueError(
                "Cannot generate renovation report from empty properties list"
            )

        # Calculate summary statistics
        total_properties = len(properties)
        renovation_totals = [
            p.renovation_estimate.total if p.renovation_estimate else 0.0
            for p in properties
        ]

        avg_renovation = sum(renovation_totals) / len(renovation_totals)
        min_renovation = min(renovation_totals)
        max_renovation = max(renovation_totals)
        high_cost_count = sum(1 for total in renovation_totals if total > 20000)

        # Find best value (lowest effective_price among passing properties)
        passing_properties = [p for p in properties if p.kill_switch_passed]
        if passing_properties:
            best_value = min(passing_properties, key=lambda p: p.effective_price)
            best_value_address = best_value.full_address
        else:
            best_value_address = "N/A"

        # Load and render template
        template = self.env.get_template("renovation_report.html")
        html_content = template.render(
            properties=properties,
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            total_properties=total_properties,
            avg_renovation=avg_renovation,
            min_renovation=min_renovation,
            max_renovation=max_renovation,
            high_cost_count=high_cost_count,
            best_value_address=best_value_address,
        )

        # Write output
        output_path.write_text(html_content, encoding="utf-8")

    def generate_custom_report(
        self,
        properties: List[Property],
        output_path: Path,
        template_name: str,
        **context,
    ) -> None:
        """Generate custom HTML report from template.

        Allows generating reports from custom templates with additional context.

        Args:
            properties: List of Property entities
            output_path: Output file path (.html)
            template_name: Name of template file in template directory
            **context: Additional context variables to pass to template

        Raises:
            ValueError: If properties list is empty
            jinja2.TemplateNotFound: If template_name doesn't exist
        """
        if not properties:
            raise ValueError("Cannot generate custom report from empty properties list")

        # Load and render template
        template = self.env.get_template(template_name)
        html_content = template.render(properties=properties, **context)

        # Write output
        output_path.write_text(html_content, encoding="utf-8")
