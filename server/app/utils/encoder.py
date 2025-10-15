"""
Utility functions for encoding and decoding data.
"""
import base64
from typing import Optional


class Base64Encoder:
    """Handles Base64 encoding and decoding operations."""
    
    @staticmethod
    def encode(text: str) -> str:
        """
        Encodes a string to Base64.
        
        Args:
            text: The string to encode.
            
        Returns:
            str: Base64 encoded string.
        """
        if not text:
            return ""
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")
    
    @staticmethod
    def decode(encoded_text: str) -> str:
        """
        Decodes a Base64 string.
        
        Args:
            encoded_text: The Base64 encoded string.
            
        Returns:
            str: Decoded string.
            
        Raises:
            ValueError: If the input is not valid Base64.
        """
        if not encoded_text:
            return ""
        try:
            return base64.b64decode(encoded_text).decode("utf-8")
        except (ValueError, TypeError, base64.binascii.Error) as e:
            raise ValueError(f"Invalid Base64 data: {e}")
    
    @staticmethod
    def encode_optional(text: Optional[str]) -> Optional[str]:
        """
        Encodes an optional string to Base64.
        
        Args:
            text: The optional string to encode.
            
        Returns:
            Optional[str]: Base64 encoded string or None.
        """
        if text is None:
            return None
        return Base64Encoder.encode(text)
    
    @staticmethod
    def decode_optional(encoded_text: Optional[str]) -> Optional[str]:
        """
        Decodes an optional Base64 string.
        
        Args:
            encoded_text: The optional Base64 encoded string.
            
        Returns:
            Optional[str]: Decoded string or None.
            
        Raises:
            ValueError: If the input is not valid Base64.
        """
        if encoded_text is None:
            return None
        return Base64Encoder.decode(encoded_text)
