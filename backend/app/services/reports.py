from pathlib import Path
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.graphics.shapes import Drawing,Line,Circle,String
from app.core.config import ROOT

LABELS={
 'en':{'title':'Soil laboratory record','farm':'Farm','sample':'Sample ID','date':'Collection date','laboratory':'Laboratory','parameter':'Parameter','value':'Value','unit':'Unit','method':'Test method','measurements':'Recorded soil measurements','limitations':'Interpretation and limitations','unavailable':'No validated prediction is available. These values are laboratory records, not a scientifically validated soil-health score.','fertilizer':'Fertilizer dosage must follow a local agricultural extension officer or accredited laboratory recommendation. No dosage has been calculated.','remarks':'Agricultural officer remarks','none':'No remarks recorded.','owner':'Owner','location':'Location','status':'Status','report':'Report ID'},
 'ta':{'title':'மண் ஆய்வகப் பதிவு','farm':'பண்ணை','sample':'மாதிரி எண்','date':'சேகரித்த தேதி','laboratory':'ஆய்வகம்','parameter':'அளவுரு','value':'மதிப்பு','unit':'அலகு','method':'சோதனை முறை','measurements':'பதிவு செய்யப்பட்ட மண் அளவீடுகள்','limitations':'விளக்கம் மற்றும் வரம்புகள்','unavailable':'சரிபார்க்கப்பட்ட கணிப்பு கிடைக்கவில்லை. இவை ஆய்வகப் பதிவுகள் மட்டுமே. மண் வள மதிப்பீடு அல்ல.','fertilizer':'உர அளவுகளை உள்ளூர் வேளாண் அலுவலர் அல்லது அங்கீகரிக்கப்பட்ட ஆய்வகத்தின் ஆலோசனைப்படி பயன்படுத்தவும். உர அளவு கணக்கிடப்படவில்லை.','remarks':'வேளாண் அலுவலர் குறிப்புகள்','none':'குறிப்புகள் பதிவு செய்யப்படவில்லை.','owner':'உரிமையாளர்','location':'இடம்','status':'நிலை','report':'அறிக்கை எண்'},
}
PARAMETER_TA={'nitrogen':'நைட்ரஜன்','phosphorus':'பாஸ்பரஸ்','potassium':'பொட்டாசியம்','ph':'மண் pH','ec':'மின் கடத்துத்திறன்','organic_carbon':'கரிம கார்பன்','organic_matter':'கரிமப் பொருள்','moisture':'ஈரப்பதம்','temperature':'வெப்பநிலை','sulphur':'கந்தகம்','zinc':'துத்தநாகம்','iron':'இரும்பு','boron':'போரான்','copper':'தாமிரம்','manganese':'மாங்கனீசு','calcium':'கால்சியம்','magnesium':'மக்னீசியம்'}

# Opaque, print-friendly equivalents of the app's blue glass / grey / white theme.
PDF_PALETTE={
    'text':colors.HexColor('#425675'),
    'heading':colors.HexColor('#245da8'),
    'brand':colors.HexColor('#326bc5'),
    'muted':colors.HexColor('#647b97'),
    'surface':colors.HexColor('#edf3fb'),
    'table_header':colors.HexColor('#dce9fb'),
    'table_alternate':colors.HexColor('#f4f7fc'),
    'border':colors.HexColor('#c9d8ec'),
    'chart_track':colors.HexColor('#dbe5f3'),
    'chart_tick':colors.HexColor('#8eabc8'),
    'chart_marker':colors.HexColor('#397bd6'),
}


def report_font():
    path=ROOT/'app'/'assets'/'fonts'/'SoilAI-Regular.ttf'
    if not path.exists():
        raise ValueError('Report font missing. Run scripts/install_fonts.py before generating reports.')
    if 'SoilAI' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('SoilAI',str(path),shapable=True))
    return 'SoilAI'


