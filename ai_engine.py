from __future__ import annotations
import pandas as pd
import numpy as np
import scipy.stats as stats
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")

def run_arima_forecast(df: pd.DataFrame):
    df_time = df.copy()
    df_time.set_index("Order Date", inplace=True)
    monthly_sales = df_time["Sales"].resample("ME").sum().fillna(0)
    
    if len(monthly_sales) < 6:
        return monthly_sales, pd.DataFrame()
        
    model = ARIMA(monthly_sales, order=(1, 1, 1))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=6)
    forecast_dates = pd.date_range(start=monthly_sales.index[-1] + pd.offsets.MonthBegin(1), periods=6, freq="MS")
    forecast_df = pd.DataFrame({"Forecast Sales": forecast.values}, index=forecast_dates)
    return monthly_sales, forecast_df

def get_prescriptive_directive(monthly_sales, forecast_df, anomaly_count, profit_margin):
    """توليد نصائح استراتيجية دقيقة لتجنب الخسارة أو تعظيم الربح"""
    if monthly_sales.empty or forecast_df.empty:
        return {"direction": "neutral", "actions_ar": [], "actions_en": [], "strategy_title_ar": "", "strategy_title_en": ""}
        
    last_actual = float(monthly_sales.iloc[-1])
    avg_forecast = float(forecast_df["Forecast Sales"].mean())
    trend_pct = ((avg_forecast - last_actual) / max(abs(last_actual), 1)) * 100

    if avg_forecast < last_actual or profit_margin < 0.10:
        # حالة الخسارة أو ضعف الربحية - استراتيجية تجنب الخسارة
        direction = "negative"
        title_ar = "🛡️ استراتيجية الدفاع وتجنب الخسائر (Stop-Loss)"
        title_en = "🛡️ Defensive Strategy & Loss Avoidance"
        actions_ar = [
            "⚠️ إيقاف فوري للخصومات على المنتجات التي يقل هامش ربحها عن 5%.",
            "🔍 تدقيق فوري للفواتير الحمراء (الشاذة) لاسترداد النزيف المالي.",
            "📦 تقليل حجم المخزون من الفئات الراكدة لزيادة السيولة (Cash Flow).",
            "📉 مراجعة عقود الموردين للمنتجات ذات التكلفة المرتفعة لتقليل COGS."
        ]
        actions_en = [
            "⚠️ Stop discounts on products with <5% margin immediately.",
            "🔍 Audit 'Red' anomaly invoices to recover financial leakage.",
            "📦 Reduce inventory levels for slow-moving categories to boost cash flow.",
            "📉 Renegotiate supplier contracts for high-cost items to lower COGS."
        ]
    else:
        # حالة الربحية والنمو - استراتيجية تعظيم المكاسب
        direction = "positive"
        title_ar = "🚀 استراتيجية الهجوم وتعظيم الأرباح (Profit-Max)"
        title_en = "🚀 Offensive Strategy & Profit Maximization"
        actions_ar = [
            "💰 توجيه ميزانية التسويق فوراً نحو 'كبار العملاء' (VIP) لزيادة الولاء.",
            "📈 زيادة مخزون المنتجات 'الأكثر ربحية' بنسبة 15% لمواجهة الطلب المتوقع.",
            "🎯 تفعيل سياسة الـ Upselling (عرض منتجات أعلى سعراً) للفئات الواعدة.",
            "💎 الحفاظ على مستوى الخصم الحالي لضمان الحصة السوقية مع مراقبة الهامش."
        ]
        actions_en = [
            "💰 Reallocate marketing budget to VIP customers to boost LTV.",
            "📈 Increase inventory by 15% for high-margin products.",
            "🎯 Implement Upselling strategies for promising categories.",
            "💎 Maintain current discount levels while monitoring net margins."
        ]

    return {
        "direction": direction,
        "strategy_title_ar": title_ar,
        "strategy_title_en": title_en,
        "actions_ar": actions_ar,
        "actions_en": actions_en,
        "trend_pct": f"{trend_pct:+.1f}%"
    }

