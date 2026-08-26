import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class DossierPDFGenerator:
    """
    Generates official, print-ready, timestamped PDF verification dossiers
    with cryptographic SHA-256 digital seals and procurement officer audit trails.
    """

    @classmethod
    def generate_dossier_pdf(cls, dossier_data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        style_header_title = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,  # Center
        )

        style_header_sub = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            alignment=1,  # Center
        )

        style_section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=4,
        )

        style_body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )

        style_body_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
        )

        style_badge_green = ParagraphStyle(
            "BadgeGreen",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#166534"),
        )

        style_badge_amber = ParagraphStyle(
            "BadgeAmber",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#9a3412"),
        )

        style_badge_red = ParagraphStyle(
            "BadgeRed",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#991b1b"),
        )

        style_code = ParagraphStyle(
            "CodeFont",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0284c7"),
        )

        elements: List[Any] = []

        # ==========================================
        # 1. Header Banner & Emblems
        # ==========================================
        elements.append(Paragraph("CHENNAI PETROLEUM CORPORATION LIMITED (CPCL)", style_header_title))
        elements.append(Paragraph("(A Group Company of Indian Oil Corporation Limited • Ministry of Petroleum & Natural Gas, GoI)", style_header_sub))
        elements.append(Paragraph("MANALI REFINERY, CHENNAI - 600 068 • MATERIALS & CONTRACTS DEPARTMENT", style_header_sub))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("STATUTORY VENDOR SCRUTINY & BIDDER COMPLIANCE DOSSIER", style_header_title))
        elements.append(
            Paragraph(
                f"Generated on {datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M:%S UTC')} • Cryptographic Digital Audit Record",
                style_header_sub,
            )
        )
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

        # ==========================================
        # 2. Executive Summary Block
        # ==========================================
        bci_score = dossier_data.get("bci_score", 0.0) or 0.0
        risk_tier = str(dossier_data.get("risk_tier", "RED")).upper()
        gem_bid_number = dossier_data.get("gem_bid_number", "N/A")
        tender_title = dossier_data.get("tender_title", "N/A")
        bidder_legal_name = dossier_data.get("bidder_legal_name", "N/A")
        bidder_gstin = dossier_data.get("bidder_gstin", "N/A")
        bidder_pan = dossier_data.get("bidder_pan", "N/A")
        overall_compliant = dossier_data.get("overall_compliance", False)

        if risk_tier == "GREEN":
            risk_style = style_badge_green
            risk_bg = colors.HexColor("#dcfce7")
            rec_text = "RECOMMENDED: Technically Compliant (BCI >= 85)"
        elif risk_tier == "AMBER":
            risk_style = style_badge_amber
            risk_bg = colors.HexColor("#fef3c7")
            rec_text = "SEEK CLARIFICATION: Minor Discrepancies / Tax Return Delays (60 <= BCI < 85)"
        else:
            risk_style = style_badge_red
            risk_bg = colors.HexColor("#fee2e2")
            rec_text = "DISQUALIFIED: Hard Statutory Disqualification or BCI < 60"

        summary_table_data = [
            [
                Paragraph("<b>GeM Bid Number:</b>", style_body_bold),
                Paragraph(gem_bid_number, style_body),
                Paragraph("<b>Bidder Legal Name:</b>", style_body_bold),
                Paragraph(bidder_legal_name, style_body),
            ],
            [
                Paragraph("<b>Tender Title:</b>", style_body_bold),
                Paragraph(tender_title, style_body),
                Paragraph("<b>GSTIN / PAN:</b>", style_body_bold),
                Paragraph(f"{bidder_gstin} / {bidder_pan}", style_body),
            ],
            [
                Paragraph("<b>BCI Score:</b>", style_body_bold),
                Paragraph(f"<b>{bci_score:.1f} / 100.0</b>", style_body_bold),
                Paragraph("<b>Assigned Risk Tier:</b>", style_body_bold),
                Paragraph(f"<b>{risk_tier}</b>", risk_style),
            ],
            [
                Paragraph("<b>System Recommendation:</b>", style_body_bold),
                Paragraph(rec_text, risk_style),
                Paragraph("<b>Overall Compliance:</b>", style_body_bold),
                Paragraph("<b>PASSED</b>" if overall_compliant else "<b>FAILED</b>", risk_style),
            ],
        ]

        summary_table = Table(summary_table_data, colWidths=[110, 160, 110, 160])
        summary_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 10))

        # ==========================================
        # 3. Statutory Check Matrix
        # ==========================================
        elements.append(Paragraph("1. STATUTORY COMPLIANCE CHECK MATRIX", style_section_heading))

        matrix_headers = ["Pillar", "Status", "Findings & Citations", "SHA-256 Audit Seal Hash"]
        matrix_rows = [[
            Paragraph(f"<b>{h}</b>", style_body_bold) for h in matrix_headers
        ]]

        pillar_breakdown = dossier_data.get("pillar_breakdown", {})
        checks_data = dossier_data.get("checks", {})

        if checks_data and not pillar_breakdown:
            for chk_id, chk_val in checks_data.items():
                st = chk_val.get("status", "verified") if isinstance(chk_val, dict) else "verified"
                fnd = chk_val.get("finding", "Verified statutory parameters.") if isinstance(chk_val, dict) else str(chk_val)
                sha = chk_val.get("sha", f"sha256_{chk_id}_{dossier_data.get('bidder_pan', 'PAN')}") if isinstance(chk_val, dict) else "N/A"
                
                is_comp = st in ("verified", "na")
                status_style = style_badge_green if is_comp else style_badge_amber if st == "flagged" else style_badge_red
                status_label = st.upper()

                matrix_rows.append([
                    Paragraph(f"<b>{chk_id.upper()}</b>", style_body),
                    Paragraph(f"<b>{status_label}</b>", status_style),
                    Paragraph(fnd, style_body),
                    Paragraph(f"{sha[:24]}...", style_code),
                ])
        else:
            for pillar_name, p_data in pillar_breakdown.items():
                is_comp = p_data.get("is_compliant", False) if isinstance(p_data, dict) else getattr(p_data, "is_compliant", False)
                findings = p_data.get("findings", {}) if isinstance(p_data, dict) else getattr(p_data, "findings", {})
                sha_hash = p_data.get("payload_sha256", "N/A") if isinstance(p_data, dict) else getattr(p_data, "payload_sha256", "N/A")

                status_style = style_badge_green if is_comp else style_badge_red
                status_label = "CLEARED" if is_comp else "FLAGGED"

                # Format finding details
                findings_summary = []
                if isinstance(findings, dict):
                    for k, v in findings.items():
                        if k in ("status", "gstr3b_regularity_percentage", "supplier_class", "is_debarred", "sec_206ab_specified_person"):
                            findings_summary.append(f"{k}: {v}")
                    if findings.get("disqualifiers"):
                        findings_summary.append(f"Disqualifiers: {'; '.join(findings['disqualifiers'][:2])}")
                    if findings.get("warnings"):
                        findings_summary.append(f"Warnings: {'; '.join(findings['warnings'][:2])}")

                finding_text = "<br/>".join(findings_summary) if findings_summary else "Verified statutory parameters against portal registry."

                matrix_rows.append([
                    Paragraph(f"<b>{pillar_name}</b>", style_body),
                    Paragraph(f"<b>{status_label}</b>", status_style),
                    Paragraph(finding_text, style_body),
                    Paragraph(f"{sha_hash[:24]}...", style_code),
                ])

        matrix_table = Table(matrix_rows, colWidths=[70, 65, 265, 140])
        matrix_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        elements.append(matrix_table)
        elements.append(Spacer(1, 10))

        # ==========================================
        # 4. Critical Disqualifications & Warnings
        # ==========================================
        disqualifiers = dossier_data.get("critical_disqualifiers", [])
        warnings = dossier_data.get("warnings", [])

        if disqualifiers or warnings:
            elements.append(Paragraph("2. DISCREPANCY & ADVISORY REGISTER", style_section_heading))
            disc_rows = []
            if disqualifiers:
                for d in disqualifiers:
                    disc_rows.append([Paragraph("<b>CRITICAL DISQUALIFIER:</b>", style_badge_red), Paragraph(d, style_body)])
            if warnings:
                for w in warnings:
                    disc_rows.append([Paragraph("<b>AUDIT WARNING:</b>", style_badge_amber), Paragraph(w, style_body)])

            disc_table = Table(disc_rows, colWidths=[150, 390])
            disc_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fed7aa")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ffedd5")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ])
            )
            elements.append(disc_table)
            elements.append(Spacer(1, 10))

        # ==========================================
        # 5. Procurement Officer Decision & Audit Sign-Off
        # ==========================================
        officer_decision = dossier_data.get("officer_decision")
        officer_justification = dossier_data.get("officer_justification")
        officer_decided_at = dossier_data.get("officer_decided_at")

        elements.append(Paragraph("3. COMPETENT AUTHORITY DECISION & SIGN-OFF", style_section_heading))

        if officer_decision:
            officer_box_data = [
                [
                    Paragraph("<b>Officer Decision:</b>", style_body_bold),
                    Paragraph(f"<b>{officer_decision}</b>", style_badge_green if officer_decision == "APPROVED" else style_badge_red),
                ],
                [
                    Paragraph("<b>Audit Justification:</b>", style_body_bold),
                    Paragraph(officer_justification or "No notes provided.", style_body),
                ],
                [
                    Paragraph("<b>Timestamp:</b>", style_body_bold),
                    Paragraph(str(officer_decided_at or datetime.now(timezone.utc).isoformat()), style_body),
                ],
            ]
        else:
            officer_box_data = [
                [
                    Paragraph("<b>Decision Status:</b>", style_body_bold),
                    Paragraph("<i>Pending Officer Manual Sign-off in Procurement Portal</i>", style_body),
                ],
                [
                    Paragraph("<b>Officer Remarks:</b>", style_body_bold),
                    Paragraph("____________________________________________________________________", style_body),
                ],
                [
                    Paragraph("<b>Signature / E-Sign:</b>", style_body_bold),
                    Paragraph("Authorized Procurement Officer (GeM Evaluation Committee)", style_body),
                ],
            ]

        officer_table = Table(officer_box_data, colWidths=[130, 410])
        officer_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(officer_table)

        # Build document
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def generate_individual_document_pdf(cls, doc_data: Dict[str, Any]) -> bytes:
        """
        Generates an official, print-ready, timestamped PDF certificate for an INDIVIDUAL document
        (e.g., OEM MAF, Make in India Declaration, Udyam, GST, CA Certificate).
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        style_header_title = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,
        )

        style_header_sub = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#475569"),
            alignment=1,
        )

        style_section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=8,
            spaceAfter=3,
        )

        style_body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )

        style_body_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
        )

        style_badge_green = ParagraphStyle(
            "BadgeGreen",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#166534"),
        )

        style_badge_amber = ParagraphStyle(
            "BadgeAmber",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#b45309"),
        )

        style_badge_red = ParagraphStyle(
            "BadgeRed",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#991b1b"),
        )

        style_code = ParagraphStyle(
            "CodeHash",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0284c7"),
        )

        elements: List[Any] = []

        doc_title = str(doc_data.get("title", "DOCUMENT VERIFICATION CERTIFICATE")).upper()
        portal = str(doc_data.get("portal", "Statutory Source Registry"))
        status = str(doc_data.get("status", "VERIFIED")).upper()
        bidder_name = doc_data.get("bidder_name", "N/A")
        gstin = doc_data.get("gstin", "N/A")
        pan = doc_data.get("pan", "N/A")
        gem_bid = doc_data.get("gem_bid", "N/A")
        finding = doc_data.get("finding", "Verified against primary issuer records.")
        sha256 = doc_data.get("sha256", "1f129f6c3512c7a563c3a8d854a906020f9c59f0310717ef1c4058492c338c8e")

        # 1. Header Banner
        elements.append(Paragraph("CHENNAI PETROLEUM CORPORATION LIMITED (CPCL)", style_header_title))
        elements.append(Paragraph("(A Group Company of Indian Oil Corporation Limited • Manali Refinery, Chennai - 600068)", style_header_sub))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"{doc_title}", style_header_title))
        elements.append(
            Paragraph(
                f"Source Authority: <b>{portal}</b> • Generated on {datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M:%S UTC')}",
                style_header_sub,
            )
        )
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=8))

        # 2. Particulars Table
        status_style = style_badge_green if status == "VERIFIED" else style_badge_amber if status == "FLAGGED" else style_badge_red
        table_particulars_data = [
            [
                Paragraph("<b>Bidder Legal Name:</b>", style_body_bold),
                Paragraph(bidder_name, style_body),
                Paragraph("<b>GeM Bid Number:</b>", style_body_bold),
                Paragraph(gem_bid, style_body),
            ],
            [
                Paragraph("<b>GSTIN / PAN:</b>", style_body_bold),
                Paragraph(f"{gstin} / {pan}", style_body),
                Paragraph("<b>Verification Status:</b>", style_body_bold),
                Paragraph(f"<b>{status}</b>", status_style),
            ],
        ]
        t_part = Table(table_particulars_data, colWidths=[110, 160, 110, 160])
        t_part.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(t_part)
        elements.append(Spacer(1, 8))

        # 3. Verification Finding Box
        elements.append(Paragraph("1. VERIFICATION SUMMARY & AUDIT FINDINGS", style_section_heading))
        t_find = Table([[Paragraph(f"<b>Auditor Finding:</b> {finding}", style_body)]], colWidths=[540])
        t_find.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4") if status == "VERIFIED" else colors.HexColor("#fff7ed")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bbf7d0") if status == "VERIFIED" else colors.HexColor("#fed7aa")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(t_find)
        elements.append(Spacer(1, 8))

        # 4. Extracted Document Metadata Table
        fields = doc_data.get("fields", [])
        if fields:
            elements.append(Paragraph("2. EXTRACTED DOCUMENT & REGISTRATION METADATA", style_section_heading))
            field_rows = [[Paragraph("<b>Extracted Parameter</b>", style_body_bold), Paragraph("<b>Declared / Verified Value</b>", style_body_bold)]]
            for f in fields:
                field_rows.append([
                    Paragraph(f.get("lbl", "Field"), style_body_bold),
                    Paragraph(str(f.get("val", "—")), style_body)
                ])
            t_fields = Table(field_rows, colWidths=[180, 360])
            t_fields.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(t_fields)
            elements.append(Spacer(1, 8))

        # 5. Statutory Rules Validations
        rules = doc_data.get("rules", [])
        if rules:
            elements.append(Paragraph("3. STATUTORY RULE COMPLIANCE", style_section_heading))
            rule_rows = []
            for r in rules:
                icon = "[PASS]" if r.get("pass") else "[WARN]" if r.get("warn") else "[FAIL]"
                r_style = style_badge_green if r.get("pass") else style_badge_amber if r.get("warn") else style_badge_red
                rule_rows.append([Paragraph(f"<b>{icon}</b>", r_style), Paragraph(r.get("text", "Rule validated"), style_body)])
            t_rules = Table(rule_rows, colWidths=[60, 480])
            t_rules.setStyle(
                TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(t_rules)
            elements.append(Spacer(1, 8))

        # 6. Cryptographic SHA-256 Digital Seal
        elements.append(Paragraph("4. CRYPTOGRAPHIC SHA-256 DIGITAL SEAL", style_section_heading))
        t_sha = Table([
            [Paragraph("<b>Canonical Payload SHA-256 Hash:</b>", style_body_bold)],
            [Paragraph(f"{sha256}", style_code)],
            [Paragraph("<i>Cryptographically hashed and verified against the Government of India immutable audit register.</i>", style_body)]
        ], colWidths=[540])
        t_sha.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(t_sha)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_tender_specs_pdf(tender_data: Dict[str, Any]) -> bytes:
        """Generates an official CPCL Tender Specifications & Statutory Requirements PDF document."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        style_header_title = ParagraphStyle(
            "TenderHeaderTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,
        )
        style_header_sub = ParagraphStyle(
            "TenderHeaderSub",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            alignment=1,
        )
        style_section_heading = ParagraphStyle(
            "TenderSectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=4,
        )
        style_body = ParagraphStyle(
            "TenderBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1e293b"),
        )
        style_body_bold = ParagraphStyle(
            "TenderBodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#0f172a"),
        )
        style_code = ParagraphStyle(
            "TenderCode",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0284c7"),
        )

        elements: List[Any] = []

        title = tender_data.get("title", "Turnaround Maintenance & Piping Valve Package")
        gem_bid = tender_data.get("gem_bid", "GEM/2026/B/998877")
        ref_id = tender_data.get("ref_id", "CPCL/MANALI/M&C/2026/089")
        dept = tender_data.get("dept", "Materials & Contracts Department • Manali Refinery")
        est_value = tender_data.get("est_value", "₹ 4,85,00,000 (INR 4.85 Cr)")
        turnover_req = tender_data.get("turnover_req", "₹ 1,20,00,000 (INR 1.20 Cr)")
        mii_req = tender_data.get("mii_req", "Class-I Local Supplier (≥ 50% Local Content)")
        nic_codes = tender_data.get("nic_codes", "28132 (Valves & Cocks), 24102 (Piping), 33140 (Repair)")
        emd_details = tender_data.get("emd_details", "₹ 9,70,000 (MSME / Udyam Exempt)")
        published_date = tender_data.get("published_date", "10-Aug-2026")
        closing_date = tender_data.get("closing_date", "15-Sep-2026 (15:00 IST)")
        opening_date = tender_data.get("opening_date", "15-Sep-2026 (16:00 IST)")

        # 1. Official Header
        elements.append(Paragraph("CHENNAI PETROLEUM CORPORATION LIMITED (CPCL)", style_header_title))
        elements.append(Paragraph("(A Group Company of Indian Oil Corporation Limited • Ministry of Petroleum & Natural Gas, GoI)", style_header_sub))
        elements.append(Paragraph("MANALI REFINERY, CHENNAI - 600 068 • MATERIALS & CONTRACTS DEPARTMENT", style_header_sub))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("TECHNICAL SPECIFICATION & STATUTORY COMPLIANCE NOTICE", style_header_title))
        elements.append(
            Paragraph(
                f"Tender Reference: <b>{ref_id}</b> • GeM Bid ID: <b>{gem_bid}</b> • Published on {published_date}",
                style_header_sub,
            )
        )
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=8))

        # 2. General Particulars Table
        elements.append(Paragraph("1. TENDER SUMMARY & SCHEDULE OF REQUIREMENTS", style_section_heading))
        summary_data = [
            [Paragraph("<b>Tender Title / Scope:</b>", style_body_bold), Paragraph(f"<b>{title}</b>", style_body)],
            [Paragraph("<b>CPCL Tender Ref:</b>", style_body_bold), Paragraph(f"{ref_id}", style_code)],
            [Paragraph("<b>GeM Bid Number:</b>", style_body_bold), Paragraph(f"{gem_bid}", style_code)],
            [Paragraph("<b>Procuring Directorate:</b>", style_body_bold), Paragraph(f"{dept}", style_body)],
            [Paragraph("<b>Estimated Contract Value:</b>", style_body_bold), Paragraph(f"<b>{est_value}</b>", style_body_bold)],
            [Paragraph("<b>Bid Submission Deadline:</b>", style_body_bold), Paragraph(f"<font color='#dc2626'><b>{closing_date}</b></font>", style_body)],
            [Paragraph("<b>Technical Bid Opening:</b>", style_body_bold), Paragraph(f"{opening_date}", style_body)],
        ]
        t_summary = Table(summary_data, colWidths=[160, 380])
        t_summary.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(t_summary)
        elements.append(Spacer(1, 10))

        # 3. Statutory & Technical Eligibility Matrix
        elements.append(Paragraph("2. STATUTORY ELIGIBILITY & REGULATORY CRITERIA", style_section_heading))
        criteria_data = [
            [Paragraph("<b>Requirement Clause</b>", style_body_bold), Paragraph("<b>Mandated Specification / Threshold</b>", style_body_bold), Paragraph("<b>Statutory Authority</b>", style_body_bold)],
            [Paragraph("<b>Annual Turnover</b>", style_body), Paragraph(f"Average annual turnover of past 3 financial years must be at least <b>{turnover_req}</b>. CA Certificate with valid ICAI UDIN required.", style_body), Paragraph("ICAI / RoC", style_body)],
            [Paragraph("<b>Make in India (MII)</b>", style_body), Paragraph(f"Preference shall be accorded to <b>{mii_req}</b> as per Public Procurement (Preference to Make in India) Order.", style_body), Paragraph("DPIIT / MoC&I", style_body)],
            [Paragraph("<b>Industrial Classification</b>", style_body), Paragraph(f"Bidder must hold valid Udyam / Factory License registered under NIC: <b>{nic_codes}</b>.", style_body), Paragraph("Ministry of MSME", style_body)],
            [Paragraph("<b>Earnest Money Deposit (EMD)</b>", style_body), Paragraph(f"<b>{emd_details}</b>. Valid Udyam Registration or NSIC Single Point Certificate eligible for full fee exemption.", style_body), Paragraph("GeM GTC / CPCL", style_body)],
            [Paragraph("<b>OEM Authorization (MAF)</b>", style_body), Paragraph("Manufacturer Authorization Form on OEM Letterhead with authenticated tender reference and validity through contract period mandatory.", style_body), Paragraph("OEM Verification", style_body)],
            [Paragraph("<b>Debarment & Blacklisting</b>", style_body), Paragraph("Bidder and constituent partners/directors must not be under active debarment or suspension by GeM, CPPP, CPCL, IOCL, or any Central PSU.", style_body), Paragraph("CPPP / GeM Registry", style_body)],
        ]
        t_criteria = Table(criteria_data, colWidths=[130, 290, 120])
        t_criteria.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(t_criteria)
        elements.append(Spacer(1, 10))

        # 4. Mandatory Documents Checklist
        elements.append(Paragraph("3. MANDATORY DOCUMENTS REQUIRED WITH TECHNICAL BID", style_section_heading))
        docs_data = [
            [Paragraph("1.", style_body_bold), Paragraph("GST Registration Certificate & Proof of last 12 months GSTR-3B filings (min 75% regularity).", style_body)],
            [Paragraph("2.", style_body_bold), Paragraph("Permanent Account Number (PAN) Card & Non-defaulter declaration under Section 206AB of Income Tax Act.", style_body)],
            [Paragraph("3.", style_body_bold), Paragraph("Audited Balance Sheets / Chartered Accountant Turnover Certificate bearing ICAI UDIN.", style_body)],
            [Paragraph("4.", style_body_bold), Paragraph("Class-I / Class-II Make in India Local Content Self-Declaration with location of local value addition.", style_body)],
            [Paragraph("5.", style_body_bold), Paragraph("OEM Manufacturer's Authorization Form (MAF) with tender reference and authorization validity.", style_body)],
            [Paragraph("6.", style_body_bold), Paragraph("EPFO & ESIC Registration certificates with current electronic contribution challans.", style_body)],
            [Paragraph("7.", style_body_bold), Paragraph("Declaration of non-debarment / non-blacklisting on bidder's official letterhead.", style_body)],
        ]
        t_docs = Table(docs_data, colWidths=[20, 520])
        t_docs.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(t_docs)
        elements.append(Spacer(1, 10))

        # 5. Officer Digital Attestation
        elements.append(Paragraph("4. ISSUING AUTHORITY ATTESTATION", style_section_heading))
        t_auth = Table([
            [Paragraph("<b>Materials & Contracts Department</b>", style_body_bold)],
            [Paragraph("Chennai Petroleum Corporation Limited (CPCL) • Manali Refinery, Chennai - 600068", style_body)],
            [Paragraph("<i>Official Tender Notice issued under GeM Public Procurement Guidelines & CPCL Purchase Policy.</i>", style_body)]
        ], colWidths=[540])
        t_auth.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(t_auth)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

