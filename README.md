# Bouns Bot 🤖

A Twitter bot that automatically tweets images of newly minted Boun NFTs on Berachain. The bot monitors the Bouns auction contract to detect new mints and posts the NFT artwork to Twitter.

## Features

- 🔄 Automatically detects new Boun NFT mints via auction contract
- 🖼️ Fetches on-chain SVG artwork and converts to PNG
- 🐦 Posts tweets with NFT images
- 🐳 Runs in a Docker container
- 🚫 Stateless - no database required
- ⚡ Smart polling based on auction end times
- 🎯 Handles burned tokens correctly by tracking auction state

## Prerequisites

- Docker installed on your system
- Twitter API credentials (from Twitter Developer Portal)
- Berachain RPC endpoint
- Boun NFT contract address
- Boun Auction contract address

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bouns-bot.git
cd bouns-bot
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit `.env` with your credentials:
```env
RPC_URL=your_rpc_url_here
NFT_CONTRACT_ADDRESS=your_nft_contract_address_here
AUCTION_CONTRACT_ADDRESS=your_auction_contract_address_here
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_SECRET=your_twitter_access_secret_here
```

4. Build and run with Docker:
```bash
# Build the image
docker build -t bouns-bot .

# Run the container
docker run -d \
  --name bouns-bot \
  --env-file .env \
  bouns-bot
```

## Running Without Docker

1. Install Python 3.11 or higher

2. Install system dependencies (for cairosvg):
```bash
# Ubuntu/Debian
sudo apt-get install libcairo2-dev libpango1.0-dev

# macOS
brew install cairo pango
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Run the bot:
```bash
python main.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RPC_URL` | Berachain RPC endpoint URL |
| `NFT_CONTRACT_ADDRESS` | Boun NFT contract address |
| `AUCTION_CONTRACT_ADDRESS` | Boun Auction contract address |
| `TWITTER_API_KEY` | Twitter API key |
| `TWITTER_API_SECRET` | Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | Twitter access token |
| `TWITTER_ACCESS_SECRET` | Twitter access token secret |

## Monitoring

Check container logs:
```bash
docker logs bouns-bot
```

## Troubleshooting

1. **Missing Twitter Credentials**: The bot will run in mock mode, printing tweets to console instead of posting to Twitter.

2. **RPC Issues**: Check your RPC endpoint and ensure you have sufficient credits.

3. **Container Crashes**: Check logs with `docker logs bouns-bot` for error messages.

## Development

- The bot monitors the auction contract to detect new Bouns
- Smart polling adjusts frequency based on auction end times
- SVG images are converted to PNG using cairosvg
- Error handling ensures the bot continues running despite temporary failures
- No persistent storage - restarts will pick up from current auction state

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
