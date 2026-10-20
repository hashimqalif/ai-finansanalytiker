# LÄGG TILL DETTA LÄNGST NER I DIN AI_ENGINE.PY FÖR ATT MATCHA DE 10 TESTERNA

import pandas as pd
from supabase import create_client, Client

def initiera_supabase(url: str, key: str) -> Client:
    """Skapar en säker koppling till din Supabase-databas."""
    return create_client(url, key)

def bearbeta_och_spara_finansdata(supabase_klient: Client, bolagsnamn: str, aar: int, kvartal: str, omsattning: float, vinst: float):
    """Beräknar marginaler och sparar verifierade data i Supabase."""
    try:
        if omsattning <= 0:
            return {"status": "Error", "meddelande": "Omsättningen måste vara större än 0."}
            
        # Beräkna vinstmarginal (Hanterar även negativa vinstvärden för förlust)
        vinstmarginal = (vinst / omsattning) * 100
        
        finansiellt_paket = {
            "company_name": bolagsnamn,
            "year": int(aar),
            "quarter": str(kvartal),
            "revenue": round(omsattning, 2),
            "profit": round(vinst, 2),
            "profit_margin": round(vinstmarginal, 2)
        }
        
        supabase_klient.table("company_finance").insert(finansiellt_paket).execute()
        return {
            "status": "Success",
            "meddelande": f"Sparat i molnet! Omsättning: {omsattning:,.0f} kr, Vinst/Förlust: {vinst:,.0f} kr ({vinstmarginal:.1f}% marginal)."
        }
    except Exception as e:
        return {"status": "Error", "meddelande": f"Kunde inte spara: {str(e)}"}

def hämta_historik_från_supabase(supabase_klient: Client) -> pd.DataFrame:
    """Hämtar historisk data från Supabase och skapar en kombinerad periodkolumn för diagram."""
    try:
        svar = supabase_klient.table("company_finance").select("company_name, year, quarter, revenue, profit").execute()
        data = svar.data
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        # Skapa en snygg sträng för tidsaxeln, t.ex. "2026 Q3" eller "2026 Helår"
        df["period"] = df["year"].astype(str) + " " + df["quarter"]
        return df
    except Exception:
        return pd.DataFrame()
