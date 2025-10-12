# Banking System Implementation

A comprehensive banking system implementation supporting account management, transfers, payments with cashback, and account merging.

## Features

### Level 1: Basic Banking Operations
- **Create Account**: Create new accounts with unique identifiers
- **Deposit**: Add funds to existing accounts
- **Transfer**: Move funds between accounts with balance validation

### Level 2: Analytics
- **Top Spenders**: Rank accounts by total outgoing transactions (transfers + withdrawals)
  - Sorted by amount (descending) and alphabetically by account ID for ties

### Level 3: Payments with Cashback
- **Pay**: Withdraw funds with automatic 2% cashback
  - Cashback is processed 24 hours (86,400,000 ms) after withdrawal
  - Each payment receives a unique identifier (payment1, payment2, ...)
- **Payment Status**: Check if cashback has been received for a payment

### Level 4: Advanced Features
- **Account Merging**: Combine two accounts while preserving:
  - Combined balances
  - Transaction histories
  - Pending cashback redirects
  - Merged outgoing transaction totals
- **Historical Balance**: Query account balance at any past timestamp

## Implementation Details

### Core Data Structures

```python
self.accounts                 # Current account states and balances
self.transaction_history      # Complete transaction log for historical queries
self.outgoing_transactions    # Total outgoing amount per account
self.payments                 # Payment tracking with cashback status
self.scheduled_cashbacks      # Pending cashback queue
self.account_merges           # Merge mapping for redirections
```

### Key Design Decisions

1. **Cashback Processing**: Cashbacks are automatically processed at the beginning of each operation if their timestamp has arrived, ensuring temporal consistency.

2. **Account Resolution**: After merges, account IDs are resolved through a chain to find the current active account, allowing payment status queries and cashback redirects.

3. **Transaction History**: Every operation is logged with timestamps to enable accurate historical balance reconstruction.

4. **Merge Semantics**: When account A is merged into B:
   - B inherits A's balance and outgoing transaction totals
   - A's pending cashbacks are redirected to B
   - Payment queries for A work with B's ID
   - A's transaction history becomes part of B's history

## Usage Example

```python
from banking_system import BankingSystem

bank = BankingSystem()

# Create accounts
bank.create_account(1, "alice")
bank.create_account(2, "bob")

# Deposit funds
bank.deposit(3, "alice", 1000)  # Returns: 1000
bank.deposit(4, "bob", 500)     # Returns: 500

# Transfer
bank.transfer(5, "alice", "bob", 200)  # Returns: 800 (alice's balance)

# Make payment with cashback
payment_id = bank.pay(6, "alice", 100)  # Returns: "payment1"
bank.get_payment_status(7, "alice", payment_id)  # Returns: "IN_PROGRESS"

# After 24 hours (86400000 ms), cashback is processed
bank.deposit(86400007, "alice", 50)  # Triggers cashback processing
bank.get_payment_status(86400008, "alice", payment_id)  # Returns: "CASHBACK_RECEIVED"

# Top spenders
bank.top_spenders(10, 3)  # Returns: ["alice(300)", "bob(0)", ...]

# Merge accounts
bank.merge_accounts(11, "alice", "bob")  # Returns: True

# Historical balance
bank.get_balance(12, "alice", 5)  # Returns balance at timestamp 5
```

## Testing

Run the test suite to verify all functionality:

```bash
python test_banking_system.py
```

The test suite covers:
- Basic operations (create, deposit, transfer)
- Top spenders ranking with tie-breaking
- Payment and cashback processing
- Account merging with balance inheritance
- Historical balance queries
- Cashback redirection after merges

## Complexity Analysis

- **create_account**: O(C) where C is the number of pending cashbacks
- **deposit**: O(C)
- **transfer**: O(C)
- **pay**: O(C)
- **top_spenders**: O(N log N + C) where N is the number of accounts
- **get_payment_status**: O(M + C) where M is the merge chain length
- **merge_accounts**: O(C)
- **get_balance**: O(H + C) where H is the number of transactions

## Notes

- All timestamps are guaranteed to be unique and in ascending order
- Cashback is always 2% of the withdrawal amount, rounded down
- Account IDs are case-sensitive strings
- Operations on non-existent accounts return `None`
- Merging an account into itself returns `False`


