#!/usr/bin/env python3
"""
Email sender module for distributing research summaries.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

logger = logging.getLogger(__name__)


class ResearchEmailSender:
    """Handles email delivery of research summaries."""
    
    def __init__(self):
        self.sender_email = None
        self.sender_password = None
    
    def set_credentials(self, email: str, password: str) -> None:
        """
        Set email credentials.
        
        Args:
            email: Sender email address
            password: Email password or app-specific password
        """
        self.sender_email = email
        self.sender_password = password
    
    def send_email(self, recipients: List[str], subject: str, articles: List[Dict]) -> bool:
        """
        Send research summary email.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject line
            articles: List of article dictionaries
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            logger.error("Email credentials not configured")
            return False
        
        if not recipients:
            logger.error("No recipients specified")
            return False
        
        try:
            # Build email body
            body = self._build_email_body(articles)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = ", ".join(recipients)
            
            # Attach text and HTML versions
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(self._build_html_email(articles), "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            logger.info(f"Connecting to Gmail SMTP server...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, message.as_string())
            
            logger.info(f"Email sent successfully to {len(recipients)} recipient(s)")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("Email authentication failed. Check credentials and app password.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    @staticmethod
    def _build_email_body(articles: List[Dict]) -> str:
        """Build plain text email body."""
        body = "Weekly Hernia Research Review\n"
        body += "=" * 50 + "\n\n"
        body += f"Found {len(articles)} new articles:\n\n"
        
        for i, article in enumerate(articles, 1):
            body += f"{i}. {article.get('title', 'No title')}\n"
            body += f"   Journal: {article.get('journal', 'Unknown')}\n"
            body += f"   Published: {article.get('pubdate', 'Unknown')}\n"
            body += f"   PubMed: {article.get('url', '')}\n"
            
            authors = article.get('authors', [])
            if authors:
                author_list = ", ".join([a.get('name', 'Unknown') for a in authors[:3]])
                if len(authors) > 3:
                    author_list += f", +{len(authors) - 3} more"
                body += f"   Authors: {author_list}\n"
            
            body += "\n"
        
        body += "=" * 50 + "\n"
        body += "This is an automated research review.\n"
        
        return body
    
    @staticmethod
    def _build_html_email(articles: List[Dict]) -> str:
        """Build HTML email body."""
        html = """
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h1>Weekly Hernia Research Review</h1>
                <hr>
        """
        
        html += f"<p>Found <strong>{len(articles)}</strong> new articles:</p>"
        html += "<ol>"
        
        for article in articles:
            html += f"<li><strong>{article.get('title', 'No title')}</strong><br>"
            html += f"<em>Journal:</em> {article.get('journal', 'Unknown')}<br>"
            html += f"<em>Published:</em> {article.get('pubdate', 'Unknown')}<br>"
            html += f"<em>PubMed:</em> <a href='{article.get('url', '')}'>{article.get('url', '')}</a><br>"
            
            authors = article.get('authors', [])
            if authors:
                author_list = ", ".join([a.get('name', 'Unknown') for a in authors[:3]])
                if len(authors) > 3:
                    author_list += f", +{len(authors) - 3} more"
                html += f"<em>Authors:</em> {author_list}<br>"
            
            html += "</li>"
        
        html += """
                </ol>
                <hr>
                <p><small>This is an automated research review.</small></p>
            </body>
        </html>
        """
        
        return html
