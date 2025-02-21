import tweepy
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from io import BytesIO 

@dataclass
class MediaUploadResponse:
    media_id: str
    media_key: Optional[str] = None

class TwitterAdapter:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str
    ):
        """Initialize Tweepy client with OAuth 1.0a credentials"""
        if not all([api_key, api_secret, access_token, access_secret]):
            raise ValueError("Must provide all OAuth credentials")
        
        # Create auth handler
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret,
            access_token, access_secret
        )
        
        # Create API v1.1 instance (needed for media upload)
        self.api = tweepy.API(auth)
        
        # Create v2 client
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )

    def upload_media(self, media_data: bytes, filename: str = "image.png") -> Optional[MediaUploadResponse]:
        """
        Uploads media to Twitter.
        Returns MediaUploadResponse if successful, None if failed.
        """
        try:
            # Convert bytes to file-like object
            media_file = BytesIO(media_data)

            # Upload the media using v1.1 API
            media = self.api.media_upload(
                filename=filename,
                file=media_file
            )
            
            return MediaUploadResponse(
                media_id=str(media.media_id),
                media_key=getattr(media, 'media_key', None)
            )

        except Exception as e:
            print(f"Error uploading media: {e}")
            return None

    def post_tweet(self, text: str, media_id: Optional[str] = None) -> bool:
        """
        Posts a tweet with optional media.
        Returns True if successful, False otherwise.
        """
        try:
            # Prepare the media IDs if provided
            media_ids = [media_id] if media_id else None
            
            # Create the tweet using v2 endpoint
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids
            )
            
            print(f"Successfully posted tweet: {text}")
            return True

        except Exception as e:
            print(f"Error posting tweet: {e}")
            return False 
        