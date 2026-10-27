"""Reconstruction prudente du rapport PDF individuel de caisse (V5.9)."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generer_rapport_caisse(session_data, rectifications):
    """Construit un PDF en mémoire, sans écrire dans la base de données."""
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=(595, 842), leftMargin=38, rightMargin=38)
    styles = getSampleStyleSheet()
    styles['Title'].alignment = TA_CENTER
    elements = [Paragraph('BOUKOULOU TRANSPORT', styles['Title']),
                Paragraph('Rapport de clôture de caisse', styles['Heading2']), Spacer(1, 12)]
    # Ne jamais interpoler du HTML non échappé dans un paragraphe ReportLab.
    rows = [['Champ', 'Valeur']]
    for key, value in session_data.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append([Paragraph(escape(str(key)), styles['BodyText']),
                         Paragraph(escape(str(value if value is not None else '—')), styles['BodyText'])])
    table = Table(rows, colWidths=[220, 290], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17365D')),
                               ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                               ('VALIGN',(0,0),(-1,-1),'TOP'),
                               ('BOTTOMPADDING',(0,0),(-1,-1),7),
                               ('LINEBELOW',(0,0),(-1,-1),.25,colors.lightgrey)]))
    elements.extend([table, Spacer(1,18),Paragraph('Historique des rectifications',styles['Heading2'])])
    if not rectifications:
        elements.append(Paragraph('Aucune rectification enregistrée.', styles['BodyText']))
    for i, r in enumerate(rectifications, 1):
        elements.append(Paragraph(f'Rectification {i}', styles['Heading3']))
        for key in ('created_at','old_declared_amount','new_declared_amount','old_difference_amount','new_difference_amount','reason'):
            if key in r:
                elements.append(Paragraph(f'<b>{escape(key)} :</b> {escape(str(r[key]))}', styles['BodyText']))
    document.build(elements)
    stream.seek(0)
    return stream
