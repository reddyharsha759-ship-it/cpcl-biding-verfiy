import io
from pathlib import Path
from typing import Dict, Optional


def create_standard_pdf(text: str, metadata: Optional[Dict[str, str]] = None) -> bytes:
    """
    Creates a standard, valid PDF 1.4 binary file with extractable text and font dictionary.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    stream_lines = ["BT", "/F1 11 Tf", "40 780 Td", "14 TL"]
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"({escaped}) Tj")
        stream_lines.append("T*")
    stream_lines.append("ET")
    stream_data = "\n".join(stream_lines).encode("latin-1", errors="replace")

    meta_entries = []
    if metadata:
        for k, v in metadata.items():
            escaped_v = str(v).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            meta_entries.append(f"/{k} ({escaped_v})")
    info_dict_content = "\n".join(meta_entries)

    # PDF object construction
    # 1 0 obj: Catalog
    # 2 0 obj: Pages
    # 3 0 obj: Page
    # 4 0 obj: Font
    # 5 0 obj: Contents stream
    # 6 0 obj: Info (Metadata)
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>\nendobj\n"
    obj4 = b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    obj5 = f"5 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("ascii") + stream_data + b"\nendstream\nendobj\n"
    obj6 = f"6 0 obj\n<< {info_dict_content} >>\nendobj\n".encode("latin-1")

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = header
    offsets = []

    for obj in [obj1, obj2, obj3, obj4, obj5, obj6]:
        offsets.append(len(body))
        body += obj

    xref_offset = len(body)
    xref = f"xref\n0 7\n0000000000 65535 f \n".encode("ascii")
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode("ascii")

    trailer = f"trailer\n<< /Size 7 /Root 1 0 R /Info 6 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")

    return body + xref + trailer


def generate_all_fixtures(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Valid MAF
    maf_valid_text = """MANUFACTURER AUTHORIZATION FORM (MAF)
Date of Issue: 15/01/2026
Tender Reference No: GEM/2026/B/998877

To,
The Competent Authority, Government e-Marketplace (GeM)

We, M/s Dell International Services India Private Limited, who are official manufacturers of Enterprise Server Hardware, having factories at Sriperumbudur, Tamil Nadu, do hereby authorize:
M/s Apex Data Solutions Private Limited (Authorized Bidder)
to submit a bid, negotiate and conclude the contract with you against Bid No: GEM/2026/B/998877.

We hereby extend our full guarantee and warranty as per General Conditions of Contract.
This authorization is Valid upto: 31/12/2027.

Yours faithfully,
For Dell International Services India Private Limited
Authorized Signatory: Rajesh V. Sharma (Director - Public Sector)
"""
    (output_dir / "valid_maf.pdf").write_bytes(create_standard_pdf(maf_valid_text, {"Title": "Valid MAF"}))

    # 2. Expired MAF
    maf_expired_text = """MANUFACTURER AUTHORIZATION FORM (MAF)
Date: 10/01/2023
Tender Number: GEM/2026/B/998877

We, M/s Cisco Systems India Private Limited, authorize partner:
M/s Apex Data Solutions Private Limited
to bid against Tender Ref: GEM/2026/B/998877.
Validity Date: 01/01/2024

Authorized Signatory: Amit Verma
For Cisco Systems India Private Limited
"""
    (output_dir / "expired_maf.pdf").write_bytes(create_standard_pdf(maf_expired_text, {"Title": "Expired MAF"}))

    # 3. Mismatched Tender MAF
    maf_mismatch_text = """MANUFACTURER AUTHORIZATION CERTIFICATE
Date: 20/02/2026
Tender No: GEM/2023/B/111111

We, M/s HP India Sales Private Limited, hereby authorize:
M/s Apex Data Solutions Private Limited
for GeM Bid Number: GEM/2023/B/111111.
Valid through: 31/12/2027.

For HP India Sales Private Limited
Authorized Signatory
"""
    (output_dir / "mismatched_tender_maf.pdf").write_bytes(create_standard_pdf(maf_mismatch_text, {"Title": "Mismatched MAF"}))

    # 4. Valid Make in India (Class-I)
    mii_class1_text = """MAKE IN INDIA (MII) SELF DECLARATION
