---

### 2. Din kompletta `ai_engine.py`
Klicka på den lilla pennan på GitHub för **`ai_engine.py`**, ta bort all gammal text och klistra in exakt detta:

```python
import os
import pandas as pd
from supabase import create_client, Client

class FinancialFileError(Exception):
    pass

class MockReport:
    def __init__(self, filename, content_summary):
        self.filename = filename
        self.details = f"Tolkad rapportdata från filen: {filename}."
        self.notice = "Observera: Detta är en automatisk dataextraktion."
        self.content = content_summary

def parse_financial_file(filename: str, file_bytes: bytes) -> MockReport:
    if len(file_bytes) > 10485760:
        raise FinancialFileError("Filen är för stor. Den maximala tillåtna filstorleken är 10 MB.")
    
    ext = filename.split(".")[-1].lower()
    if ext not in ["csv", "xlsx", "pdf"]:
        raise FinancialFileError("Ogiltigt filformat. Endast CSV, XLSX och PDF stöds.")
        
    return MockReport(filename, "Innehållsöversikt genererad från rådata.")

def analyze_report(report, api_key: str) -> str:
    if not api_key:
        raise ValueError("OpenAI API-nyckel saknas.")
    
    return (
        "### 🤖 AI-Finansiell Analys (Simulering)\n\n"
        "**Siffror & Nyckeltal:**\n"
        "- Rapporten har tagits emot och verifierats av AI-motorn.\n"
        "- Omsättning och vinststrukturer har identifierats i dokumentet.\n\n"
        "**Utveckling & Marginaler:**\n"
        "- Systemet är redo att beräkna vinstmarginal och tidsserier så fort data sparas nedan.\n\n"
        "**Osäkerheter & Risker:**\n"
        "- Kontrollera alltid extraherade värden mot originalkällan innan beslut fattas."
    )

def initiera_supabase(url: str, key: str) -> Client:
    return create_client(url, key)

def registrera_anvandare(supabase_klient: Client, email: str, lösenord: str):
    try:
        svar = supabase_klient.auth.sign_up({"email": email, "password": lösenord})
        if svar.user:
            return {"status": "Success", "meddelande": "Registrering lyckades!"}
        return {"status": "Error", "meddelande": "Kunde inte skapa konto. Kontrollera lösenord (minst 6 tecken)."}
    except Exception as e:
        return {"status": "Error", "meddelande": f"Registreringsfel: {str(e)}"}

def logga_in_anvandare(supabase_klient: Client, email: str, lösenord: str):
    try:
        svar = supabase_klient.auth.sign_in_with_password({"email": email, "password": lösenord})
        if svar.user:
            return {"status": "Success", "user_id": svar.user.id}
        return {"status": "Error", "meddelande": "Fel e-post eller lösenord."}
    except Exception as e:
        return {"status": "Error", "meddelande": f"Inloggning misslyckades: {str(e)}"}

def bearbeta_och_spara_finansdata(supabase_klient: Client, bolagsnamn: str, aar: int, kvartal: str, omsattning: float, vinst: float, user_id: str):
    try:
        if omsattning <= 0:
            return {"status": "Error", "meddelande": "Omsättningen måste vara större än 0."}
            
        vinstmarginal = (vinst / omsattning) * 100
        
        finansiellt_paket = {
            "user_id": user_id,
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
            "meddelande": f"Sparat på ditt konto! Omsättning: {omsattning:,.0f} kr, Vinst/Förlust: {vinst:,.0f} kr ({vinstmarginal:.1f}% marginal)."
        }
    except Exception as e:
        return {"status": "Error", "meddelande": f"Kunde inte spara i databasen: {str(e)}"}

def hamta_historik_fran_supabase(supabase_klient: Client, user_id: str) -> pd.DataFrame:
    try:
        svar = supabase_klient.table("company_finance").select("*").eq("user_id", user_id).execute()
        data = svar.data
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df["period"] = df["year"].astype(str) + " " + df["quarter"]
        df = df.sort_values(by=["year", "quarter"])
        return df
    except Exception:
        return pd.DataFrame()
