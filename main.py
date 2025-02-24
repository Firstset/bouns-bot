import os
import time
import base64
import json
import cairosvg
from web3 import Web3
from typing import Optional, NamedTuple
from dotenv import load_dotenv
from twitter_adapter import TwitterAdapter
from dataclasses import dataclass

@dataclass
class AuctionData:
    noun_id: int
    amount: int
    start_time: int
    end_time: int
    bidder: str
    settled: bool

class BounsBot:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Load environment variables
        self.rpc_url = os.getenv("RPC_URL")
        self.nft_contract_address = os.getenv("NFT_CONTRACT_ADDRESS")
        self.auction_contract_address = os.getenv("AUCTION_CONTRACT_ADDRESS")
        
        if not all([self.rpc_url, self.nft_contract_address, self.auction_contract_address]):
            raise ValueError("Missing required environment variables: RPC_URL, NFT_CONTRACT_ADDRESS, AUCTION_CONTRACT_ADDRESS")

        # Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Convert contract addresses to checksum addresses
        self.nft_contract_address = Web3.to_checksum_address(self.nft_contract_address)
        self.auction_contract_address = Web3.to_checksum_address(self.auction_contract_address)
        
        # Initialize contracts
        self.nft_contract, self.auction_contract = self._initialize_contracts()
        
        # Initialize Twitter API
        self._initialize_twitter()

    def _initialize_contracts(self):
        # NFT contract ABI (minimal)
        nft_abi = [
            {
                "inputs": [{"type": "uint256"}],
                "name": "tokenURI",
                "outputs": [{"type": "string"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Auction contract ABI
        auction_abi = [
            {
                "inputs": [],
                "name": "auction",
                "outputs": [
                    {"name": "nounId", "type": "uint256"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"},
                    {"name": "bidder", "type": "address"},
                    {"name": "settled", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        nft_contract = self.web3.eth.contract(
            address=self.nft_contract_address,
            abi=nft_abi
        )
        
        auction_contract = self.web3.eth.contract(
            address=self.auction_contract_address,
            abi=auction_abi
        )
        
        return nft_contract, auction_contract

    def _get_current_auction(self) -> AuctionData:
        """Get current auction data from the contract"""
        result = self.auction_contract.functions.auction().call()
        return AuctionData(
            noun_id=result[0],
            amount=result[1],
            start_time=result[2],
            end_time=result[3],
            bidder=result[4],
            settled=result[5]
        )

    def _calculate_sleep_time(self, auction: AuctionData) -> int:
        """Calculate how long to sleep based on auction end time"""
        current_time = int(time.time())
        
        # If auction is not settled and end_time hasn't passed
        if not auction.settled and auction.end_time > current_time:
            # Sleep until end_time, but no longer than 5 minutes
            sleep_time = min(auction.end_time - current_time, 300)
            return sleep_time
        
        # Default sleep time of 5 minutes
        return 300

    def _initialize_twitter(self):
        """Initialize Twitter API client"""
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_secret = os.getenv("TWITTER_ACCESS_SECRET")

        try:
            if all([api_key, api_secret, access_token, access_secret]):
                self.twitter = TwitterAdapter(
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token,
                    access_secret=access_secret
                )
                print("Twitter API initialized with OAuth")
            else:
                print("Warning: Missing Twitter credentials, falling back to mock tweets")
                self.twitter = None
                return

        except Exception as e:
            print(f"Error initializing Twitter API: {e}")
            self.twitter = None

    def get_svg(self, token_uri: str) -> bytes:
        """Extract SVG bytes from token URI"""
        # Remove "data:application/json;base64,"
        json_prefix = "data:application/json;base64,"
        if token_uri.startswith(json_prefix):
            token_uri = token_uri[len(json_prefix):]

        # Decode JSON
        decoded_json = base64.b64decode(token_uri).decode("utf-8")
        metadata = json.loads(decoded_json)

        # Extract image field
        image_data = metadata["image"]
        svg_prefix = "data:image/svg+xml;base64,"
        if image_data.startswith(svg_prefix):
            image_data = image_data[len(svg_prefix):]

        # Decode SVG
        return base64.b64decode(image_data)

    def svg_to_png(self, svg_bytes: bytes) -> bytes:
        """Convert SVG bytes to PNG bytes using cairosvg"""
        try:
            png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
            print(f"Successfully converted SVG ({len(svg_bytes)} bytes) to PNG ({len(png_bytes)} bytes)")
            return png_bytes
        except Exception as e:
            print(f"Error converting SVG to PNG: {e}")
            # Return the original SVG bytes as a fallback
            return svg_bytes

    def post_tweet(self, png_data: bytes, token_id: int):
        """Post tweet with image using Twitter API"""
        if not self.twitter:
            # Fall back to mock implementation
            print(f"[MOCK] Tweeting about token #{token_id}")
            print(f"[MOCK] Tweet text: New Boun minted! #{token_id}")
            print(f"[MOCK] Image size: {len(png_data)} bytes")
            return

        try:
            # Upload media first
            media_response = self.twitter.upload_media(png_data, f"boun_{token_id}.png")
            if not media_response:
                print(f"Failed to upload media for token #{token_id}")
                return

            # Post tweet with media
            tweet_text = f"New Boun minted! #{token_id}"
            if not self.twitter.post_tweet(tweet_text, media_response.media_id):
                print(f"Failed to post tweet for token #{token_id}")
                return

        except Exception as e:
            print(f"Error posting tweet for token #{token_id}: {e}")

    def main_loop(self):
        """Main bot loop"""
        print("###~~~ BOUNS BOT ~~~###")
        
        # Initialize with current auction
        last_noun_id = self._get_current_auction().noun_id
        print(f"Starting with noun ID: {last_noun_id}")

        while True:
            try:
                # Get current auction data
                current_auction = self._get_current_auction()
                
                # Check if we have a new noun
                if current_auction.noun_id > last_noun_id:
                    print(f"New Boun detected! {last_noun_id} -> {current_auction.noun_id}")
                    
                    try:
                        # Fetch URI with retries
                        max_retries = 5
                        retry_delay = 1  # Initial delay in seconds
                        for attempt in range(max_retries):
                            try:
                                print(f"Fetching tokenURI for {current_auction.noun_id}, attempt {attempt + 1}/{max_retries}")
                                uri = self.nft_contract.functions.tokenURI(current_auction.noun_id).call()
                                break  # Success, exit retry loop
                            except Exception as e:
                                if attempt == max_retries - 1:  # Last attempt
                                    raise  # Re-raise the last exception
                                print(f"Failed to fetch tokenURI for {current_auction.noun_id} (attempt {attempt + 1}/{max_retries}): {e}")
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff

                        svg_bytes = self.get_svg(uri)
                        png_bytes = self.svg_to_png(svg_bytes)
                        
                        print(f"Tweeting about Boun #{current_auction.noun_id}")
                        self.post_tweet(png_bytes, current_auction.noun_id)
                        
                    except Exception as e:
                        print(f"Error processing Boun {current_auction.noun_id}: {e}")
                    
                    last_noun_id = current_auction.noun_id
                
            except Exception as e:
                print(f"Error in main loop: {e}")

            # Calculate sleep time based on auction state
            sleep_time = self._calculate_sleep_time(current_auction)
            time.sleep(sleep_time)

if __name__ == "__main__":
    bot = BounsBot()
    bot.main_loop() 