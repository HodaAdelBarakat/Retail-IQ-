import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from utils_ import format_currency, format_percentage
from analysis_final import build_analysis_bundle
from ai_engine import run_full_ai_analysis, get_decisions
from report_generator import create_pdf_report
import warnings

warnings.filterwarnings("ignore")

# ============================================================
# إعدادات الصفحة والهوية البصرية
# ============================================================
st.set_page_config(page_title="RetailIQ ", layout="wide", page_icon="🛒📈")

if "lang" not in st.session_state: 
    st.session_state.lang = "العربية"

is_ar = st.session_state.lang == "العربية"
direction = "rtl" if is_ar else "ltr"

# فرض الهوية البصرية (Dark Navy) على كامل التطبيق بغض النظر عن إعدادات المتصفح
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* {{ font-family: 'Cairo', sans-serif; direction: {direction}; }}

/* توحيد الخلفية باللون الأزرق الكحلي الفخم */
.stApp, .main, [data-testid="stHeader"] {{ background-color: #0F172A !important; color: #F8FAFC !important; }}

/* كروت المؤشرات */
[data-testid="stMetric"] {{ background-color: #1E293B !important; border-radius: 15px !important; padding: 20px !important; border: 1px solid #334155 !important; text-align: center; }}
[data-testid="stMetricLabel"] {{ color: #CBD5E1 !important; font-size: 1.1rem !important; }}
[data-testid="stMetricValue"] {{ font-size: 2.2rem !important; color: #38BDF8 !important; font-weight: 900 !important; }}

/* كروت القرارات والبانر */
.decision-card {{ background: #1E293B; padding: 15px; border-radius: 10px; border-left: 6px solid #EF4444; margin-bottom: 12px; }}
.recovery-banner {{ background: linear-gradient(90deg, #7F1D1D 0%, #B91C1C 100%); padding: 20px; border-radius: 15px; text-align: center; color: white; font-weight: bold; font-size: 1.5rem; margin-bottom: 25px; }}

/* تعديل شكل التابات والقائمة الجانبية */
button[data-baseweb="tab"] {{ color: #94A3B8 !important; }}
button[aria-selected="true"] {{ color: #38BDF8 !important; border-bottom-color: #38BDF8 !important; font-weight: bold !important; }}
[data-testid="stSidebar"] {{ background-color: #1E293B !important; border-right: 1px solid #334155 !important; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# القائمة الجانبية (Sidebar)
# ============================================================
st.sidebar.title("🛒📈 RetailIQ ")
lang = st.sidebar.radio("Language / اللغة", ["English", "العربية"], index=1 if is_ar else 0)
if lang != st.session_state.lang:
    st.session_state.lang = lang
    st.rerun()

# تهيئة الذاكرة لحفظ البيانات
if "bundle_data" not in st.session_state: st.session_state.bundle_data = None
if "ai_data" not in st.session_state: st.session_state.ai_data = None
if "last_file_name" not in st.session_state: st.session_state.last_file_name = None

file = st.sidebar.file_uploader("📂 Upload Financial Data", type=['csv', 'xlsx'])

# معالجة الملف فقط إذا كان جديداً (تجنب إعادة المعالجة عند تغيير اللغة)
if file is not None:
    if st.session_state.last_file_name != file.name:
        with st.spinner("⚡ جاري التحليل..." if is_ar else "⚡ Processing..."):
            new_bundle = build_analysis_bundle(file)
            if "error" in new_bundle:
                st.error(new_bundle["error"])
                st.stop()
            new_ai = run_full_ai_analysis(new_bundle["cleaned_data"])
            
            # حفظ النتائج في الذاكرة
            st.session_state.bundle_data = new_bundle
            st.session_state.ai_data = new_ai
            st.session_state.last_file_name = file.name

if st.session_state.bundle_data is None:
    st.info("👋 يرجى رفع ملف البيانات لتفعيل محرك المدير المالي." if is_ar else "👋 Please upload your sales data to activate the CFO Engine.")
    st.stop()

# استرجاع البيانات من الذاكرة
bundle = st.session_state.bundle_data
ai = st.session_state.ai_data

# ============================================================
# ⚠️ استخراج المتغيرات بأمان (هنا كان سبب الإيرور وتم حله)
# ============================================================
kpis = bundle.get("kpis", {})
cat_sum = bundle.get("category_summary", pd.DataFrame())
vips = bundle.get("vip_customers", pd.DataFrame())
worst = bundle.get("worst_products", pd.DataFrame())
tax_table = bundle.get("tax_audit_table", pd.DataFrame())

monthly = ai.get("monthly_sales", pd.DataFrame())
forecast_df = ai.get("forecast_df", pd.DataFrame())
df_z = ai.get("df_with_zscore", pd.DataFrame())
anomalies = ai.get("anomalies", pd.DataFrame())
df_tax = ai.get("df_with_tax", pd.DataFrame())
strategy = ai.get("strategy", {})
recovery = ai.get('total_potential_recovery', 0)

# ============================================================
# التابات (Tabs)
# ============================================================
t1, t2, t3, t4 = st.tabs(["📊 النبض المالي", "🧠 التشخيص والاستراتيجية", "💡 القرارات", "👔 المدير المالي"] if is_ar else ["📊 Pulse", "🧠 Diagnostics & Strategy", "💡 Decisions", "👔 CFO"])

# --- TAB 1: Pulse ---
with t1:
    st.markdown(f"### {'📈 النبض التنفيذي والمؤشرات الرئيسية' if is_ar else '📈 Executive Pulse & KPIs'}")
    st.info("💡 **لوحة القيادة:** نظرة عامة سريعة على صحة أعمالك المالية، موقف الضرائب، وأفضل وأسوأ العناصر المؤثرة على الإيرادات." if is_ar else "💡 **Dashboard:** A quick overview of your financial health, tax standing, and top/worst revenue drivers.")
    
    # ----------------------------------------------------
    # 1. المؤشرات المالية والضريبية (KPIs)
    # ----------------------------------------------------
    st.markdown(f"#### {'💰 المؤشرات المالية الأساسية' if is_ar else '💰 Core Financials'}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي المبيعات" if is_ar else "Total Sales", format_currency(kpis.get("Total Sales", 0)))
    c2.metric("إجمالي الأرباح" if is_ar else "Total Profit", format_currency(kpis.get("Total Profit", 0)))
    c3.metric("هامش الربح" if is_ar else "Profit Margin", format_percentage(kpis.get("Profit Margin", 0)))
    c4.metric("سرعة الطلبات" if is_ar else "Order Velocity", f"{kpis.get('Order Velocity', 0)} /Day")

    st.markdown(f"#### {'⚖️ مؤشرات الضرائب وصافي الدخل' if is_ar else '⚖️ Tax & Net Income'}")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("الربح الصافي (بعد الضريبة)" if is_ar else "Net Profit (After Tax)", format_currency(kpis.get("Net Profit After Tax", 0)))
    c6.metric("إجمالي الضريبة" if is_ar else "Total VAT", format_currency(kpis.get("Total VAT", 0)))
    c7.metric("ضريبة الدخل" if is_ar else "Income Tax", format_currency(kpis.get("Total Income Tax", 0)))
    c8.metric("فواتير مشبوهة" if is_ar else "Tax Suspicious", f"{kpis.get('Tax Suspicious Count', 0)} ⚠️")

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 2. أداء الفئات (Category Performance)
    # ----------------------------------------------------
    st.markdown(f"### {'🏆 أداء الفئات التشغيلية' if is_ar else '🏆 Category Performance'}")
    if not cat_sum.empty:
        # توحيد الألوان لتدريج الأزرق إلى الأحمر
        fig_cat = px.bar(cat_sum, x='Total_Sales', y='Category', orientation='h',  
                                                                color='Total_Profit', 
                                                                text='Total_Sales', 
                                                                color_continuous_scale=['#EF4444', '#38BDF8'], # أحمر للخسارة وأزرق للربح
                                                                template='plotly_dark',
                                                                labels={"Total_Sales": "المبيعات" if is_ar else "Sales", "Category": "الفئة" if is_ar else "Category","Total_Profit": "الربح" if is_ar else "Profit"})
        
        fig_cat.update_traces(texttemplate='%{text:,.0f}', textposition='outside', textfont_color='white')
        fig_cat.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0), plot_bgcolor='#0F172A', paper_bgcolor='#0F172A')
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 3. كبار العملاء (تحت بعض)
    # ----------------------------------------------------
    st.markdown(f"### {'⭐ كبار العملاء (Pareto 80/20)' if is_ar else '⭐ VIP Customers (Pareto 80/20)'}")
    st.success("💡 **قاعدة باريتو:** هؤلاء هم أهم 10 عملاء يمثلون النسبة الأكبر من إيراداتك. يجب الحفاظ على ولائهم وتقديم خدمات مميزة لهم." if is_ar else "💡 **Pareto Rule:** Top 10 clients driving the majority of revenue. Maintain their loyalty.")
    if not vips.empty:
        st.dataframe(vips.head(10), use_container_width=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 4. المنتجات النازفة (تحت بعض)
    # ----------------------------------------------------
    st.markdown(f"### {'🩸 المنتجات النازفة (الخاسرة)' if is_ar else '🩸 Bleeding Products (Loss)'}")
    st.error("💡 **تنبيه الإدارة:** أكثر 10 منتجات تستنزف أرباحك حالياً. تتطلب مراجعة فورية لسياسة التسعير أو تكلفة الشراء." if is_ar else "💡 **Alert:** Top 10 profit-draining products. Requires immediate repricing or cost review.")
    if not worst.empty:
        st.dataframe(worst.head(10), use_container_width=True)
with t2:
    # ----------------------------------------------------
    # 1. التنبؤ
    # ----------------------------------------------------
    st.markdown(f"### {'التنبؤ بالمبيعات (ARIMA) 📈' if is_ar else '📈 ARIMA Sales Forecast'}")
    st.info("💡 **خوارزمية ARIMA:** تقوم بتحليل السلاسل الزمنية وتوقع مبيعات الـ 6 أشهر القادمة لمساعدتك في تخطيط المخزون." if is_ar else "💡 **ARIMA Algorithm:** Analyzes time series to forecast the next 6 months of sales.")
    
    if not forecast_df.empty and not monthly.empty:
        trend_pct = strategy.get("trend_pct", "0%")
        is_positive = "positive" in strategy.get("direction", "")
        last_forecast_val = forecast_df["Forecast Sales"].iloc[-1]
        
        # تم ضبط المسافات هنا لتدخل داخل شرط الـ if
        if is_positive:
            st.success(f"📈 **نظرة تحليلية:** يتوقع النموذج اتجاهاً صاعداً بنسبة ({trend_pct})، لتصل المبيعات إلى {format_currency(last_forecast_val)}." if is_ar else f"📈 **Analytical View:** Model predicts an upward trend ({trend_pct}) reaching {format_currency(last_forecast_val)}.")
        else:
            st.error(f"📉 **نظرة تحليلية:** يتوقع النموذج اتجاهاً هابطاً بنسبة ({trend_pct}) لتصل المبيعات إلى {format_currency(last_forecast_val)}، مما يتطلب تدخلات عاجلة لخفض التكاليف." if is_ar else f"📉 **Analytical View:** Model predicts a downward trend ({trend_pct}) dropping to {format_currency(last_forecast_val)}, requiring immediate cost-cutting.")
        
        fig_f = go.Figure()
        fig_f.add_trace(go.Scatter(x=monthly.index, y=monthly.values, name="المبيعات الفعلية" if is_ar else "Actual", line=dict(color="#38BDF8", width=2)))
        fig_f.add_trace(go.Scatter(x=forecast_df.index, y=forecast_df["Forecast Sales"].values, name="توقع 6 أشهر" if is_ar else "Forecast", mode='lines+markers', line=dict(dash='dash', color="#EF4444", width=2)))
        fig_f.update_layout(template="plotly_dark", height=400, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_f, use_container_width=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 2. الشذوذ
    # ----------------------------------------------------
    st.markdown(f"### {'اكتشاف الشذوذ المالي (Z-Score) 🚨' if is_ar else '🚨 Financial Anomaly Detection (Z-Score)'}")
    st.warning("💡 **خوارزمية Z-Score:** تكشف الانحرافات الحادة. النقاط الحمراء تمثل معاملات بها خسائر فادحة غير منطقية تتطلب مراجعة." if is_ar else "💡 **Z-Score Algorithm:** Detects sharp deviations. Red dots represent illogical massive losses.")
    
    anomalies_count = len(anomalies)
    st.error(f"نظرة تحليلية: رصد النظام {anomalies_count} فواتير/عمليات شاذة تتجاوز الانحراف المعياري الطبيعي وتتسبب في نزيف مالي مستتر." if is_ar else f"Analytical View: Detected {anomalies_count} anomalous invoices causing hidden financial leakage.")

    if not df_z.empty:
        plot_df = df_z.copy()
        if len(plot_df) > 3000:
            plot_df = pd.concat([plot_df[plot_df['profit_z'].abs() <= 3].sample(2000), plot_df[plot_df['profit_z'].abs() > 3]])
        plot_df['Anomaly'] = plot_df['profit_z'].abs() > 3
        fig_z = px.scatter(plot_df, x='Sales', y='Profit', color='Anomaly', color_discrete_map={True: '#EF4444', False: '#38BDF8'})
        fig_z.update_traces(marker=dict(size=6, opacity=0.8))
        fig_z.update_layout(template="plotly_dark", height=400, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_z, use_container_width=True)

    st.markdown(f"#### {'📋 تفاصيل الفواتير المكسورة (الشاذة)' if is_ar else '📋 Broken Invoices Detail'}")
    if not anomalies.empty:
        st.dataframe(anomalies[["Order ID", "Product Name", "Sales", "Profit", "profit_z"]], use_container_width=True)
    else:
        st.success("✅ لا يوجد نزيف مالي حالياً." if is_ar else "✅ No financial leakage currently.")

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 3. الضرائب
    # ----------------------------------------------------
    st.markdown(f"### {strategy.get('strategy_title_ar' if is_ar else 'strategy_title_en', 'الاستراتيجية ومخاطر الضرائب')}")
    col_strat_text, col_strat_viz = st.columns([1.5, 1])
    
    with col_strat_text:
        actions = strategy.get("actions_ar" if is_ar else "actions_en", [])
        for action in actions:
            st.markdown(f"✅ {action}")
        st.success("💡 **توجيه الإدارة:** تم بناء هذه التوصيات آلياً بناءً على تحليل التنبؤات وهوامش الربح الحالية ومخاطر الضرائب." if is_ar else "💡 **Guidance:** Auto-generated recommendations based on forecast and tax risks.")
            
    with col_strat_viz:
        if not df_tax.empty and 'Tax_Risk_Level' in df_tax.columns:
            fig_tax = px.pie(df_tax, names='Tax_Risk_Level', hole=0.5, color='Tax_Risk_Level', color_discrete_map={'High':'#EF4444','Medium':'#10B981','Low':'#5C6BC0'}) 
            fig_tax.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05, 0, 0], marker=dict(line=dict(color='#0F172A', width=2)), textfont_size=14, textfont_color='white')
            fig_tax.update_layout(template='plotly_dark', showlegend=False, height=320, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_tax, use_container_width=True)
            # --- 🎯 أوبشن الفلتر التفاعلي ---
    st.markdown(f"#### {'🔍 فلترة جدول التدقيق الضريبي' if is_ar else '🔍 Tax Audit Table Filtering'}")
    
    risk_choice = st.selectbox(
        "🎯 اختر مستوى المخاطرة لعرض فواتيره في الجدول:" if is_ar else "🎯 Select Risk Level to Filter:",
        options=["All / الكل", "High / عالي", "Medium / متوسط", "Low / منخفض"]
    )

    filtered_tax = df_tax.copy()
    if "High" in risk_choice: filtered_tax = df_tax[df_tax['Tax_Risk_Level'] == 'High']
    elif "Medium" in risk_choice: filtered_tax = df_tax[df_tax['Tax_Risk_Level'] == 'Medium']
    elif "Low" in risk_choice: filtered_tax = df_tax[df_tax['Tax_Risk_Level'] == 'Low']

    st.dataframe(filtered_tax[['Order ID', 'Sales', 'Profit', 'Discount', 'Tax_Risk_Score']].sort_values("Tax_Risk_Score", ascending=False), use_container_width=True)

    st.markdown(f"#### {'🔍 جدول التدقيق الضريبي التفصيلي' if is_ar else '🔍 Detailed Tax Audit Table'}")
    if not tax_table.empty:
        st.dataframe(tax_table, use_container_width=True)
        st.warning("⚠️ ملاحظة: الفواتير المعلمة بـ '⚠️ Yes' في عمود 'Tax Suspicious ⚠️' تتطلب مراجعة بشرية فورية لمطابقة نسب الخصم مع الربح الفعلي." if is_ar else "⚠️ Note: Invoices marked as '⚠️ Yes' in the 'Tax Suspicious' column require immediate human review to align discount rates with actual profit.")
with t3:
    st.markdown(f"<div class='recovery-banner'>{'🔴 إجمالي النزيف المالي القابل للاسترداد: ' if is_ar else '🔴 Total Recoverable Leakage: '} {format_currency(recovery)}</div>", unsafe_allow_html=True)
    
    if not anomalies.empty:
        st.markdown(f"#### {'🚨 الإجراءات الإدارية الإلزامية للفواتير الشاذة' if is_ar else '🚨 Mandatory Actions for Broken Invoices'}")
        for idx, row in anomalies.head(15).iterrows():
            decision_text = get_decisions(row).get("ar" if is_ar else "en", "")
            st.markdown(f"<div class='decision-card'><b>Invoice: {row.get('Order ID', 'N/A')}</b> | <b style='color:#ef4444'>Loss: {format_currency(abs(row.get('Profit', 0)))}</b> <br><span style='color:#CBD5E1'>Decision: {decision_text}</span></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    # --- في ملف app.py داخل تاب 3 ---
    if st.button("📑 تحميل التقرير التنفيذي (PDF)" if is_ar else "📑 Download Executive PDF", use_container_width=True):
        with st.spinner("جاري تجهيز القرارات الإدارية..." if is_ar else "Compiling Administrative Decisions..."):
            
            # 1. تجميع قرارات الاستراتيجية العامة (التي تظهر في تاب 2)
            strategy_actions = strategy.get("actions_en", [])
            
            # 2. تجميع القرارات الذكية لكل فاتورة شاذة (الجديد هنا)
            invoice_decisions = []
            if not anomalies.empty:
                for idx, row in anomalies.head(20).iterrows(): # نأخذ أول 20 فاتورة حرجة
                    d_dict = get_decisions(row)
                    inv_id = row.get('Order ID', 'N/A')
                    # دمج رقم الفاتورة مع القرار الإنجليزي الخاص بها
                    invoice_decisions.append(f"Invoice {inv_id}: {d_dict['en']}")
            
            # 3. استدعاء توليد الملف وإرسال كل البيانات
            pdf_data = create_pdf_report(
                kpis=kpis, 
                executive_orders_en=" | ".join(strategy_actions), # الاستراتيجية العامة
                financial_impact=recovery, 
                anomalies=anomalies, 
                forecast_df=forecast_df,
                detailed_decisions=invoice_decisions # نمرر قرارات الفواتير هنا
            )
            
            st.download_button("✅ Click to Download", pdf_data, "RetailIQ_Executive_Audit.pdf", "application/pdf")

with t4:
    col_cfo_title, col_cfo_clear = st.columns([4, 1])
    with col_cfo_title:
        st.subheader("👔 المدير المالي الذكي (Gemini AI)" if is_ar else "👔 Smart CFO AI (Gemini)")
    with col_cfo_clear:
        if st.button("🧹 مسح المحادثة" if is_ar else "🧹 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    q = st.chat_input("اسأل المدير المالي..." if is_ar else "Ask the CFO...")
    
    if q:
        with st.chat_message("user"):
            st.markdown(q)
        st.session_state.messages.append({"role": "user", "content": q})

        # --- 🎯 حقن البيانات الصريح (عشان ميقولش معنديش بيانات) ---
        # تجهيز قائمة العملاء كنص واضح
        top_customers = ", ".join(vips['Customer Name'].head(10).astype(str).tolist()) if not vips.empty else "No Data Available"
        
        financial_context = f"""
        Role: Senior CFO. 
        MANDATORY DATA:
        - TOTAL REVENUE: {format_currency(kpis.get('Total Sales', 0))}
        - TOTAL GROSS PROFIT: {format_currency(kpis.get('Total Profit', 0))}
        - NET PROFIT (AFTER ALL TAXES): {format_currency(kpis.get('Net Profit After Tax', 0))}
        - TOTAL VAT: {format_currency(kpis.get('Total VAT', 0))}
        - INCOME TAX: {format_currency(kpis.get('Total Income Tax', 0))}
        - LEAKAGE (RECOVERY): {format_currency(recovery)}
        - TOP 10 VIP CUSTOMERS: {top_customers}
        - STRATEGY: {", ".join(strategy.get('actions_en', []))}
        
        STRICT INSTRUCTIONS: 
        1. If the user asks about taxes or net profit, use the numbers above.
        2. If asked about customers, refer to the VIP CUSTOMERS list provided.
        3. IMPORTANT: Use clear spaces between Arabic words and numbers to ensure readability.
        4. Answer in a professional, structured manner.
        """
        
        try:
            import google.generativeai as genai
            
            # قراءة المفتاح السري من إعدادات المنصة
            my_api_key = st.secrets["GOOGLE_API_KEY"]
            
            # تشغيل المكتبة بالمفتاح الصحيح
            genai.configure(api_key=my_api_key)
            
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_to_use = available_models[0] if available_models else 'gemini-1.5-flash'
            model = genai.GenerativeModel(model_to_use)
            
            with st.spinner("يتم الآن مراجعة سجلاتك المالية..." if is_ar else "Reviewing financial records..."):
                # نطلب منه في الـ Prompt إنه يحافظ على المسافات
                response = model.generate_content(f"Instruction: {financial_context} \n\n User Question: {q} \n\n (Please ensure proper spacing in your response for readability)")
                full_response = response.text
            
            with st.chat_message("assistant"):
                st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")