Tender Ref: GEM/2026/B/998877
Entity: Apex Data Solutions Private Limited

In accordance with the Public Procurement (Preference to Make in India) Order, we hereby declare:
1. The percentage of local content is 65.5% (Class-I Local Supplier).
2. Location of local value addition: Plot 42, MIDC Industrial Area, Pune, Maharashtra, India.
3. CA Certified ICAI UDIN: 24012345AAAAAA1234.

Declarant: Suresh Kumar (Managing Director)
"""
    (output_dir / "valid_mii_class1.pdf").write_bytes(create_standard_pdf(mii_class1_text, {"Title": "MII Class 1 Declaration"}))

    # 5. Low Local Content MII (Non-Local)
    mii_low_text = """LOCAL CONTENT COMPLIANCE DECLARATION
Tender Ref: GEM/2026/B/998877

We declare that:
The local content percentage is 15.0%
Location of manufacturing: Foreign Assembly Facility
Classification: Non-Local Supplier (< 20%)

Authorized Representative: John Doe
"""
    (output_dir / "low_local_content_mii.pdf").write_bytes(create_standard_pdf(mii_low_text, {"Title": "Low Local Content MII"}))

    # 6. Valid CA Financial Turnover Certificate
    ca_valid_text = """TO WHOMSOEVER IT MAY CONCERN
ANNUAL TURNOVER & NET WORTH CERTIFICATE

This is to certify that M/s Apex Data Solutions Private Limited, having PAN: ABCDE1234F, has achieved annual turnover and net worth as follows:
- FY 2022-23: INR 10.5 Crore
- FY 2023-24: INR 12.0 Crore
- FY 2024-25: INR 15.0 Crore

The Average Annual Turnover for the trailing 3 financial years is INR 12.5 Crore.
The Net Worth as on March 31, 2025 is INR 8.5 Crore (Positive).

UDIN: 24098765BBBBBB4321
For M/s Sharma & Associates Chartered Accountants
FRN: 109876W
CA Anil Sharma (Partner, Membership No: 098765)
"""
    (output_dir / "valid_turnover_ca_cert.pdf").write_bytes(create_standard_pdf(ca_valid_text, {"Title": "Valid CA Turnover Certificate"}))

    # 7. Insufficient Turnover CA Certificate
    ca_low_text = """CHARTERED ACCOUNTANTS TURNOVER CERTIFICATE
Entity: Apex Small Enterprises

Annual Turnover:
- FY 2022-23: INR 1.0 Crore
- FY 2023-24: INR 1.2 Crore
- FY 2024-25: INR 1.4 Crore
Average Annual Turnover: INR 1.2 Crore
Net Worth: INR 0.5 Crore
UDIN: 24112233CCCCCC7890

For M/s Gupta & Co Chartered Accountants
"""
    (output_dir / "insufficient_turnover_ca_cert.pdf").write_bytes(create_standard_pdf(ca_low_text, {"Title": "Insufficient Turnover CA Certificate"}))

    # 8. Scanned PDF with OCR Fallback
    scanned_text = "   "  # Empty text stream to simulate scanned non-searchable document
    ocr_fallback = """OCR_FALLBACK_TEXT:
MANUFACTURER AUTHORIZATION FORM (MAF)
Date of Issue: 10/02/2026
Tender Reference No: GEM/2026/B/998877
We, M/s Lenovo India Private Limited, authorize M/s Apex Data Solutions Private Limited.
Valid upto: 31/12/2027.
Authorized Signatory: Vikram Seth
"""
    (output_dir / "scanned_sample.pdf").write_bytes(create_standard_pdf(scanned_text, {"Keywords": ocr_fallback, "Title": "Scanned MAF"}))

    print(f"Generated 8 test PDF fixtures in {output_dir}")


if __name__ == "__main__":
    generate_all_fixtures(Path(__file__).parent)
