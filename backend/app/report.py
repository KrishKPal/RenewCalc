"""Printable PDF created from the persisted assessment result (no recalculation)."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether


def create_pdf(result: dict) -> bytes:
    output = BytesIO()
    pdf = SimpleDocTemplate(output, pagesize=A4, rightMargin=19*mm, leftMargin=19*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    base = getSampleStyleSheet()
    title_style = ParagraphStyle("BrandTitle", parent=base["Title"], fontSize=21, leading=27,
                                 textColor=colors.HexColor("#124b3a"), spaceAfter=10)
    section_style = ParagraphStyle("SectionTitle", parent=base["Heading2"], fontSize=13, leading=18,
                                   textColor=colors.HexColor("#123448"), spaceBefore=17, spaceAfter=8)
    small = ParagraphStyle("Small", parent=base["BodyText"], fontSize=9.1, leading=14,
                           textColor=colors.HexColor("#425a57"), spaceAfter=5)
    blocks = [Paragraph("RenewCalc | Solar Feasibility", title_style),
              Paragraph("Location: " + escape(result["location"]["name"]), small),
              Paragraph("Calculation: " + result["calculation_version"] + " | " + result["computed_at"][:10], small),
              Paragraph("Outcome: " + result["status"].replace("_", " ").title(), section_style),
              Paragraph(escape(result["explanation"]), small)]
    p = result["selected"]
    f = result["finance"]
    def table(rows):
        wrapped = [[Paragraph(str(cell), small) for cell in row] for row in rows]
        t = Table(wrapped, colWidths=[84*mm, 82*mm], repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0),colors.HexColor("#E7F3EC")),
            ("ROWBACKGROUNDS", (0,1),(-1,-1),[colors.white,colors.HexColor("#F7FAF8")]),
            ("BOTTOMPADDING", (0,0),(-1,-1),8),
            ("TOPPADDING", (0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        return t
    blocks += [Paragraph("Energy and investment summary", section_style), table([
        ["Metric", "Estimate"],
        ["Installed DC capacity", f"{p['capacity_kwp']:.2f} kWp ({p['modules']} modules)"],
        ["Mean annual solar generation", f"{result['annual_generation_kwh']:,.0f} kWh"],
        ["Mean annual self-consumption", f"{result['annual_self_consumed_kwh']:,.0f} kWh"],
        ["Mean annual exports", f"{result['annual_export_kwh']:,.0f} kWh"],
        ["Modeled first-year savings", f"INR {p['year_one_bill_savings_inr']:,.0f}"],
        ["Installation cost assumption", f"INR {p['capex_inr']:,.0f}"],
        ["25-year net present value", f"INR {f['npv_inr']:,.0f}"],
        ["Simple payback", f"{f['simple_payback_years']} years" if f['simple_payback_years'] is not None else "Not reached in analysis horizon"],
    ])]
    blocks.append(Paragraph("Monthly average output", section_style))
    monthly_rows = [["Month", "Solar (kWh)", "Bill before (INR)", "Bill after (INR)"]]
    for row in result["monthly"]:
        monthly_rows.append([str(row["month"]), f"{row['generation_kwh']:,.0f}",
                             f"{row['baseline_bill_inr']:,.0f}", f"{row['solar_bill_inr']:,.0f}"])
    t = Table(monthly_rows, colWidths=[25*mm,42*mm,47*mm,47*mm],repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E7F3EC")),
                           ("TEXTCOLOR",(0,0),(-1,0),colors.HexColor("#174936")),
                           ("FONTSIZE",(0,0),(-1,-1),8), ("TOPPADDING",(0,0),(-1,-1),6),
                           ("BOTTOMPADDING",(0,0),(-1,-1),6), ("LINEBELOW",(0,-1),(-1,-1),.3,colors.grey)]))
    blocks.append(t)
    blocks.append(Paragraph("Alternative system sizes", section_style))
    option_rows = [["Capacity", "Annual generation", "NPV", "Payback"]]
    for option in result["alternatives"][:12]:
        option_rows.append([f"{option['capacity_kwp']:.2f} kWp", f"{option['annual_kwh']:,.0f} kWh",
                            f"INR {option['npv_inr']:,.0f}",
                            f"{option['simple_payback_years']} yr" if option["simple_payback_years"] is not None else "Not reached"])
    option_table = Table(option_rows, colWidths=[35*mm,45*mm,42*mm,39*mm], repeatRows=1, hAlign="LEFT")
    option_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E7F3EC")),
                           ("FONTSIZE",(0,0),(-1,-1),8), ("TOPPADDING",(0,0),(-1,-1),5),
                           ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    blocks.append(option_table)
    blocks.append(Paragraph("Scenario sensitivity (not confidence intervals)", section_style))
    for scenario in result.get("scenarios", []):
        blocks.append(Paragraph(f"{scenario['name']}: NPV INR {scenario['npv_inr']:,.0f}; CAPEX adjustment {scenario['capex_adjustment_pct']}%; historical weather year {scenario['weather_reference_year'] or 'average'}", small))
    blocks.append(Paragraph("Sources and limitations", section_style))
    for source in result["sources"]:
        blocks.append(Paragraph("- " + source["provider"] + ": " + str(source.get("dataset",source.get("status",""))),small))
    for assumption in result["assumptions"]:
        blocks.append(Paragraph("- " + escape(assumption),small))
    blocks.append(Spacer(1,8))
    blocks.append(Paragraph("Research scenario only. Not an installation quotation, guaranteed return or professional structural/electrical certification.",small))
    pdf.build(blocks)
    return output.getvalue()
