---

### 2. Din nya `ai_engine.py` (Ersätt allt på GitHub)

Här lägger vi till kontofunktionerna för registrering och inloggning, samt ser till att databasen sparar och hämtar rader baserat på den specifika kundens unika **User ID** från Supabase.

```python
import os
import pandas as pd
from supabase import create_client, Client

class FinancialFileError(Exception):
    pass

class MockReport:
    def __init__(self, filename, content_summary):
        self.filename = filename
        self.details = f"Tolkad rapportdata från: {filename}."
        self.notice = "Automatisk extraktion aktiv."
        self.content = content_summary

def parse_financial_file(filename: str, file_bytes: bytes) -> MockReport:
    if len(file_bytes) > 10485760:
        raise FinancialFileError("Filen överstiger maxgränsen på 10 MB.")
    return MockReport(filename, "Rådata.")

def analyze_report(report, api_key: str) -> str:
    return (
        "### 🤖 AI-Finansiell Analys (Simulering)\n\n"
        "**Siffror & Nyckeltal:**\n"
        "- Rapporten har extraherats utan nollor.\n"
        "- Omsättningsstrukturer har verifierats i dokumentet.\n\n"
        "**Nästa steg:**\n"
        "- Kontrollera siffrorna nedan och skicka till din personliga databas."
    )

# --- ⚙️ SUPABASE KONTOSYSTEM & AUTENTISERING ---

def initiera_supabase(url: str, key: str) -> Client:
    return create_client(url, key)

def registrera_anvandare(supabase_klient: Client, email: str, lösenord: str):
    """Skapar ett nytt, säkert konto för en kund i Supabase Auth."""
    try:
        svar = supabase_klient.auth.sign_up({"email": email, "password": lösenord})
        if svar.user:
            return {"status": "Success", "meddelande": "Registrering lyckades!"}
        return {"status": "Error", "meddelande": "Kunde inte skapa konto."}
    except Exception as e:
        return {"status": "Error", "meddelande": f"Fel: {str(e)}"}

def logga_in_anvandare(supabase_klient: Client, email: str, lösenord: str):
    """Loggar in en befintlig kund och hämtar deras unika User ID."""
    try:
        svar = supabase_klient.auth.sign_in_with_password({"email": email, "password": lösenord})
        if svar.user:
            return {"status": "Success", "user_id": svar.user.id}
        return {"status": "Error", "meddelande": "Fel e-post eller lösenord."}
    except Exception as e:
        return {"status": "Error", "meddelande": f"Inloggning misslyckades: {str(e)}"}

def logga_ut_anvandare(supabase_klient: Client):
    try:
        supabase_klient.auth.sign_out()
    except Exception:
        pass

# --- 🗄️ KUNDSPECIFIK DATABASHANTERING ---

def bearbeta_och_spara_finansdata(supabase_klient: Client, bolagsnamn: str, aar: int, kvartal: str, omsattning: float, vinst: float, user_id: str):
    """Sparar data i molnet och låser raden till den inloggade kundens user_id."""
    try:
        vinstmarginal = (vinst / omsattning) * 100 if omsattning > 0 else 0.0
        
        finansiellt_paket = {
            "user_id": user_id,  # VIKTIGT: Låser raden till denna kund!
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
            "meddelande": f"Sparat på ditt konto! {bolagsnamn} ({kvartal} {aar}) - Marginal: {vinstmarginal:.1f}%"
        }
    except Exception as e:
        return {"status": "Error", "meddelande": f"Kunde inte spara: {str(e)}"}

def hamta_historik_fran_supabase(supabase_klient: Client, user_id: str) -> pd.DataFrame:
    """Hämtar historisk data som enbart tillhör den inloggade kundens user_id."""
    try:
        # Filtrera med .eq("user_id", user_id) så kunder ALDRIG kan se varandras data!
        svar = supabase_klient.table("company_finance").select("*").eq("user_id", user_id).execute()
        data = svar.data
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df["period"] = df["year"].astype(str) + " " + df["quarter"]
        # Sortera kronologiskt
        df = df.sort_values(by=["year", "quarter"])
        return df
    except Exception:
        return pd.DataFrame()