def detect_anomalies(df: pd.DataFrame):
    df_anom = df.copy()
    if "Profit" in df_anom.columns:
        df_anom["profit_z"] = np.nan_to_num(stats.zscore(df_anom["Profit"].fillna(0)))
    else:
        df_anom["profit_z"] = 0
        
    if "Discount" in df_anom.columns:
        df_anom["discount_z"] = np.nan_to_num(stats.zscore(df_anom["Discount"].fillna(0)))
    else:
        df_anom["discount_z"] = 0
        
    anomalies = df_anom[(df_anom["profit_z"].abs() > 3) | (df_anom["discount_z"].abs() > 3)].copy()
    return df_anom, anomalies

def calculate_tax_risk(df: pd.DataFrame) -> pd.DataFrame:
    """إضافة حساب مستوى الخطر الضريبي لرسم الـ Pie Chart"""
    df_tax = df.copy()
    if "Discount" not in df_tax.columns: df_tax["Discount"] = 0
    if "Profit" not in df_tax.columns: df_tax["Profit"] = 0
    
    df_tax['Tax_Risk_Score'] = (df_tax['Discount'] * 100) + (df_tax['Profit'] < 0) * 50
    df_tax['Tax_Risk_Level'] = pd.cut(df_tax['Tax_Risk_Score'], bins=[-1, 35, 65, 5000], labels=['Low', 'Medium', 'High'])
    return df_tax

def calculate_kpis(df: pd.DataFrame) -> dict:
    """حساب مؤشرات الأداء المالية والتكاليف"""
    total_sales  = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    total_orders = int(df["Order ID"].nunique()) if "Order ID" in df.columns else len(df)

    # حساب التكلفة الإجمالية ونسبتها (المعادلات العلمية)
    total_cost = total_sales - total_profit
    cost_to_sales_ratio = safe_divide(total_cost, total_sales) * 100

    if "Order Date" in df.columns:
        date_range_days = max((df["Order Date"].max() - df["Order Date"].min()).days, 1)
        order_velocity  = round(safe_divide(total_orders, date_range_days), 2)
    else:
        order_velocity = 0.0

    return {
        "Total Sales": total_sales,
        "Total Profit": total_profit,
        "Total Cost (COGS)": total_cost,
        "Cost to Sales Ratio": cost_to_sales_ratio,
        "Profit Margin": safe_divide(total_profit, total_sales),
        "Average Order Value": safe_divide(total_sales, total_orders),
        "Total Orders": total_orders,
        "Order Velocity": order_velocity,
        "Total VAT": float(df["VAT_Amount"].sum()) if "VAT_Amount" in df.columns else 0.0,
        "Total Income Tax": float(df["Income_Tax"].sum()) if "Income_Tax" in df.columns else 0.0,
        "Net Profit After Tax": float(df["Net_Profit_AfterTax"].sum()) if "Net_Profit_AfterTax" in df.columns else 0.0,
        "Tax Suspicious Count": int(df["Tax_Suspicious"].sum()) if "Tax_Suspicious" in df.columns else 0,
    }

