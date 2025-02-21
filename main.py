import os
import time
import base64
import json
import cairosvg
from web3 import Web3
from typing import Optional
from dotenv import load_dotenv
from twitter_adapter import TwitterAdapter

class BounsBot:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Load environment variables
        self.rpc_url = os.getenv("RPC_URL")
        self.contract_address = os.getenv("CONTRACT_ADDRESS")
        
        if not self.rpc_url or not self.contract_address:
            raise ValueError("Missing required environment variables: RPC_URL, CONTRACT_ADDRESS")

        # Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Convert contract address to checksum address
        self.contract_address = Web3.to_checksum_address(self.contract_address)
        
        # Load contract ABI and initialize contract
        self.contract = self._initialize_contract()
        
        # Initialize Twitter API
        self._initialize_twitter()

    def _initialize_contract(self):
        # TODO: Load actual ABI from file
        minimal_abi = [
            {
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"type": "uint256"}],
                "name": "tokenURI",
                "outputs": [{"type": "string"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        return self.web3.eth.contract(
            address=self.contract_address,
            abi=minimal_abi
        )

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
        # Initialize old supply (Option B from spec - skip existing tokens)
        old_supply = self.contract.functions.totalSupply().call()
        print(f"Starting with total supply: {old_supply}")

        while True:
            try:
                new_supply = self.contract.functions.totalSupply().call()
                if new_supply > old_supply:
                    print(f"New tokens detected! {old_supply} -> {new_supply}")
                    
                    for token_id in range(old_supply + 1, new_supply + 1):
                        try:
                            # Fetch URI with retries
                            max_retries = 5
                            retry_delay = 1  # Initial delay in seconds
                            for attempt in range(max_retries):
                                try:
                                    uri = self.contract.functions.tokenURI(token_id).call()
                                    break  # Success, exit retry loop
                                except Exception as e:
                                    if attempt == max_retries - 1:  # Last attempt
                                        raise  # Re-raise the last exception
                                    print(f"Failed to fetch tokenURI for {token_id} (attempt {attempt + 1}/{max_retries}): {e}")
                                    time.sleep(retry_delay)
                                    retry_delay *= 2  # Exponential backoff

                            svg_bytes = self.get_svg(uri)
                            png_bytes = self.svg_to_png(svg_bytes)
                            
                            print(f"Tweeting about token #{token_id}")
                            self.post_tweet(png_bytes, token_id)
                        except Exception as e:
                            print(f"Error processing token {token_id}: {e}")
                    
                    old_supply = new_supply
                
            except Exception as e:
                print(f"Error in main loop: {e}")

            # Sleep for 5 minutes
            time.sleep(300)

if __name__ == "__main__":
    bot = BounsBot()
    bot.main_loop() 