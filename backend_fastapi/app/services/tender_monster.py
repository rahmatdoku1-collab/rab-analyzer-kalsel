import pandas as pd
import numpy as np
from itertools import combinations
import json
import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def analyze_vendor_submissions(dfs: list, vendor_names: list, hps_budget: float, industry: str = "Umum"):
    """
    Main entry point for Tender Monster Engine.
    dfs: list of DataFrames containing line items per vendor.
    Expected columns in each DF: ['Item', 'Volume', 'Satuan', 'Harga Satuan', 'Total Harga']
    """
    # 1. Combine all items into a single analysis dataframe
    all_items = []
    for i, df in enumerate(dfs):
        vendor_name = vendor_names[i]
        for _, row in df.iterrows():
            all_items.append({
                "Vendor": vendor_name,
                "Item": row.get('Item', 'Unknown'),
                "Volume": float(row.get('Volume', 1)),
                "Harga_Satuan": float(row.get('Harga Satuan', row.get('Harga_Satuan', 0))),
                "Total_Harga": float(row.get('Total Harga', row.get('Total_Harga', 0)))
            })
            
    df_all = pd.DataFrame(all_items)
    
    # Check if empty
    if df_all.empty:
        return {"error": "No valid data found."}

    # 2. Price Fairness Engine (Median & Z-Score per item)
    item_stats = df_all.groupby('Item')['Harga_Satuan'].agg(['median', 'mean', 'std']).reset_index()
    df_all = pd.merge(df_all, item_stats, on='Item', how='left')
    
    # Calculate Markup Percentage vs Median
    df_all['Markup_Pct'] = np.where(
        df_all['median'] > 0,
        ((df_all['Harga_Satuan'] - df_all['median']) / df_all['median']) * 100,
        0
    )
    
    # 3. Hidden Markup Detector
    # Items prone to hidden markup
    hidden_markup_keywords = ['mobilisasi', 'demobilisasi', 'administrasi', 'contingency', 'supervisi', 'transport', 'handling', 'jasa', 'alat berat']
    
    df_all['Is_Hidden_Markup_Prone'] = df_all['Item'].str.lower().apply(
        lambda x: any(k in str(x) for k in hidden_markup_keywords)
    )
    
    # Flag as hidden markup if it's prone AND > 15% above median
    df_all['Fraud_Signal'] = np.where(
        df_all['Is_Hidden_Markup_Prone'] & (df_all['Markup_Pct'] > 15.0),
        "HIDDEN_MARKUP",
        np.where(df_all['Markup_Pct'] > 30.0, "OVERPRICED", "FAIR")
    )
    
    # 4. Collusion Detector
    collusion_flags = []
    # Pivot to get Harga Satuan per vendor per item
    try:
        df_pivot = df_all.pivot_table(index='Item', columns='Vendor', values='Harga_Satuan', aggfunc='first').fillna(0)
        
        for v1, v2 in combinations(vendor_names, 2):
            if v1 in df_pivot.columns and v2 in df_pivot.columns:
                # Calculate correlation/similarity
                diff = np.abs(df_pivot[v1] - df_pivot[v2])
                identical_count = (diff == 0).sum()
                total_items = len(df_pivot)
                
                identical_pct = (identical_count / total_items) * 100 if total_items > 0 else 0
                
                if identical_pct > 60:
                    collusion_flags.append({
                        "Vendor_1": v1,
                        "Vendor_2": v2,
                        "Risk_Level": "HIGH",
                        "Reason": f"{identical_pct:.0f}% item memiliki harga persis sama."
                    })
                elif identical_pct > 30:
                    collusion_flags.append({
                        "Vendor_1": v1,
                        "Vendor_2": v2,
                        "Risk_Level": "MEDIUM",
                        "Reason": f"{identical_pct:.0f}% item memiliki harga persis sama."
                    })
    except Exception as e:
        pass # Handle pivot errors if items don't align perfectly

    # 5. Smart Winner Engine
    vendor_scores = []
    
    # Industry weight settings
    weights = {
        "Sipil": {"Price": 0.50, "Reliability": 0.30, "Risk": 0.20},
        "Tambang": {"Price": 0.30, "Reliability": 0.40, "Risk": 0.30},
        "EPC": {"Price": 0.40, "Reliability": 0.30, "Risk": 0.30},
        "Umum": {"Price": 0.40, "Reliability": 0.25, "Risk": 0.35}
    }
    w = weights.get(industry, weights["Umum"])
    
    for vendor in vendor_names:
        v_data = df_all[df_all['Vendor'] == vendor]
        total_bid = v_data['Total_Harga'].sum()
        
        # Mock reliability (in real app, fetch from DB)
        # We will use random for MVP simulation unless provided
        reliability = np.random.uniform(70, 98)
        
        # Risk calculation based on fraud signals
        hidden_markup_count = len(v_data[v_data['Fraud_Signal'] == 'HIDDEN_MARKUP'])
        overpriced_count = len(v_data[v_data['Fraud_Signal'] == 'OVERPRICED'])
        
        # Base risk is 0, max is 100
        risk_score = min(100, (hidden_markup_count * 15) + (overpriced_count * 5))
        risk_inversion = 100 - risk_score
        
        # Price score (lower is better, max 100 at 20% below HPS)
        if total_bid <= 0:
            price_score = 0
        else:
            ratio = total_bid / hps_budget if hps_budget > 0 else 1
            if ratio > 1:
                price_score = max(0, 100 - ((ratio - 1) * 200)) # Penalize overbudget
            else:
                price_score = min(100, 100 + ((1 - ratio) * 100)) # Reward underbudget
                
        final_score = (w["Price"] * price_score) + (w["Reliability"] * reliability) + (w["Risk"] * risk_inversion)
        
        vendor_scores.append({
            "Vendor": vendor,
            "Total_Bid": total_bid,
            "Price_Score": price_score,
            "Reliability": reliability,
            "Risk_Score": risk_score,
            "Final_Score": final_score,
            "Hidden_Markups": hidden_markup_count,
            "Overpriced_Items": overpriced_count
        })
        
    df_vendors = pd.DataFrame(vendor_scores).sort_values("Final_Score", ascending=False)
    
    return {
        "vendor_scoring": df_vendors.to_dict(orient="records"),
        "item_analysis": df_all.to_dict(orient="records"),
        "collusion_flags": collusion_flags
    }

def generate_forensic_summary(analysis_result):
    """
    Uses OpenRouter AI to generate an executive summary of the findings.
    """
    if not OPENROUTER_API_KEY:
        return "⚠️ OPENROUTER_API_KEY tidak ditemukan. Analisis AI dinonaktifkan."
        
    try:
        # Simplify data for context limit
        top_vendor = analysis_result['vendor_scoring'][0]
        
        prompt = f"""
        Act as a Forensic Procurement Auditor. 
        Analyze this tender result and give a 3-paragraph executive summary in Indonesian.
        
        Top Vendor by Best Value Score: {top_vendor['Vendor']}
        Total Bid: Rp {top_vendor['Total_Bid']}
        Risk Score: {top_vendor['Risk_Score']}/100
        Hidden Markups detected: {top_vendor['Hidden_Markups']}
        
        Collusion Flags: {len(analysis_result['collusion_flags'])} detected.
        
        Focus on whether the Top Vendor is genuinely good or using a lowball strategy with hidden markups.
        Suggest a negotiation strategy.
        """
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error AI: {response.text}"
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"
