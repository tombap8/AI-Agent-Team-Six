# Backtest Verification Task

## Checklist
- [x] Navigate to http://localhost:8501/Backtest
- [x] Verify riskfolio weights (donut chart) is calculated/displayed
- [x] Verify cumulative return chart (Portfolio vs Benchmark) is displayed
- [x] Verify order signals table is populated
- [x] Capture screenshot
- [x] Report findings

## Findings
- Successfully navigated to the Backtest page.
- Started the backtest calculation by clicking the "🚀 포트폴리오 최적화 및 백테스트 시작" button.
- Checked the donut chart under "🍩 최적 자산 배분 비중", which is rendered as a Plotly chart.
- Verified that the "📊 과거 1개년 누적 수익률 백테스트 결과" section displays CAGR and MDD metrics (Portfolio: CAGR 40.07%, MDD -3.39% / Benchmark: CAGR -12.52%, MDD -18.89%) and shows the cumulative return chart.
- Confirmed that the "📋 증권사 주문 자동 생성 시트 (Ch 17 연동)" table is populated with order signals.
- Screenshots captured and saved to:
  - `backtest_donut_chart`
  - `backtest_cumulative_returns`
  - `backtest_order_signals`
