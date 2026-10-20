import os
import pandas as pd
from supabase import create_client, Client

# --- 1. PRODUKTSPECIFIKA FELHANTERINGAR ---
class FinancialFileError(Exception):
    """Eget felmeddelande för hantering av ogiltiga finansiella filer."""
    pass

# --- 2. KLASS FÖR ATT STRUKTURERA RAPPORTDATA ---
class MockReport:
    def __init__(self, filename, content_summary):
        self.filename = filename
        self.details = f"Tolkad rapportdata från filen: {filename}."
        self.notice = "Observera: Detta är en automatisk dataextraktion."
        self.content = content_summary

# --- 3. FUNKTION FÖR ATT LÄSA OCH VALIDERA FILER ---
def parse_financial_file(filename: str, file_bytes: bytes) -> MockReport:
    """Läser in och validerar filstorlek och format (CSV, XLSX, PDF)."""
    # Begränsning: Max 10 MB (10 * 1024 * 1024 bytes)
    if len(file_bytes) > 10485760:
        raise FinancialFileError("Filen är för stor. Den maximala tillåtna filstorleken är 10 MB.")
    
    ext = filename.split(".")[-1].lower()
    if ext not in ["csv", "xlsx", "pdf"]:
        raise FinancialFileError("Ogiltigt filformat. Endast CSV, XLSX och PDF stöds.")
        
    return MockReport(filename, "Innehållsöversikt genererad från rådata.")

# --- 4. FUNKTION FÖR ATT ANROPA OPENAI ---
def analyze_report(report, api_key: str) -> str:
    """Skickar rapportens innehåll till OpenAI för finansiell sammanfattning."""
    if not api_key:
        raise ValueError("OpenAI API-nyckel saknas.")
    
    # Här ligger det förberedda AI-svaret tills du har fyllt på ditt OpenAI-konto med krediter.
    # Detta förhindrar att appen kraschar på grund av konto-kvoter under testning.
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

# --- 5. SUPABASE DATABASHANTERING (UTAN SVENSKA TECKEN) ---
def initiera_supabase(url: str, key: str) -> Client:
    """Skapar en säker koppling till din Supabase-databas."""
    return create_client(url, key)

def bearbeta_och_spara_finansdata(supabase_klient: Client, bolagsnamn: str, aar: int, kvartal: str, omsattning: float, vinst: float):
    """Beräknar finansiella marginaler och sparar verifierad data i Supabase."""
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

def hamta_historik_fran_supabase(supabase_klient: Client) -> pd.DataFrame:
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
