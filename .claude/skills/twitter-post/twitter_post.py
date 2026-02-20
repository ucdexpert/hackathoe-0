#!/usr/bin/env python3
"""
Twitter Post Skill - Create tweets with Twitter API v2

Usage:
    python twitter_post.py --action post --content "Your tweet content"
    python twitter_post.py --action history --count 10
    python twitter_post.py --action delete --tweet-id 1234567890

Requirements:
    pip install tweepy
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import tweepy
    Tweepy_AVAILABLE = True
except ImportError:
    Tweepy_AVAILABLE = False
    print("WARNING: tweepy not installed. Install with: pip install tweepy")


class TwitterClient:
    """Twitter API client for posting and retrieving tweets."""

    def __init__(self):
        """Initialize Twitter client."""
        self.client = None
        self.api = None
        self.vault_root = Path(__file__).parent.parent.parent
        self.reports_dir = self.vault_root / "Reports"
        self.logs_dir = self.vault_root / "Logs"
        self.twitter_log = self.reports_dir / "twitter_log.md"
        self.error_log = self.logs_dir / "twitter.log"

        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with Twitter API."""
        if not Tweepy_AVAILABLE:
            self._log_error("tweepy library not available")
            return False

        api_key = os.environ.get('TWITTER_API_KEY')
        api_secret = os.environ.get('TWITTER_API_SECRET')
        access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        access_secret = os.environ.get('TWITTER_ACCESS_SECRET')
        bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')

        if not all([api_key, api_secret, access_token, access_secret]):
            self._log_error("Twitter credentials not fully configured")
            return False

        try:
            # OAuth 1.0a for posting
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret,
                access_token, access_secret
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)

            # Twitter API v2 client for additional features
            if bearer_token:
                self.client = tweepy.Client(
                    bearer_token=bearer_token,
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret,
                    wait_on_rate_limit=True
                )
            else:
                self.client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret,
                    wait_on_rate_limit=True
                )

            # Verify credentials
            self.api.verify_credentials()
            self._log_activity("authenticated", {"status": "success"})
            return True

        except Exception as e:
            self._log_error(f"Authentication failed: {str(e)}")
            return False

    def _log_error(self, message: str):
        """Log error to file."""
        try:
            with open(self.error_log, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - ERROR - {message}\n")
        except Exception:
            pass

    def _log_activity(self, action: str, details: Dict[str, Any], status: str = 'success'):
        """Log activity to twitter_log.md."""
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        month_str = timestamp.strftime('%Y-%m-%B')

        # Read or create log file
        if self.twitter_log.exists():
            with open(self.twitter_log, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = f"# Twitter Activity Log\n\n"

        # Check if we need new month section
        if month_str not in content:
            content += f"\n## {month_str.replace('-', ' ')}\n\n"
            content += "| Date | Time | Action | Content | Status | Tweet ID |\n"
            content += "|------|------|--------|---------|--------|----------|\n"

        # Add table row
        content_preview = details.get('content', '')[:50].replace('|', '-')
        if len(details.get('content', '')) > 50:
            content_preview += '...'

        tweet_id = details.get('tweet_id', 'N/A')
        content += f"| {date_str} | {time_str} | {action} | {content_preview} | {status.upper()} | {tweet_id} |\n"

        # Add detailed section for posts
        if action == 'POST' and status == 'success':
            content += f"\n---\n\n### Tweet ID: {tweet_id}\n"
            content += f"**Posted:** {date_str} {time_str}\n"
            content += f"**Content:** {details.get('content', '')}\n"
            if details.get('hashtags'):
                content += f"**Hashtags:** {', '.join(details['hashtags'])}\n"
            content += f"**Status:** {status.upper()}\n\n---\n"

        # Write back
        with open(self.twitter_log, 'w', encoding='utf-8') as f:
            f.write(content)

    def post_tweet(self, content: str, hashtags: List[str] = None) -> Dict[str, Any]:
        """
        Post a tweet to Twitter.

        Args:
            content: Tweet text (max 280 characters)
            hashtags: List of hashtags (without # symbol)

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'tweet_id': None,
            'tweet_url': None,
            'error': None
        }

        # Validate content
        if not content or len(content.strip()) == 0:
            result['error'] = 'Tweet content is required'
            self._log_activity('POST', {'content': content}, 'error')
            return result

        if len(content) > 280:
            result['error'] = 'Content exceeds 280 character limit'
            self._log_activity('POST', {'content': content[:280]}, 'error')
            return result

        # Format content with hashtags
        full_content = content
        if hashtags:
            hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
            # Ensure total length doesn't exceed 280
            if len(full_content) + len(hashtag_str) + 1 <= 280:
                full_content = f"{content} {hashtag_str}"
            else:
                # Truncate content to fit hashtags
                max_content_len = 280 - len(hashtag_str) - 1
                full_content = f"{content[:max_content_len]} {hashtag_str}"

        if not self.api:
            result['error'] = 'Twitter client not authenticated'
            self._log_activity('POST', {'content': full_content}, 'error')
            return result

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Post tweet using API v2
                response = self.client.create_tweet(text=full_content)
                tweet_id = response.data['id']

                result['success'] = True
                result['tweet_id'] = tweet_id
                result['tweet_url'] = f'https://twitter.com/user/status/{tweet_id}'

                self._log_activity('POST', {
                    'content': full_content,
                    'tweet_id': tweet_id,
                    'hashtags': hashtags or []
                }, 'success')

                return result

            except tweepy.errors.TooManyRequests:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(60)  # Wait 1 minute before retry
                else:
                    result['error'] = 'Rate limit exceeded'
                    self._log_error(f"Rate limit exceeded: {full_content[:100]}")

            except Exception as e:
                result['error'] = str(e)
                self._log_error(f"Post failed: {str(e)}")
                break

        self._log_activity('POST', {'content': full_content}, 'error')
        return result

    def get_tweet_history(self, count: int = 10) -> Dict[str, Any]:
        """
        Get recent tweets from the authenticated account.

        Args:
            count: Number of tweets to retrieve (max 100)

        Returns:
            Dict with tweet list
        """
        result = {
            'success': False,
            'tweets': [],
            'error': None
        }

        if not self.client:
            result['error'] = 'Twitter client not authenticated'
            return result

        count = min(count, 100)  # API limit

        try:
            # Get authenticated user's ID
            me = self.client.get_me()
            user_id = me.data.id

            # Get user's tweets
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=count,
                tweet_fields=['created_at', 'text', 'public_metrics']
            )

            if response.data:
                tweets = []
                for tweet in response.data:
                    tweets.append({
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'metrics': {
                            'retweets': tweet.public_metrics.get('retweet_count', 0),
                            'likes': tweet.public_metrics.get('like_count', 0),
                            'replies': tweet.public_metrics.get('reply_count', 0),
                            'quotes': tweet.public_metrics.get('quote_count', 0)
                        }
                    })

                result['success'] = True
                result['tweets'] = tweets
                result['count'] = len(tweets)

        except Exception as e:
            result['error'] = str(e)
            self._log_error(f"Get history failed: {str(e)}")

        return result

    def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """
        Delete a tweet.

        Args:
            tweet_id: ID of tweet to delete

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'error': None
        }

        if not self.client:
            result['error'] = 'Twitter client not authenticated'
            return result

        try:
            self.client.delete_tweet(id=tweet_id)
            result['success'] = True

            self._log_activity('DELETE', {'tweet_id': tweet_id}, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_error(f"Delete failed: {str(e)}")
            self._log_activity('DELETE', {'tweet_id': tweet_id}, 'error')

        return result


# ============================================================================
# Skill Entry Point
# ============================================================================

def twitter_post_skill(action: str, **kwargs) -> Dict[str, Any]:
    """
    Main entry point for the twitter-post skill.

    Args:
        action: Action to perform (post, history, delete)
        **kwargs: Action-specific parameters

    Returns:
        Result dictionary
    """
    client = TwitterClient()

    if action == 'post':
        return client.post_tweet(
            content=kwargs.get('content', ''),
            hashtags=kwargs.get('hashtags', [])
        )

    elif action == 'history':
        return client.get_tweet_history(
            count=kwargs.get('count', 10)
        )

    elif action == 'delete':
        return client.delete_tweet(
            tweet_id=kwargs.get('tweet_id')
        )

    else:
        return {
            'success': False,
            'error': f"Unknown action: {action}. Valid actions: post, history, delete"
        }


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Twitter Post Skill')
    parser.add_argument('--action', '-a', required=True,
                       choices=['post', 'history', 'delete'],
                       help='Action to perform')
    parser.add_argument('--content', '-c', help='Tweet content')
    parser.add_argument('--hashtags', '-t', nargs='*', help='Hashtags (without #)')
    parser.add_argument('--tweet-id', '-i', help='Tweet ID for deletion')
    parser.add_argument('--count', '-n', type=int, default=10, help='Number of tweets')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    result = twitter_post_skill(
        action=args.action,
        content=args.content,
        hashtags=args.hashtags,
        tweet_id=args.tweet_id,
        count=args.count
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result['success']:
            print(f"SUCCESS: {args.action.title()} completed")
            if 'tweet_url' in result and result['tweet_url']:
                print(f"Tweet URL: {result['tweet_url']}")
            if 'tweets' in result:
                for tweet in result['tweets'][:5]:
                    print(f"  - {tweet['text'][:50]}...")
        else:
            print(f"ERROR: {result.get('error', 'Unknown error')}")

    sys.exit(0 if result['success'] else 1)
