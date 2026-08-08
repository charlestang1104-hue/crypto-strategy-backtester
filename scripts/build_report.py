"""Build the public research report from committed experiment artifacts."""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "research-report.pdf"
BASELINE_METRICS = (
    ROOT / "artifacts" / "full_sample_baseline" / "metrics" / "performance_summary.csv"
)
HOLDOUT_METRICS = ROOT / "artifacts" / "holdout_evaluation" / "metrics" / "performance_summary.csv"

NAVY = colors.HexColor("#0f172a")
BLUE = colors.HexColor("#2563eb")
ORANGE = colors.HexColor("#ea580c")
RED = colors.HexColor("#b91c1c")
SLATE = colors.HexColor("#475569")
PALE_BLUE = colors.HexColor("#eff6ff")
PALE_SLATE = colors.HexColor("#f8fafc")
LINE = colors.HexColor("#cbd5e1")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def select(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    for row in rows:
        if all(row[key] == value for key, value in criteria.items()):
            return row
    raise KeyError(f"No metric row matches {criteria}")


def percentage(value: str, digits: int = 2) -> str:
    return f"{float(value):+.{digits}%}"


def number(value: str, digits: int = 0) -> str:
    return f"{float(value):,.{digits}f}"


def metric_table(data: list[list[str]], widths: list[float]) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE_SLATE]),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def report_image(path: Path, width: float) -> Image:
    image = Image(str(path))
    scale = width / image.imageWidth
    image.drawWidth = width
    image.drawHeight = image.imageHeight * scale
    return image


def page_decor(canvas, document) -> None:  # noqa: ANN001
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 16 * mm, A4[0] - 20 * mm, 16 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE)
    canvas.drawString(20 * mm, 10 * mm, "Crypto Strategy Backtester | Research only")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"{document.page}")
    canvas.restoreState()


