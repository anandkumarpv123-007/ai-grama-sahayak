"""Generate Synthetic Test Sample Documents for AI Grama Sahayak.

Generates completely synthetic documents for automated testing.
ZERO personal or real citizen data is included.
"""

import os
from PIL import Image, ImageDraw, PngImagePlugin


def make_pdf(text_lines, is_scanned=False):
    """Construct a synthetic PDF 1.4 binary file."""
    if is_scanned:
        # Scanned dummy: has an Image XObject and empty stream (no text)
        image_stream = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\xff\xd9"
        objects = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /XObject << /Im1 5 0 R >> >> >>\nendobj\n",
            b"4 0 obj\n<< /Length 0 >>\nstream\n\nendstream\nendobj\n",
            f"5 0 obj\n<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length {len(image_stream)} >>\nstream\n".encode("latin1")
            + image_stream
            + b"\nendstream\nendobj\n",
        ]
    else:
        stream_content = "BT /F1 12 Tf 50 750 Td\n"
        for line in text_lines:
            safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_content += f"({safe_line}) Tj T*\n"
        stream_content += "ET"
        stream_bytes = stream_content.encode("latin1")

        objects = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
            f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1")
            + stream_bytes
            + b"\nendstream\nendobj\n",
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        ]

    header = b"%PDF-1.4\n"
    body = b""
    xref = [0]
    pos = len(header)
    for obj in objects:
        xref.append(pos)
        pos += len(obj)
        body += obj

    xref_table = f"xref\n0 {len(xref)}\n0000000000 65535 f \n".encode("latin1")
    for offset in xref[1:]:
        xref_table += f"{offset:010d} 00000 n \n".encode("latin1")

    trailer = f"trailer\n<< /Size {len(xref)} /Root 1 0 R >>\nstartxref\n{pos}\n%%EOF\n".encode("latin1")
    return header + body + xref_table + trailer


def make_png_image(filepath, text_meta=None):
    """Generate a clean synthetic PNG image with optional text metadata."""
    img = Image.new("RGB", (400, 200), color=(240, 248, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 390, 190], outline=(70, 130, 180), width=2)
    draw.text((30, 30), "SYNTHETIC SAMPLE DOCUMENT", fill=(0, 51, 102))

    meta = PngImagePlugin.PngInfo()
    if text_meta:
        for k, v in text_meta.items():
            meta.add_text(k, v)
        img.save(filepath, "PNG", pnginfo=meta)
    else:
        img.save(filepath, "PNG")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Synthetic Income Certificate PDF
    income_pdf = make_pdf([
        "GOVERNMENT OF ANDHRA PRADESH - REVENUE DEPARTMENT",
        "MEESEVA CITIZEN SERVICES",
        "INCOME CERTIFICATE",
        "Certificate No: IC0123456789",
        "This is to certify that Sri K. Rama Rao, S/o K. Venkata Rao",
        "resident of Samalkota, Kakinada District.",
        "The annual income of the family from all sources is Rs. 75,000/-",
        "Date of Issue: 2026-01-10",
        "Issued by: Tahsildar, Kakinada District",
    ])
    with open(os.path.join(base_dir, "synthetic_income_certificate.pdf"), "wb") as f:
        f.write(income_pdf)

    # 2. Synthetic Caste Certificate PDF
    caste_pdf = make_pdf([
        "GOVERNMENT OF ANDHRA PRADESH - REVENUE DEPARTMENT",
        "COMMUNITY, NATIVITY AND DATE OF BIRTH CERTIFICATE",
        "Certificate No: CGC9876543210",
        "This is to certify that Smt P. Lakshmi, D/o P. Appa Rao",
        "belongs to BC-A community in Visakhapatnam District.",
        "Mandal: Visakhapatnam Urban",
        "Date: 2026-02-15",
    ])
    with open(os.path.join(base_dir, "synthetic_caste_certificate.pdf"), "wb") as f:
        f.write(caste_pdf)

    # 3. Synthetic Ration Card PDF
    ration_pdf = make_pdf([
        "GOVERNMENT OF ANDHRA PRADESH - FOOD & CIVIL SUPPLIES",
        "RICE CARD (FOOD SECURITY CARD)",
        "Rice Card No: WAP041234567890",
        "Head of the Family: M. Subba Rao",
        "District: Guntur",
        "Issue Date: 2026-01-05",
    ])
    with open(os.path.join(base_dir, "synthetic_ration_card.pdf"), "wb") as f:
        f.write(ration_pdf)

    # 4. Synthetic Scanned (Unreadable) PDF
    scanned_pdf = make_pdf([], is_scanned=True)
    with open(os.path.join(base_dir, "synthetic_scanned_unreadable.pdf"), "wb") as f:
        f.write(scanned_pdf)

    # 5. Synthetic PNG with metadata
    make_png_image(
        os.path.join(base_dir, "synthetic_income_cert.png"),
        text_meta={
            "Certificate Number": "IC0998877665",
            "Applicant Name": "G. Suresh",
            "Annual Income": "Rs. 60,000/-",
            "District": "Kakinada",
            "Date": "2026-02-01",
        },
    )

    # 6. Blank PNG
    make_png_image(os.path.join(base_dir, "synthetic_blank.png"))

    # 7. Invalid text file
    with open(os.path.join(base_dir, "synthetic_invalid.txt"), "w", encoding="utf-8") as f:
        f.write("This is a plain text file, not an allowed document type.\n")

    print("Synthetic test samples generated successfully in", base_dir)


if __name__ == "__main__":
    main()