def get_decisions(row) -> dict:
    """محرك قرارات خبير (Expert System) شامل - قواعد علمية وديناميكية"""
    profit = float(row.get("Profit", 0))
    sales = float(row.get("Sales", 0))
    discount = float(row.get("Discount", 0))
    qty = float(row.get("Quantity", 1))
    profit_z = float(row.get("profit_z", 0))
    tax_suspicious = row.get("Tax_Suspicious", False)
    margin = profit / sales if sales > 0 else 0
    rec_en, rec_ar = [], []

    # 1. الامتثال الضريبي
    if tax_suspicious:
        rec_ar.append(f"⚖️ إحالة للامتثال الضريبي: تلاعب محتمل (خصم {discount*100:.0f}% لتوليد خسارة دفترية بقيمة {abs(profit):,.2f}$).")
        rec_en.append(f"⚖️ Tax Compliance Alert: Potential manipulation (phantom {discount*100:.0f}% discount causing ${abs(profit):,.2f} loss).")

    # 2. أخطاء الإدخال
    if margin > 0.85 and sales > 100:
        rec_ar.append(f"🚨 ربح وهمي: الهامش يتجاوز {margin*100:.0f}% (مكسب {profit:,.2f}$). يرجى المراجعة، غالباً لم يتم تسجيل التكلفة (COGS).")
        rec_en.append(f"🚨 Phantom Profit: Margin is {margin*100:.0f}% (Profit: ${profit:,.2f}). Likely missing COGS data.")

    # 3. تحليل الخسائر (النزيف)
    if profit < 0:
        if discount >= 0.15:
            rec_ar.append(f"✂️ إلغاء الخصم فوراً ({discount*100:.0f}%): هذا الخصم تسبب في نزيف مباشر بقيمة {abs(profit):,.2f}$ من رأس المال.")
            rec_en.append(f"✂️ Revoke {discount*100:.0f}% Discount: It caused a direct leakage of ${abs(profit):,.2f}.")
        elif sales > 500:
            rec_ar.append(f"🛑 إيقاف البيع مؤقتاً: بيع بقيمة {sales:,.2f}$ أدى لخسارة {abs(profit):,.2f}$. المزيد من المبيعات يعني إفلاس أسرع.")
            rec_en.append(f"🛑 Halt Sales: Volume of ${sales:,.2f} resulted in ${abs(profit):,.2f} loss.")
        else:
            rec_ar.append(f"📉 تدقيق التكاليف: الفاتورة خسرانة {abs(profit):,.2f}$ بدون خصومات! تكلفة التوريد تتجاوز سعر البيع.")
            rec_en.append(f"📉 COGS Audit: Loss of ${abs(profit):,.2f} with NO discount. Sourcing costs exceed price.")

    # 4. القواعد الاحترافية (Micro-transactions & Cannibalization)
    if profit > 0:
        if sales > 0 and sales < 5 and qty == 1:
            rec_ar.append(f"💳 فخ رسوم الدفع: مبيعات دقيقة ({sales:,.2f}$). رسوم الفيزا ستبتلع الربح. ادمج المنتج في عروض (Bundles).")
            rec_en.append(f"💳 Micro-transaction Trap: ${sales:,.2f} sale. Fees will eat the profit. Bundle this item.")
        elif discount >= 0.20 and margin >= 0.30:
            rec_ar.append(f"💸 خصم مهدر: المنتج قوي ويحقق هامش {margin*100:.0f}% رغم وجود خصم {discount*100:.0f}%. قم بإلغاء الخصم فوراً.")
            rec_en.append(f"💸 Unjustified Discount: Margin is {margin*100:.0f}% despite a {discount*100:.0f}% discount.")
        elif discount >= 0.40 and qty <= 2:
            rec_ar.append(f"🗑️ مخزون ميت: خصم ضخم ({discount*100:.0f}%) لبيع {qty:.0f} قطع فقط. قم بتصفية المنتج فوراً.")
            rec_en.append(f"🗑️ Dead Inventory: Massive {discount*100:.0f}% discount for few units.")

    # 5. الفرص الضائعة
    if margin > 0.40 and qty < 5 and profit > 0 and discount < 0.20:
        rec_ar.append(f"🚀 فرصة نمو: هامش ممتاز ({margin*100:.0f}%) حقق {profit:,.2f}$ من {qty:.0f} قطع فقط. ضاعف ميزانية التسويق.")
        rec_en.append(f"🚀 Growth Opportunity: Excellent {margin*100:.0f}% margin. Double marketing spend.")

    # 6. Fallback
    if not rec_ar:
        rec_ar.append(f"✅ أداء مستقر: هامش ({margin*100:.0f}%) وربح {profit:,.2f}$. حافظ على سياسة التسعير.")
        rec_en.append(f"✅ Healthy: Stable {margin*100:.0f}% margin. Keep current pricing.")

    return {"en": " | ".join(rec_en), "ar": " | ".join(rec_ar)}
    
def run_full_ai_analysis(df: pd.DataFrame) -> dict:
    if df.empty: return {}
    monthly_sales, forecast_df = run_arima_forecast(df)
    df_with_zscore, anomalies = detect_anomalies(df)
    df_with_tax = calculate_tax_risk(df)
    
    total_sales = df["Sales"].sum()
    profit_margin = df["Profit"].sum() / total_sales if total_sales > 0 else 0
    
    # استدعاء المحرك الاستراتيجي
    strategy = get_prescriptive_directive(monthly_sales, forecast_df, len(anomalies), profit_margin)
    
    return {
        "monthly_sales": monthly_sales,
        "forecast_df": forecast_df,
        "df_with_zscore": df_with_zscore,
        "anomalies": anomalies,
        "df_with_tax": df_with_tax,
        "strategy": strategy,
        "total_potential_recovery": abs(anomalies[anomalies["Profit"] < 0]["Profit"].sum())
    }
