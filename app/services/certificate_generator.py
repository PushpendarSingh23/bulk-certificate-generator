from datetime import date
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from app.core.logging import logger


class CertificateGenerator:
    """
    Generates professional landscape-oriented PDF certificates using ReportLab.
    """

    # Colors
    NAVY = colors.HexColor("#0f2537")
    GOLD = colors.HexColor("#c69214")
    GOLD_LIGHT = colors.HexColor("#dfb15b")
    DARK_GRAY = colors.HexColor("#2c3e50")
    MUTED_GRAY = colors.HexColor("#64748b")
    LIGHT_BG = colors.HexColor("#fcfbf8")

    @classmethod
    def generate(
        cls,
        output_path: Path,
        recipient_name: str,
        event_name: str,
        organization_name: str,
        issue_date: date,
        certificate_id: str,
        certificate_title: str = "Certificate of Completion"
    ) -> Path:
        """
        Builds the PDF certificate and writes it to output_path.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Page size: Landscape Letter (792 x 612 points)
        width, height = landscape(letter)
        
        c = canvas.Canvas(str(output_path), pagesize=landscape(letter))
        c.setTitle(f"Certificate - {recipient_name}")
        c.setSubject(event_name)
        c.setAuthor(organization_name)

        # 1. Background Fill
        c.setFillColor(cls.LIGHT_BG)
        c.rect(0, 0, width, height, fill=1, stroke=0)

        # 2. Decorative Outer Border (Navy)
        c.setStrokeColor(cls.NAVY)
        c.setLineWidth(6)
        c.rect(20, 20, width - 40, height - 40, fill=0, stroke=1)

        # 3. Decorative Inner Border (Gold)
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(2)
        c.rect(28, 28, width - 56, height - 56, fill=0, stroke=1)

        # 4. Corner Ornaments (Gold geometric corner accents)
        corner_len = 35
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(3)
        # Top-left
        c.line(35, height - 35, 35 + corner_len, height - 35)
        c.line(35, height - 35, 35, height - 35 - corner_len)
        # Top-right
        c.line(width - 35, height - 35, width - 35 - corner_len, height - 35)
        c.line(width - 35, height - 35, width - 35, height - 35 - corner_len)
        # Bottom-left
        c.line(35, 35, 35 + corner_len, 35)
        c.line(35, 35, 35, 35 + corner_len)
        # Bottom-right
        c.line(width - 35, 35, width - 35 - corner_len, 35)
        c.line(width - 35, 35, width - 35, 35 + corner_len)

        # 5. Issuing Organization (Top Header)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(cls.NAVY)
        c.drawCentredString(width / 2.0, height - 80, organization_name.upper())

        # Thin divider line under organization
        c.setStrokeColor(cls.GOLD_LIGHT)
        c.setLineWidth(1)
        c.line(width / 2.0 - 120, height - 90, width / 2.0 + 120, height - 90)

        # 6. Certificate Title
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(cls.GOLD)
        c.drawCentredString(width / 2.0, height - 130, certificate_title.upper())

        # 7. Subtitle / Presentation line
        c.setFont("Helvetica", 13)
        c.setFillColor(cls.MUTED_GRAY)
        c.drawCentredString(width / 2.0, height - 170, "THIS IS PROUDLY PRESENTED TO")

        # 8. Recipient Full Name
        c.setFont("Helvetica-Bold", 30)
        c.setFillColor(cls.NAVY)
        c.drawCentredString(width / 2.0, height - 220, recipient_name)

        # Name underline
        name_width = c.stringWidth(recipient_name, "Helvetica-Bold", 30)
        line_half = max(name_width / 2.0 + 20, 150)
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(1.5)
        c.line(width / 2.0 - line_half, height - 230, width / 2.0 + line_half, height - 230)

        # 9. Statement of Completion / Event Details
        c.setFont("Helvetica", 13)
        c.setFillColor(cls.DARK_GRAY)
        c.drawCentredString(
            width / 2.0,
            height - 275,
            "for successfully completing the curriculum and demonstrating excellence in"
        )

        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(cls.NAVY)
        c.drawCentredString(width / 2.0, height - 315, event_name)

        # 10. Decorative Circular Seal (Center-Lower)
        seal_x = width / 2.0
        seal_y = height - 410
        
        # Outer seal circle
        c.setStrokeColor(cls.GOLD)
        c.setFillColor(cls.LIGHT_BG)
        c.setLineWidth(2)
        c.circle(seal_x, seal_y, 32, fill=1, stroke=1)
        
        # Inner seal circle
        c.setStrokeColor(cls.NAVY)
        c.setLineWidth(1)
        c.circle(seal_x, seal_y, 26, fill=0, stroke=1)
        
        # Seal Star/Text
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(cls.GOLD)
        c.drawCentredString(seal_x, seal_y + 8, "★ OFFICIAL ★")
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(cls.NAVY)
        c.drawCentredString(seal_x, seal_y - 8, "VERIFIED")

        # 11. Signatures / Metadata Sections (Left: Issue Date, Right: Authorized Signatory)
        # Left: Issue Date
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cls.DARK_GRAY)
        date_str = issue_date.strftime("%B %d, %Y")
        c.drawCentredString(160, height - 425, date_str)
        c.setStrokeColor(cls.MUTED_GRAY)
        c.setLineWidth(1)
        c.line(85, height - 435, 235, height - 435)
        c.setFont("Helvetica", 10)
        c.setFillColor(cls.MUTED_GRAY)
        c.drawCentredString(160, height - 450, "DATE OF ISSUANCE")

        # Right: Issuing Authority
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cls.DARK_GRAY)
        c.drawCentredString(width - 160, height - 425, organization_name)
        c.setStrokeColor(cls.MUTED_GRAY)
        c.setLineWidth(1)
        c.line(width - 235, height - 435, width - 85, height - 435)
        c.setFont("Helvetica", 10)
        c.setFillColor(cls.MUTED_GRAY)
        c.drawCentredString(width - 160, height - 450, "AUTHORIZED SIGNATORY")

        # 12. Bottom Certificate ID / Verification text
        c.setFont("Courier", 9)
        c.setFillColor(cls.MUTED_GRAY)
        c.drawCentredString(width / 2.0, 48, f"Certificate ID: {certificate_id}")
        
        c.showPage()
        c.save()
        
        logger.info("Generated certificate %s for %s at %s", certificate_id, recipient_name, output_path)
        return output_path
