#!/usr/bin/env python3
"""
Main entry point for the Abdominal Wall Weekly Research Review system.
Supports both one-time execution and continuous scheduling.
"""

import os
import sys
import logging
import schedule
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from pubmed_search import PubMedSearcher, format_articles_for_email, save_results
from email_sender import ResearchEmailSender

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_review.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ResearchReviewAgent:
    """Main agent coordinating search and email delivery."""
    
    def __init__(self):
        self.searcher = PubMedSearcher()
        self.email_sender = ResearchEmailSender()
        self._configure_from_env()
    
    def _configure_from_env(self):
        """Load configuration from environment variables."""
        # PubMed/NCBI settings
        self.searcher.email = os.getenv('NCBI_EMAIL', 'research@example.com')
        self.searcher.api_key = os.getenv('NCBI_API_KEY')
        
        # Email settings
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if sender_email and sender_password:
            self.email_sender.set_credentials(sender_email, sender_password)
        else:
            logger.warning("Email credentials not configured. Email sending will be disabled.")
        
        # Search parameters
        self.days_back = int(os.getenv('DAYS_BACK', '7'))
        self.max_results = int(os.getenv('MAX_RESULTS', '50'))
        
        # Recipients
        recipients_str = os.getenv('RECIPIENT_EMAILS', '')
        self.recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]
    
    def run_research_review(self):
        """Execute complete research review workflow."""
        logger.info("=" * 80)
        logger.info("Starting Research Review Workflow")
        logger.info("=" * 80)
        
        try:
            # Step 1: Search PubMed
            logger.info(f"Searching PubMed for articles from past {self.days_back} days...")
            articles = self.searcher.run_weekly_search(max_results=self.max_results)
            
            if not articles:
                logger.warning("No articles found in this search")
                return False
            
            logger.info(f"Found {len(articles)} articles")
            
            # Step 2: Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"search_results_{timestamp}.json"
            save_results(articles, results_file)
            
            # Also update the latest results file
            save_results(articles, "latest_search_results.json")
            
            # Step 3: Display results
            formatted = format_articles_for_email(articles)
            logger.info("Search Results Preview:")
            logger.info(formatted)
            
            # Step 4: Send email if configured
            if self.recipients and self.email_sender.sender_email:
                logger.info(f"Sending email to {len(self.recipients)} recipient(s)...")
                subject = f"Weekly Hernia Research Review - {len(articles)} New Articles"
                success = self.email_sender.send_email(self.recipients, subject, articles)
                if success:
                    logger.info("Email sent successfully")
                else:
                    logger.error("Failed to send email")
                    return False
            else:
                logger.warning("Email recipients or credentials not configured. Skipping email.")
            
            logger.info("=" * 80)
            logger.info("Research Review Workflow Completed Successfully")
            logger.info("=" * 80)
            return True
            
        except Exception as e:
            logger.error(f"Error during research review workflow: {e}", exc_info=True)
            return False
    
    def schedule_weekly(self, day: str = "monday", hour: int = 9, minute: int = 0):
        """
        Schedule weekly research reviews.
        
        Args:
            day: Day of week ('monday', 'tuesday', etc.)
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
        """
        day_map = {
            'monday': schedule.every().monday,
            'tuesday': schedule.every().tuesday,
            'wednesday': schedule.every().wednesday,
            'thursday': schedule.every().thursday,
            'friday': schedule.every().friday,
            'saturday': schedule.every().saturday,
            'sunday': schedule.every().sunday,
        }
        
        if day.lower() not in day_map:
            raise ValueError(f"Invalid day: {day}")
        
        job = day_map[day.lower()].at(f"{hour:02d}:{minute:02d}").do(self.run_research_review)
        logger.info(f"Scheduled weekly research review for {day.capitalize()} at {hour:02d}:{minute:02d}")
        
        return job
    
    def run_scheduler(self):
        """Run continuous scheduler."""
        logger.info("Starting scheduler... Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
    
    def run_once(self):
        """Run research review once."""
        return self.run_research_review()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Abdominal Wall Weekly Research Review System'
    )
    parser.add_argument(
        '--mode',
        choices=['once', 'schedule'],
        default='once',
        help='Run mode: once (default) or schedule'
    )
    parser.add_argument(
        '--day',
        default='monday',
        help='Day to schedule (e.g., monday, tuesday)'
    )
    parser.add_argument(
        '--hour',
        type=int,
        default=9,
        help='Hour to run (0-23, default: 9)'
    )
    parser.add_argument(
        '--minute',
        type=int,
        default=0,
        help='Minute to run (0-59, default: 0)'
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = ResearchReviewAgent()
    
    # Run based on mode
    if args.mode == 'once':
        success = agent.run_once()
        sys.exit(0 if success else 1)
    else:
        agent.schedule_weekly(day=args.day, hour=args.hour, minute=args.minute)
        agent.run_scheduler()


if __name__ == "__main__":
    main()
