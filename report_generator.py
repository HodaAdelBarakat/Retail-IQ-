from fpdf import FPDF
import pandas as pd
from datetime import datetime

# إعدادات الألوان للهوية البصرية
DARK_BLUE = (15, 23, 42)
LIGHT_BLUE = (56, 189, 248)
RED = (239, 68, 68)
GREEN = (16, 185, 129)
GREY = (100, 116, 139)
BLACK = (0, 0, 0)
TABLE_HEADER_BLUE = (0, 51, 102)

class RetailIQReport(FPDF):
    def header(self):
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 35, 'F')
        
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(255, 255, 255)
        self.set_y(10)
        self.cell(190, 15, "RetailIQ Executive Audit Report", border=0, ln=1, align="C")
        
        self.set_font("Helvetica", "", 10)
        self.cell(190, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", border=0, ln=1, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential - RetailIQ AI Financial Engine", align="C")

    def section_title(self, title):
        self.ln(5)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*DARK_BLUE)
        self.set_fill_color(240, 244, 248)
        self.cell(190, 10, f"  {title}", ln=1, align="L", fill=True)
        self.ln(3)

def clean_text(text):
    if not isinstance(text, str): return str(text)
    return text.encode('ascii', 'ignore').decode('ascii')

def create_pdf_report(kpis, executive_orders_en, financial_impact, anomalies, forecast_df, detailed_decisions=None):
    pdf = RetailIQReport()
    pdf.add_page()
    
    # --------------------------------------------------------
    # 1. Executive Financial Summary
    # --------------------------------------------------------
    pdf.section_title("1. Executive Financial Summary")
    
    col_width = 63 # تقسيم العرض لـ 3 أعمدة
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BLACK)
    
    # الصف الأول: المبيعات - التكلفة - الربح الإجمالي
    pdf.cell(col_width, 7, "Total Sales:")
    pdf.cell(col_width, 7, "Total Cost (COGS):")
    pdf.cell(col_width, 7, "Total Gross Profit:", ln=1)
    
    pdf.set_font("Helvetica", "", 10)
    t_sales = kpis.get('Total Sales', 0)
    t_profit = kpis.get('Total Profit', 0)
    t_cost = t_sales - t_profit
    
    pdf.cell(col_width, 7, f"${t_sales:,.2f}")
    pdf.cell(col_width, 7, f"${t_cost:,.2f}")
    pdf.cell(col_width, 7, f"${t_profit:,.2f}", ln=1)
    pdf.ln(3)

    # الصف الثاني: الهامش - صافي الربح - النزيف المالي
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_width, 7, "Profit Margin:")
    pdf.cell(col_width, 7, "Net Profit (After Tax):")
    pdf.cell(col_width, 7, "Recoverable Leakage:", ln=1)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_width, 7, f"{kpis.get('Profit Margin', 0):.2%}")
    pdf.cell(col_width, 7, f"${kpis.get('Net Profit After Tax', 0):,.2f}")
    
    pdf.set_text_color(*RED) # تلوين النزيف بالأحمر
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_width, 7, f"${financial_impact:,.2f}", ln=1)
    pdf.set_text_color(*BLACK) # إرجاع اللون الأسود
    pdf.ln(5)

    # --------------------------------------------------------
    # 2. Critical Risk: Financial Leakage
    # --------------------------------------------------------
    pdf.section_title("2. Critical Risk: Financial Leakage")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*RED)
    pdf.cell(190, 8, f"TOTAL RECOVERABLE LEAKAGE: ${financial_impact:,.2f}", ln=1)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*BLACK)
    pdf.multi_cell(190, 6, f"The AI engine has identified {len(anomalies)} anomalous transactions that deviate from standard profit norms. These records indicate potential pricing errors or operational inefficiency.")
    pdf.ln(3)

    if not anomalies.empty:
        pdf.set_fill_color(*DARK_BLUE)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        
        pdf.cell(40, 8, "Order ID", border=1, fill=True)
        pdf.cell(70, 8, "Product Name", border=1, fill=True)
        pdf.cell(30, 8, "Sales", border=1, fill=True)
        pdf.cell(30, 8, "Profit", border=1, fill=True)
        pdf.cell(20, 8, "Disc%", border=1, ln=1, fill=True)
        
        pdf.set_text_color(*BLACK)
        pdf.set_font("Helvetica", "", 8)
        for _, row in anomalies.head(15).iterrows():
            pdf.cell(40, 7, str(row['Order ID']), border=1)
            pdf.cell(70, 7, clean_text(str(row['Product Name'])[:35]), border=1)
            pdf.cell(30, 7, f"${row['Sales']:,.2f}", border=1)
            pdf.cell(30, 7, f"${row['Profit']:,.2f}", border=1)
            pdf.cell(20, 7, f"{row['Discount']:.0%}", border=1, ln=1)

    # --------------------------------------------------------
    # 3. Future Forecasting (6 Months)
    # --------------------------------------------------------
    pdf.section_title("3. Sales Forecast")
    
    if not forecast_df.empty:
        pdf.set_fill_color(*TABLE_HEADER_BLUE)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        
        pdf.cell(95, 8, "Month", border=1, fill=True, align="C")
        pdf.cell(95, 8, "Forecasted Value", border=1, ln=1, fill=True, align="C")
        
        pdf.set_text_color(*BLACK)
        pdf.set_font("Helvetica", "B", 9)
        
        for idx, row in forecast_df.iterrows():
            try:
                date_str = idx.strftime('%B %Y')
            except AttributeError:
                date_str = str(idx)[:10]
                
            val_str = f"${row['Forecast Sales']:,.2f}"
            
            pdf.cell(95, 8, date_str, border=1, align="C")
            pdf.cell(95, 8, val_str, border=1, ln=1, align="C")
            
        pdf.ln(5)

    # --------------------------------------------------------
    # 4. Administrative Action Plan
    # --------------------------------------------------------
   pdf.add_page()
    pdf.section_title("4. Administrative Action Plan")
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*RED)
    pdf.cell(190, 8, "I. General Strategic Directive:", ln=1)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*BLACK)
    if executive_orders_en:
        for order in executive_orders_en.split(" | "):
            pdf.set_x(10)
            pdf.multi_cell(190, 6, f"- {clean_text(order)}")
    
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(190, 8, "II. Specific Invoice-Level Decisions (Mandatory Audit):", ln=1)
    
    pdf.set_font("Helvetica", "", 9)
    
    if detailed_decisions:
        for dec in detailed_decisions:
            pdf.set_x(10)
            dec_text = clean_text(dec)
            dec_lower = dec_text.lower()
            
            # 🔥 التلوين الديناميكي للقرارات بناءً على الحالة (خسارة/ربح)
            if any(word in dec_lower for word in ["loss", "leakage", "halt", "revoke", "dead", "trap", "phantom", "severe"]):
                pdf.set_text_color(*RED)
            elif any(word in dec_lower for word in ["growth", "healthy", "excellent"]):
                pdf.set_text_color(*GREEN)
            else:
                pdf.set_text_color(*BLACK)
                
            pdf.multi_cell(190, 6, f"* {dec_text}")
            pdf.ln(2)
    else:
        pdf.set_text_color(*BLACK)
        pdf.cell(190, 8, "No specific invoice-level interventions required at this stage.", ln=1)

    # --------------------------------------------------------
    # الحل السحري للإيرور
    # --------------------------------------------------------
    output = pdf.output(dest='S')
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    return output.encode('latin-1', errors='replace')
