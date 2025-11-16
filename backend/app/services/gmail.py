"""Gmail API service for email ingestion and sending."""

import base64
import os
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

from app.core.config import settings


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailService:
    """Gmail API service for email operations."""

    def __init__(self):
        """Initialize Gmail service with credentials."""
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        # Token file stores the user's access and refresh tokens
        if os.path.exists(settings.GMAIL_TOKEN_PATH):
            with open(settings.GMAIL_TOKEN_PATH, "rb") as token:
                self.creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GMAIL_CREDENTIALS_PATH, SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(settings.GMAIL_TOKEN_PATH, "wb") as token:
                pickle.dump(self.creds, token)

        # Build the service
        self.service = build("gmail", "v1", credentials=self.creds)

    def get_unprocessed_messages(self, label: str = "INBOX") -> List[Dict[str, Any]]:
        """
        Get unprocessed messages from inbox.

        Args:
            label: Gmail label to filter by

        Returns:
            List of message metadata
        """
        try:
            # Get or create "processed" label
            processed_label_id = self._get_or_create_label("processed")

            # Search for messages in inbox that don't have "processed" label
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=[label],
                    q=f"-label:{processed_label_id}",
                    maxResults=50,
                )
                .execute()
            )

            messages = results.get("messages", [])
            return messages

        except Exception as e:
            print(f"Error getting unprocessed messages: {str(e)}")
            return []

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full message details.

        Args:
            message_id: Gmail message ID

        Returns:
            Full message object or None
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return message
        except Exception as e:
            print(f"Error getting message {message_id}: {str(e)}")
            return None

    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gmail message into structured format.

        Args:
            message: Gmail message object

        Returns:
            Parsed message with from, to, subject, body, etc.
        """
        headers = message.get("payload", {}).get("headers", [])

        # Extract headers
        parsed = {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "from": self._get_header(headers, "From"),
            "to": self._get_header(headers, "To"),
            "subject": self._get_header(headers, "Subject"),
            "date": self._get_header(headers, "Date"),
            "in_reply_to": self._get_header(headers, "In-Reply-To"),
            "body_text": "",
            "raw_metadata": message,
        }

        # Extract body
        parsed["body_text"] = self._get_message_body(message)

        return parsed

    def _get_message_body(self, message: Dict[str, Any]) -> str:
        """Extract plain text body from message."""
        payload = message.get("payload", {})

        # Check if message has parts (multipart)
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    return base64.urlsafe_b64decode(data).decode("utf-8")
        else:
            # Single part message
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8")

        return ""

    def _get_header(self, headers: List[Dict[str, str]], name: str) -> Optional[str]:
        """Extract header value by name."""
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value")
        return None

    def mark_as_processed(self, message_id: str):
        """
        Mark a message as processed by adding custom label.

        Args:
            message_id: Gmail message ID
        """
        try:
            processed_label_id = self._get_or_create_label("processed")

            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": [processed_label_id]},
            ).execute()

        except Exception as e:
            print(f"Error marking message as processed: {str(e)}")

    def _get_or_create_label(self, label_name: str) -> str:
        """
        Get or create a Gmail label.

        Args:
            label_name: Label name

        Returns:
            Label ID
        """
        try:
            # Get existing labels
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])

            # Check if label exists
            for label in labels:
                if label["name"].lower() == label_name.lower():
                    return label["id"]

            # Create label if it doesn't exist
            label = (
                self.service.users()
                .labels()
                .create(
                    userId="me",
                    body={
                        "name": label_name,
                        "labelListVisibility": "labelShow",
                        "messageListVisibility": "show",
                    },
                )
                .execute()
            )

            return label["id"]

        except Exception as e:
            print(f"Error getting/creating label: {str(e)}")
            return ""

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send an email via Gmail.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)
            thread_id: Optional thread ID to reply to
            in_reply_to: Optional message ID for In-Reply-To header

        Returns:
            Sent message ID or None
        """
        try:
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            if in_reply_to:
                message["In-Reply-To"] = in_reply_to
                message["References"] = in_reply_to

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            send_message = {"raw": raw_message}
            if thread_id:
                send_message["threadId"] = thread_id

            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=send_message)
                .execute()
            )

            return result.get("id")

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return None
