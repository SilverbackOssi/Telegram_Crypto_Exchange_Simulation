# Telegram Crypto Simulation Bot Development Documentation

A telegram bot that simulates cryptocurrency trading without real money.

## Features

- Virtual crypto trading
- Real-time price tracking
- Portfolio management
- Trade history

## Development

### Project Structure

The code uses Django models to define the `Wallet` and `Transaction` models, which represent the user's wallet and transaction records, respectively. The models are related to the `User` model, which stores user information such as the Telegram user ID and username.

The code also includes error handling mechanisms such as custom exceptions (`InsufficientFundsError`), input validation, and exception handling for API requests.

```
├── bot.py          # Main bot logic
├── commands/       # Bot commands
├── handlers/       # Message handlers
├── models/         # Data models
└── utils/          # Helper functions
```

### Adding New Commands

1. Create a new command file in `commands/`
2. Register the command in `bot.py`
3. Implement the command logic
4. Test the functionality

## Usage

Start trading crypto with virtual money by interacting with the bot on Telegram.
The bot would be available @CryptoSimBotOssi when hosted

## License

MIT License
