import reflex as rx
from datetime import datetime
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from .pages import cms_rows

def root(request: Request):
    return JSONResponse({"message": "hello from reflex"})

def get_lastmod_date(row_data):
    """Try to extract lastmod date from CMS row, default to current date"""
    date_fields = [
        "Last Page Update",
        "Last Price Update",
        "Last Price Update - Human",
    ]
    for field in date_fields:
        date_str = row_data.get(field)
        if date_str:
            try:
                if isinstance(date_str, str) and "T" in date_str:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if isinstance(date_str, str) and len(date_str) >= 10:
                    return datetime.strptime(date_str[:10], "%Y-%m-%d")
            except (ValueError, AttributeError):
                pass
    return datetime.now()

def sitemap(request: Request):
    """Generate sitemap.xml with weekly changefreq and lastmod dates"""
    base_url = "https://www.priceduck.co.za"
    now = datetime.now().strftime("%Y-%m-%d")
    
    # Start building XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    
    # Homepage
    xml_lines.append("  <url>")
    xml_lines.append(f"    <loc>{base_url}/</loc>")
    xml_lines.append(f"    <lastmod>{now}</lastmod>")
    xml_lines.append("    <changefreq>weekly</changefreq>")
    xml_lines.append("    <priority>1.0</priority>")
    xml_lines.append("  </url>")
    
    # CMS pages
    for row in cms_rows:
        slug = (row.get("Slug") or "").strip()
        if not slug:
            continue
        
        route = "/" + slug.lstrip("/")
        lastmod_date = get_lastmod_date(row)
        lastmod_str = lastmod_date.strftime("%Y-%m-%d")
        
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{base_url}{route}</loc>")
        xml_lines.append(f"    <lastmod>{lastmod_str}</lastmod>")
        xml_lines.append("    <changefreq>weekly</changefreq>")
        xml_lines.append("    <priority>0.8</priority>")
        xml_lines.append("  </url>")
    
    xml_lines.append("</urlset>")
    
    xml_content = "\n".join(xml_lines)
    
    return Response(content=xml_content, media_type="application/xml")