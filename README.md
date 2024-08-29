# Loan Simulator

Tool to simulate different loan amortization stategies.

## Usage

1. Set initial loan conditions in [initial_conditions.json](./data/initial_conditions.json)
2. Add any overpayments made to [past_overpayments.csv](./data/past_overpayments.csv)

### Running the UI
```shell
streamlit run --server.runOnSave True src/ui.py
```
