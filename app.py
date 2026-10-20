#region Using declarations
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.NinjaScript.Indicators;
#endregion

// NQ/MNQ Trend & Pullback-robot för NinjaTrader 8
// Chart: NQ eller MNQ, 5 minuter.
// Regler:
//   Trend:   EMA 20 > EMA 50 (long) / EMA 20 < EMA 50 (short)
//   Filter:  Pris över sessions-VWAP (long) / under (short)
//   Entry:   Pullback till EMA 20 inom senaste N staplar, sedan bekräftelsestapel
//            som stänger tillbaka i trendens riktning (OnBarClose)
//   Risk:    ATR-baserad stop och target, max 1 position, daglig maxförlust-spärr,
//            max antal trades per dag, handel bara inom tidsfönster, flat före stängning
namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQTrendPullbackBot : Strategy
    {
        private EMA emaFast;
        private EMA emaSlow;
        private ATR atr;

        private double cumPV;
        private double cumVol;
        private double vwap;
        private bool dailyLocked;
        private int tradesToday;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "NQ/MNQ Trend & Pullback (EMA20/50, VWAP, ATR, daily lock)";
                Name = "NQTrendPullbackBot";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsFillLimitOnTouch = false;
                MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
                OrderFillResolution = OrderFillResolution.Standard;
                Slippage = 0;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Gtc;
                TraceOrders = false;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 60;
                IsInstantiatedOnEachOptimizationIteration = true;

                OrderQuantity = 1;
                EmaFastPeriod = 20;
                EmaSlowPeriod = 50;
                AtrPeriod = 14;
                StopAtrMult = 1.5;
                TargetAtrMult = 3.0;
                PullbackBars = 3;
                MaxDailyLoss = 500;
                MaxTradesPerDay = 5;
                // Tider i diagrammets tidszon (HHMMSS). Standard = svensk tid (NQ RTH 15:30-22:00).
                StartTime = 153500;
                EndTime = 213000;
                CloseTime = 215500;
            }
            else if (State == State.DataLoaded)
            {
                emaFast = EMA(EmaFastPeriod);
                emaSlow = EMA(EmaSlowPeriod);
                atr = ATR(AtrPeriod);
                AddChartIndicator(emaFast);
                AddChartIndicator(emaSlow);
            }
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0)
                return;

            // --- Sessions-VWAP (nollställs vid ny session) ---
            if (Bars.IsFirstBarOfSession)
            {
                cumPV = 0;
                cumVol = 0;
                dailyLocked = false;
                tradesToday = 0;
            }
            double typical = (High[0] + Low[0] + Close[0]) / 3.0;
            cumPV += typical * Volume[0];
            cumVol += Volume[0];
            vwap = cumVol > 0 ? cumPV / cumVol : Close[0];

            if (CurrentBar < BarsRequiredToTrade)
                return;

            int now = ToTime(Time[0]);

            // --- Flat före stängning ---
            if (now >= CloseTime)
            {
                FlattenAll("TimeClose");
                return;
            }

            // --- Daglig maxförlust-spärr ---
            if (!dailyLocked && GetSessionPnL() <= -MaxDailyLoss)
            {
                dailyLocked = true;
                Print(Time[0] + " DAILY LOCK aktiverad. Dagens P&L: " + GetSessionPnL().ToString("F2"));
            }
            if (dailyLocked)
            {
                FlattenAll("DailyLock");
                return;
            }

            // --- Entry-regler: bara flat, inom tidsfönster, under max antal trades ---
            if (Position.MarketPosition != MarketPosition.Flat)
                return;
            if (now < StartTime || now >= EndTime)
                return;
            if (tradesToday >= MaxTradesPerDay)
                return;

            double stopTicks = Math.Max(4, Math.Round(atr[0] * StopAtrMult / TickSize));
            double targetTicks = Math.Max(4, Math.Round(atr[0] * TargetAtrMult / TickSize));

            bool upTrend = emaFast[0] > emaSlow[0];
            bool downTrend = emaFast[0] < emaSlow[0];

            bool pulledBackLong = false;
            bool pulledBackShort = false;
            for (int i = 1; i <= PullbackBars; i++)
            {
                if (Low[i] <= emaFast[i]) pulledBackLong = true;
                if (High[i] >= emaFast[i]) pulledBackShort = true;
            }

            bool longSignal = upTrend
                && Close[0] > vwap
                && pulledBackLong
                && Close[0] > emaFast[0]
                && Close[0] > Open[0];

            bool shortSignal = downTrend
                && Close[0] < vwap
                && pulledBackShort
                && Close[0] < emaFast[0]
                && Close[0] < Open[0];

            if (longSignal)
            {
                SetStopLoss("Long", CalculationMode.Ticks, stopTicks, false);
                SetProfitTarget("Long", CalculationMode.Ticks, targetTicks);
                EnterLong(OrderQuantity, "Long");
                tradesToday++;
                Print(Time[0] + " LONG signal. Stop " + stopTicks + " ticks, target " + targetTicks + " ticks.");
            }
            else if (shortSignal)
            {
                SetStopLoss("Short", CalculationMode.Ticks, stopTicks, false);
                SetProfitTarget("Short", CalculationMode.Ticks, targetTicks);
                EnterShort(OrderQuantity, "Short");
                tradesToday++;
                Print(Time[0] + " SHORT signal. Stop " + stopTicks + " ticks, target " + targetTicks + " ticks.");
            }
        }

        private void FlattenAll(string reason)
        {
            if (Position.MarketPosition == MarketPosition.Long)
                ExitLong("Exit " + reason, "Long");
            else if (Position.MarketPosition == MarketPosition.Short)
                ExitShort("Exit " + reason, "Short");
        }

        // Dagens realiserade + orealiserade resultat i valuta
        private double GetSessionPnL()
        {
            double pnl = 0;
            DateTime today = Time[0].Date;

            for (int i = SystemPerformance.AllTrades.Count - 1; i >= 0; i--)
            {
                Trade t = SystemPerformance.AllTrades[i];
                if (t.Exit.Time.Date != today)
                    break;
                pnl += t.ProfitCurrency - t.Commission;
            }

            if (Position.MarketPosition != MarketPosition.Flat)
                pnl += Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);

            return pnl;
        }

        #region Properties
        [NinjaScriptProperty]
        [Range(1, 100)]
        [Display(Name = "Antal kontrakt", Order = 1, GroupName = "1. Position")]
        public int OrderQuantity { get; set; }

        [NinjaScriptProperty]
        [Range(2, 200)]
        [Display(Name = "EMA snabb", Order = 1, GroupName = "2. Indikatorer")]
        public int EmaFastPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(3, 400)]
        [Display(Name = "EMA långsam", Order = 2, GroupName = "2. Indikatorer")]
        public int EmaSlowPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(2, 100)]
        [Display(Name = "ATR-period", Order = 3, GroupName = "2. Indikatorer")]
        public int AtrPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(1, 10)]
        [Display(Name = "Pullback-staplar (lookback)", Order = 4, GroupName = "2. Indikatorer")]
        public int PullbackBars { get; set; }

        [NinjaScriptProperty]
        [Range(0.1, 10.0)]
        [Display(Name = "Stop (x ATR)", Order = 1, GroupName = "3. Risk")]
        public double StopAtrMult { get; set; }

        [NinjaScriptProperty]
        [Range(0.1, 20.0)]
        [Display(Name = "Target (x ATR)", Order = 2, GroupName = "3. Risk")]
        public double TargetAtrMult { get; set; }

        [NinjaScriptProperty]
        [Range(1, 1000000)]
        [Display(Name = "Max daglig förlust (USD)", Order = 3, GroupName = "3. Risk")]
        public double MaxDailyLoss { get; set; }

        [NinjaScriptProperty]
        [Range(1, 100)]
        [Display(Name = "Max trades per dag", Order = 4, GroupName = "3. Risk")]
        public int MaxTradesPerDay { get; set; }

        [NinjaScriptProperty]
        [Range(0, 235959)]
        [Display(Name = "Starttid (HHMMSS)", Order = 1, GroupName = "4. Tid")]
        public int StartTime { get; set; }

        [NinjaScriptProperty]
        [Range(0, 235959)]
        [Display(Name = "Sista entry-tid (HHMMSS)", Order = 2, GroupName = "4. Tid")]
        public int EndTime { get; set; }

        [NinjaScriptProperty]
        [Range(0, 235959)]
        [Display(Name = "Stäng alla positioner (HHMMSS)", Order = 3, GroupName = "4. Tid")]
        public int CloseTime { get; set; }
        #endregion
    }
}
