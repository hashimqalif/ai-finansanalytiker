# AI Finansanalytiker

En Streamlit-app med en informationssida och ett analysverktyg för finansiella
rapporter på svenska med OpenAI.

## Kom igång

Från projektmappen:

```bash
python -m pip install -r requirements.txt
export OPENAI_API_KEY="din-api-nokkel"
streamlit run app.py
```

Du kan också ange API-nyckeln i appen. Nyckeln sparas inte av appen.

För att spara verifierade nyckeltal i Supabase behöver du ange
`SUPABASE_URL` och `SUPABASE_ANON_KEY` som miljövariabler innan du startar appen:

```bash
export SUPABASE_URL="https://ditt-projekt.supabase.co"
export SUPABASE_ANON_KEY="din-publishable-eller-anon-nyckel"
```

Ladda upp en CSV-, XLSX- eller textbaserad PDF-fil (max 10 MB). CSV- och Excel-filer
begränsas till 5 000 rader och 40 kolumner; PDF-filer begränsas till de första 30
sidorna. Skannade PDF-filer utan text stöds inte.

## Integritet och begränsningar

Filinnehållet skickas till OpenAI först när du väljer «Analysera rapport». Ladda inte
upp data som du inte har tillstånd att dela med OpenAI. Analysen kan innehålla fel
och är inte personlig investerings-, skatte- eller juridisk rådgivning.

Hemsidans priser och planbeskrivningar är förslag. Appen hanterar inte betalningar,
abonnemang, analyskvoter eller planbaserade filgränser.

## Supabase

`ai_engine.py` innehåller hjälpfunktioner för att ansluta till Supabase och spara
nyckeltal i tabellen `company_finance`. Historikdiagrammen hämtar sparad data från
den tabellen när du väljer att läsa in historiken; de visar aldrig exempelvärden.
Anropet kräver uttryckligen angiven omsättning och vinst; rapportanalysen gissar
inte dessa värden. Skapa tabellen med
kolumnerna `company_name`, `year`, `quarter`, `revenue`, `profit` och
`profit_margin` innan du använder funktionen. Begränsa databasåtkomsten med
Supabase Row Level Security och använd inte en service role-nyckel i klientappen.
Innan datan sparas måste du själv ange och verifiera bolag, period (kvartal eller
helår), omsättning och vinst i formuläret. Appen beräknar vinstmarginalen från
dessa värden. En negativ vinst anges som förlust. Använd en Supabase anon/publishable
nyckel med lämpliga Row Level Security-policyer; exponera aldrig en service role-nyckel.