def generate_pdf(path,report_id,language,sample,farm,owner,measurements,reviews):
    font=report_font()
    text=LABELS[language]
    body=ParagraphStyle('Body',fontName=font,fontSize=9,leading=14,textColor=PDF_PALETTE['text'],spaceAfter=0,alignment=TA_LEFT,shaping=True)
    heading=ParagraphStyle('Heading',parent=body,fontSize=14,leading=23,spaceBefore=18,spaceAfter=12,textColor=PDF_PALETTE['heading'])
    title=ParagraphStyle('Title',parent=heading,fontSize=23,leading=33,spaceBefore=0,textColor=PDF_PALETTE['brand'])
    caption=ParagraphStyle('Caption',parent=body,fontSize=7,leading=12,textColor=PDF_PALETTE['muted'])
    def paragraph(value,style=body):
        return Paragraph(escape(str(value)),style)
    story=[paragraph('SoilAI',title),paragraph(text['title'],heading),paragraph(f"{text['report']}: {report_id}",caption),Spacer(1,15)]
    info=[(text['farm'],farm.name),(text['owner'],owner.name),(text['location'],', '.join(filter(None,[farm.village,farm.district,farm.state]))),(text['sample'],sample.sample_code),(text['date'],sample.collected_on),(text['laboratory'],sample.laboratory or '-'),(text['status'],sample.status)]
    info_table=Table([[paragraph(label),paragraph(value)] for label,value in info],colWidths=[130,365],hAlign='LEFT')
    info_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),PDF_PALETTE['surface']),('BOX',(0,0),(-1,-1),.4,PDF_PALETTE['border']),('LEFTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([info_table,paragraph(text['measurements'],heading)])
    rows=[[paragraph(text[k]) for k in ['parameter','value','unit','method']]]
    for m in measurements:
        label=PARAMETER_TA.get(m.parameter,m.parameter) if language=='ta' else m.parameter.replace('_',' ').title()
        rows.append([paragraph(label),paragraph(f'{m.value:g}'),paragraph(m.unit),paragraph(m.method)])
    if len(rows)==1:
        rows.append([paragraph('-') for _ in range(4)])
    table=Table(rows,colWidths=[140,60,65,230],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),PDF_PALETTE['table_header']),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PDF_PALETTE['table_alternate']]),('LINEBELOW',(0,0),(-1,0),.5,PDF_PALETTE['border']),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(table)
    ph=next((m for m in measurements if m.parameter=='ph' and m.unit=='pH'),None)
    if ph:
        chart=Drawing(495,70)
        chart.add(Line(15,35,480,35,strokeColor=PDF_PALETTE['chart_track'],strokeWidth=5))
        for tick in [0,7,14]:
            x=15+465*tick/14
            chart.add(Line(x,28,x,42,strokeColor=PDF_PALETTE['chart_tick']))
            chart.add(String(x,12,str(tick),fontName=font,fontSize=8,textAnchor='middle',fillColor=PDF_PALETTE['muted']))
        chart.add(Circle(15+465*ph.value/14,35,5,fillColor=PDF_PALETTE['chart_marker'],strokeColor=colors.white))
        story.append(KeepTogether([paragraph(('pH measurement: ' if language=='en' else 'மண் pH அளவீடு: ')+str(ph.value),heading),chart,paragraph('Scale only; not a fertility classification.' if language=='en' else 'அளவுகோல் மட்டுமே; மண் வள வகைப்பாடு அல்ல.',caption)]))
    story.append(KeepTogether([paragraph(text['limitations'],heading),paragraph(text['unavailable']),Spacer(1,7),paragraph(text['fertilizer'])]))
    story.append(KeepTogether([paragraph(text['remarks'],heading),paragraph(reviews[0].remarks if reviews else text['none'])]))
    for review in reviews[1:]:
        story.append(paragraph(review.remarks))
    def footer(canvas,doc):
        canvas.setStrokeColor(PDF_PALETTE['border']);canvas.line(50,40,545,40)
        canvas.setFont(font,7);canvas.setFillColor(PDF_PALETTE['muted'])
        canvas.drawString(50,26,'SoilAI | Laboratory record | '+report_id[:8]);canvas.drawRightString(545,26,str(doc.page))
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=50,leftMargin=50,topMargin=40,bottomMargin=60,title='SoilAI - '+sample.sample_code,author='SoilAI')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)


def generate_xlsx(path,language,sample,farm,owner,measurements,reviews):
    text=LABELS[language]
    workbook=Workbook();sheet=workbook.active;sheet.title='SoilAI'
    sheet.append(['SoilAI',text['title']]);sheet.append([text['farm'],farm.name]);sheet.append([text['owner'],owner.name]);sheet.append([text['sample'],sample.sample_code]);sheet.append([text['date'],sample.collected_on]);sheet.append([])
    sheet.append([text[k] for k in ['parameter','value','unit','method']])
    def literal(value):
        value=str(value)
        return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value
    for m in measurements:
        sheet.append([PARAMETER_TA.get(m.parameter,m.parameter) if language=='ta' else m.parameter,m.value,m.unit,literal(m.method)])
    sheet.append([]);sheet.append([text['unavailable']]);sheet.append([text['fertilizer']]);sheet.append([text['remarks']])
    for review in reviews:
        sheet.append([literal(review.remarks)])
    # All external string cells are forced to strings, preventing formula injection.
    for row in sheet:
        for cell in row:
            if isinstance(cell.value,str):
                cell.data_type='s'
            cell.alignment=Alignment(vertical='top',wrap_text=True)
            cell.font=Font(name='Nirmala UI',size=11,color='244B35')
    for row_index in [1,7]:
        for cell in sheet[row_index]:
            cell.fill=PatternFill('solid',fgColor='E1ECDA');cell.font=Font(name='Nirmala UI',bold=True,size=12,color='244B35')
    for col,width in {'A':30,'B':22,'C':18,'D':65}.items():sheet.column_dimensions[col].width=width
    sheet.freeze_panes='A8';sheet.auto_filter.ref=f'A7:D{7+len(measurements)}'
    workbook.save(path)