def build() -> Path:
    baseline_rows = read_rows(BASELINE_METRICS)
    holdout_rows = read_rows(HOLDOUT_METRICS)
    mean = select(
        baseline_rows,
        period="full_sample",
        strategy="mean_reversion",
        cost_scenario="baseline",
    )
    trend = select(
        baseline_rows,
        period="full_sample",
        strategy="trend_following",
        cost_scenario="baseline",
    )
    development = select(
        holdout_rows,
        period="development",
        strategy="trend_following",
        cost_scenario="baseline",
    )
    holdout = select(
        holdout_rows,
        period="holdout",
        strategy="trend_following",
        cost_scenario="baseline",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title="Crypto Strategy Backtester",
        author="Qianfeng Tang",
        subject="Cost-aware systematic crypto strategy research",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=27,
            leading=31,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=SLATE,
            spaceAfter=8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=NAVY,
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Subsection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=BLUE,
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.2,
            textColor=NAVY,
            spaceAfter=2.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.7,
            leading=10.5,
            textColor=SLATE,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Callout",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=RED,
            backColor=colors.HexColor("#fef2f2"),
            borderColor=colors.HexColor("#fecaca"),
            borderWidth=0.6,
            borderPadding=8,
            spaceBefore=2 * mm,
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Caption",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=SLATE,
            spaceBefore=1 * mm,
            spaceAfter=3 * mm,
        )
    )

    story = [
        Spacer(1, 8 * mm),
        Paragraph("Crypto Strategy Backtester", styles["ReportTitle"]),
        Paragraph(
            "Cost-aware research on fixed-rule cryptocurrency signals",
            styles["Subtitle"],
        ),
        Paragraph("Qianfeng Tang | 8 August 2026", styles["Body"]),
        Spacer(1, 5 * mm),
        Table(
            [
                ["Sample", "Assets", "Initial capital"],
                ["2024-01-01 to 2026-01-01", "BTCUSDT, ETHUSDT, BNBUSDT", "10,000 USDT"],
            ],
            colWidths=[55 * mm, 70 * mm, 40 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, 1), PALE_BLUE),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]
            ),
        ),
        Spacer(1, 8 * mm),
        Paragraph("Executive summary", styles["Section"]),
        Paragraph(
            "This study tests transparent mean-reversion and trend-following rules on 6-hour spot "
            "crypto data. The framework makes time alignment, target exposure, turnover, transaction "
            "costs, and failure conditions explicit. All executable targets use a one-bar signal lag.",
            styles["Body"],
        ),
        Paragraph(
            f"At the baseline cost, full-sample trend following returns {percentage(trend['net_return'])} "
            f"but has a Sharpe ratio of {float(trend['sharpe_net']):.3f} and a maximum drawdown of "
            f"{percentage(trend['max_drawdown_net'])}. Mean reversion loses all capital. Most "
            "importantly, the fixed trend rule also loses almost all capital in the illustrative "
            "2025 holdout.",
            styles["Callout"],
        ),
        Paragraph(
            "The evidence does not support an investable-strategy claim. It supports a software and "
            "research conclusion: cost assumptions, chronological evaluation, and downside metrics can "
            "reverse the story told by a single profitable full-sample curve.",
            styles["Body"],
        ),
        Spacer(1, 3 * mm),
        report_image(
            ROOT
            / "artifacts"
            / "full_sample_baseline"
            / "figures"
            / "full_sample_equity_curves.png",
            165 * mm,
        ),
        Paragraph(
            "Figure 1. Full-sample net portfolio value after the baseline Roll-style trading cost.",
            styles["Caption"],
        ),
        PageBreak(),
        Paragraph("1. Research design", styles["Section"]),
        Paragraph("Data", styles["Subsection"]),
        Paragraph(
            "The sample contains 2,924 UTC bars per asset from Binance Public Data. The effective "
            "federal funds rate from FRED is converted to a 6-hour step rate and aligned using only "
            "same-date or earlier observations. The validation layer checks schema, symbol coverage, "
            "chronological ordering, duplicates, gaps, price positivity, and finite values.",
            styles["Body"],
        ),
        report_image(
            ROOT / "artifacts" / "full_sample_baseline" / "figures" / "market_overview.png",
            165 * mm,
        ),
        Paragraph(
            "Figure 2. Normalized close prices and 6-hour simple returns for the three assets.",
            styles["Caption"],
        ),
        Paragraph("Signals and timing", styles["Subsection"]),
        Paragraph(
            "Mean reversion uses a 40-bar rolling price z-score: long below -1 and short above +1. "
            "Trend following uses the sign of the 8-bar versus 32-bar moving-average difference. "
            "Signals observed at time t become executable targets at t+1. Target weights are "
            "normalized to a 100,000 USDT gross cap.",
            styles["Body"],
        ),
        Paragraph("Cost and capital model", styles["Subsection"]),
        Paragraph(
            "A per-asset Roll-style estimate is derived from lag-1 return covariance and averaged "
            "across assets. The baseline estimate is 0.1147% per unit traded, with 0.5x and 1.5x "
            "sensitivity cases. Executed gross exposure is limited to the smaller of 100,000 USDT and "
            "10 times current equity. Realized portfolio value cannot become negative.",
            styles["Body"],
        ),
        PageBreak(),
        Paragraph("2. Full-sample results", styles["Section"]),
        metric_table(
            [
                ["Strategy", "Net return", "Sharpe", "Sortino", "Max drawdown", "Turnover"],
                [
                    "Mean reversion",
                    percentage(mean["net_return"]),
                    f"{float(mean['sharpe_net']):.3f}",
                    f"{float(mean['sortino_net']):.3f}",
                    percentage(mean["max_drawdown_net"]),
                    number(mean["total_turnover_usdt"]),
                ],
                [
                    "Trend following",
                    percentage(trend["net_return"]),
                    f"{float(trend['sharpe_net']):.3f}",
                    f"{float(trend['sortino_net']):.3f}",
                    percentage(trend["max_drawdown_net"]),
                    number(trend["total_turnover_usdt"]),
                ],
            ],
            [35 * mm, 24 * mm, 20 * mm, 20 * mm, 28 * mm, 38 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            f"Trend following finishes at {number(trend['final_net_value'], 2)} USDT, but modeled "
            f"baseline cost totals {number(trend['total_cost_usdt'], 2)} USDT. Its Sharpe ratio is "
            "low, and its 82.1% drawdown is too large to describe the rule as robust. Mean reversion "
            "cannot overcome turnover-linked cost and reaches the capital floor.",
            styles["Body"],
        ),
        report_image(
            ROOT
            / "artifacts"
            / "full_sample_baseline"
            / "figures"
            / "full_sample_cost_sensitivity.png",
            150 * mm,
        ),
        Paragraph(
            "Figure 3. Net return deteriorates sharply as the proportional-cost assumption rises.",
            styles["Caption"],
        ),
        report_image(
            ROOT
            / "artifacts"
            / "full_sample_baseline"
            / "figures"
            / "full_sample_cumulative_net_pnl.png",
            150 * mm,
        ),
        Paragraph(
            "Figure 4. Daily-sampled cumulative net PnL under the baseline cost.",
            styles["Caption"],
        ),
        PageBreak(),
        Paragraph("3. Chronological robustness", styles["Section"]),
        Paragraph(
            "The same fixed parameters are evaluated separately in 2024 and 2025. No parameter "
            "optimization is performed on the holdout. Because the repository was created "
            "retrospectively from an earlier full-sample analysis, this split is illustrative rather "
            "than a pristine deployment-grade out-of-sample test.",
            styles["Body"],
        ),
        metric_table(
            [
                ["Period", "Strategy", "Net return", "Sharpe", "Max drawdown", "Final value"],
                [
                    "Development 2024",
                    "Trend following",
                    percentage(development["net_return"]),
                    f"{float(development['sharpe_net']):.3f}",
                    percentage(development["max_drawdown_net"]),
                    number(development["final_net_value"], 2),
                ],
                [
                    "Holdout 2025",
                    "Trend following",
                    percentage(holdout["net_return"]),
                    f"{float(holdout['sharpe_net']):.3f}",
                    percentage(holdout["max_drawdown_net"]),
                    number(holdout["final_net_value"], 2),
                ],
            ],
            [33 * mm, 36 * mm, 24 * mm, 20 * mm, 27 * mm, 25 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "The development period creates the apparent full-sample success. In the 2025 holdout, "
            "the same trend rule produces a -1.446 Sharpe ratio and almost total capital loss. This "
            "regime instability dominates the investment interpretation.",
            styles["Callout"],
        ),
        report_image(
            ROOT / "artifacts" / "holdout_evaluation" / "figures" / "development_equity_curves.png",
            150 * mm,
        ),
        Paragraph("Figure 5. Development-period net equity curves.", styles["Caption"]),
        report_image(
            ROOT / "artifacts" / "holdout_evaluation" / "figures" / "holdout_equity_curves.png",
            150 * mm,
        ),
        Paragraph("Figure 6. Illustrative holdout net equity curves.", styles["Caption"]),
        PageBreak(),
        Paragraph("4. Engineering controls", styles["Section"]),
        Paragraph(
            "The analysis is implemented as an installable Python package rather than a notebook-only "
            "script. Strict YAML configuration defines each experiment. A CLI validates cached data, "
            "runs experiments, and returns non-zero codes for invalid inputs. Artifacts are generated "
            "in a staging directory and published only after all metrics and figures succeed.",
            styles["Body"],
        ),
        KeepTogether(
            [
                Paragraph("Automated checks", styles["Subsection"]),
                Paragraph(
                    "Nineteen tests cover signal lagging, exposure bounds, data repairs, risk-free "
                    "alignment, cost monotonicity on controlled fixtures, capital floors, hand-checked "
                    "metrics, CLI behavior, a network-free integration run, and accepted baseline "
                    "regression values. GitHub Actions runs Ruff and pytest on Python 3.11 and 3.12.",
                    styles["Body"],
                ),
            ]
        ),
        Paragraph("Limitations", styles["Subsection"]),
        Paragraph(
            "The execution model omits explicit exchange fees, dynamic spreads, market impact, "
            "funding, latency, partial fills, and survivorship controls. The sample covers only three "
            "assets and two years. The outlier rule is a defensive data-engineering demonstration, not "
            "a substitute for multi-vendor reconciliation. No claim of statistical significance or "
            "future profitability is made.",
            styles["Body"],
        ),
        Paragraph("Next research steps", styles["Subsection"]),
        Paragraph(
            "Useful extensions include volatility-targeted sizing, risk budgets, quote-based spread "
            "and impact estimates, walk-forward evaluation, bootstrap uncertainty intervals, a wider "
            "survivorship-controlled universe, and a forward paper-trading period.",
            styles["Body"],
        ),
        Paragraph("Reproducibility and sources", styles["Subsection"]),
        Paragraph(
            "The repository documents installation, configuration, CLI reproduction, committed "
            "metrics, and public source attribution. Market bars come from Binance Public Data; the "
            "risk-free proxy is FRED series DFF. Provider data remains subject to provider terms. The "
            "authored code is MIT licensed.",
            styles["Body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Research only - not investment advice. The project is not affiliated with or endorsed by "
            "Binance or the Federal Reserve Bank of St. Louis.",
            styles["Callout"],
        ),
    ]
    document.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    return OUTPUT


if __name__ == "__main__":
    print(build())
