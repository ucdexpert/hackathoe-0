#!/usr/bin/env python3
"""
Social Media Poster - Facebook and Instagram posting via Graph API

Usage:
    python social_poster.py --platform facebook --action post --content "Your post"
    python social_poster.py --platform instagram --action post --content "Caption" --image-url "https://example.com/image.jpg"
    python social_poster.py --platform facebook --action insights --since 2026-02-01

Requirements:
    pip install requests
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import SocialMediaConfig


class SocialMediaPoster:
    """Facebook and Instagram posting via Graph API."""

    def __init__(self):
        """Initialize social media poster."""
        self.config = SocialMediaConfig()
        self.vault_root = Path(__file__).parent.parent.parent
        self.logs_dir = self.vault_root / "Logs"
        self.social_log = self.logs_dir / "social.log"

        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Graph API base URL
        self.graph_url = "https://graph.facebook.com/v18.0"

    def _log_activity(self, platform: str, action: str, details: Dict[str, Any], status: str = 'success'):
        """Log activity to social.log in JSON Lines format."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'action': action,
            'status': status,
            'details': details
        }

        try:
            with open(self.social_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        except Exception as e:
            print(f"Failed to log activity: {e}")

    def _make_request(self, endpoint: str, params: Dict = None, data: Dict = None,
                      method: str = 'GET') -> Dict[str, Any]:
        """Make a request to Facebook Graph API."""
        url = f"{self.graph_url}/{endpoint}"

        if params is None:
            params = {}

        # Add access token
        if self.config.FACEBOOK_PAGE_ACCESS_TOKEN:
            params['access_token'] = self.config.FACEBOOK_PAGE_ACCESS_TOKEN

        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, params=params, data=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                except:
                    pass
            return {'error': error_msg}

    def post_facebook(self, content: str, image_path: str = None) -> Dict[str, Any]:
        """
        Post to Facebook Page.

        Args:
            content: Post content/caption
            image_path: Optional path to image file

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'post_id': None,
            'post_url': None,
            'error': None
        }

        # Validate configuration
        if not self.config.is_facebook_configured():
            result['error'] = 'Facebook credentials not configured'
            self._log_activity('facebook', 'post', {'content': content[:100]}, 'error')
            return result

        # Validate content
        if not content or len(content.strip()) == 0:
            result['error'] = 'Post content is required'
            self._log_activity('facebook', 'post', {}, 'error')
            return result

        try:
            if image_path:
                # Post with photo
                if not Path(image_path).exists():
                    result['error'] = f'Image file not found: {image_path}'
                    self._log_activity('facebook', 'post', {'image_path': image_path}, 'error')
                    return result

                # Upload photo
                with open(image_path, 'rb') as f:
                    files = {'source': f}
                    data = {
                        'message': content,
                        'access_token': self.config.FACEBOOK_PAGE_ACCESS_TOKEN
                    }

                    response = requests.post(
                        f"{self.graph_url}/{self.config.FACEBOOK_PAGE_ID}/photos",
                        data=data,
                        files=files,
                        timeout=60
                    )

                    response.raise_for_status()
                    response_data = response.json()
            else:
                # Text-only post
                endpoint = f"{self.config.FACEBOOK_PAGE_ID}/feed"
                response_data = self._make_request(
                    endpoint,
                    data={'message': content},
                    method='POST'
                )

            if 'error' in response_data:
                result['error'] = response_data['error'].get('message', 'Unknown error')
                self._log_activity('facebook', 'post', {'content': content[:100]}, 'error')
                return result

            post_id = response_data.get('id')
            result['success'] = True
            result['post_id'] = post_id
            result['post_url'] = f'https://facebook.com/{self.config.FACEBOOK_PAGE_ID}/posts/{post_id.split("_")[1] if "_" in post_id else post_id}'

            self._log_activity('facebook', 'post', {
                'content': content[:100],
                'post_id': post_id,
                'has_image': bool(image_path)
            }, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('facebook', 'post', {'content': content[:100], 'error': str(e)}, 'error')

        return result

    def post_instagram(self, content: str, image_path: str = None) -> Dict[str, Any]:
        """
        Post to Instagram Business account.

        Args:
            content: Post caption
            image_path: Path to image file (required for Instagram)

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'media_id': None,
            'media_url': None,
            'error': None
        }

        # Validate configuration
        if not self.config.is_instagram_configured():
            result['error'] = 'Instagram credentials not configured'
            self._log_activity('instagram', 'post', {'content': content[:100]}, 'error')
            return result

        # Instagram requires an image
        if not image_path:
            result['error'] = 'Image path is required for Instagram posts'
            self._log_activity('instagram', 'post', {}, 'error')
            return result

        if not Path(image_path).exists():
            result['error'] = f'Image file not found: {image_path}'
            self._log_activity('instagram', 'post', {'image_path': image_path}, 'error')
            return result

        try:
            # Note: Instagram Graph API requires a publicly accessible image URL
            # For local files, you need to upload to a CDN first
            result['error'] = 'Instagram posting requires image to be hosted at a public URL. Use image_url parameter or upload to CDN first.'
            result['requires_public_url'] = True

            self._log_activity('instagram', 'post', {
                'content': content[:100],
                'image_path': image_path,
                'note': 'Requires public image URL'
            }, 'pending')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('instagram', 'post', {'content': content[:100], 'error': str(e)}, 'error')

        return result

    def post_instagram_direct(self, content: str, image_url: str) -> Dict[str, Any]:
        """
        Post to Instagram using a publicly accessible image URL.

        Args:
            content: Post caption
            image_url: Publicly accessible URL to image

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'media_id': None,
            'media_url': None,
            'error': None
        }

        if not self.config.is_instagram_configured():
            result['error'] = 'Instagram credentials not configured'
            return result

        if not image_url:
            result['error'] = 'Image URL is required'
            return result

        try:
            # Step 1: Create media container
            endpoint = f"{self.config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
            params = {
                'image_url': image_url,
                'caption': content,
                'access_token': self.config.INSTAGRAM_ACCESS_TOKEN
            }

            response = requests.post(
                f"{self.graph_url}/{endpoint}",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            container_data = response.json()

            if 'error' in container_data:
                result['error'] = container_data['error'].get('message', 'Unknown error')
                return result

            container_id = container_data.get('id')

            # Step 2: Publish the media
            publish_endpoint = f"{self.config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
            publish_params = {
                'creation_id': container_id,
                'access_token': self.config.INSTAGRAM_ACCESS_TOKEN
            }

            response = requests.post(
                f"{self.graph_url}/{publish_endpoint}",
                params=publish_params,
                timeout=30
            )
            response.raise_for_status()
            publish_data = response.json()

            if 'error' in publish_data:
                result['error'] = publish_data['error'].get('message', 'Unknown error')
                return result

            media_id = publish_data.get('id')
            result['success'] = True
            result['media_id'] = media_id
            result['media_url'] = f'https://instagram.com/p/{media_id}'

            self._log_activity('instagram', 'post', {
                'content': content[:100],
                'image_url': image_url,
                'media_id': media_id
            }, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('instagram', 'post', {'content': content[:100], 'error': str(e)}, 'error')

        return result

    def get_facebook_insights(self, since: str = None, until: str = None) -> Dict[str, Any]:
        """
        Get Facebook Page insights.

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)

        Returns:
            Dict with insights
        """
        result = {
            'success': False,
            'insights': {},
            'error': None
        }

        if not self.config.is_facebook_configured():
            result['error'] = 'Facebook credentials not configured'
            return result

        try:
            # Default to last 7 days
            if until is None:
                until = datetime.now().strftime('%Y-%m-%d')
            if since is None:
                since = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            endpoint = f"{self.config.FACEBOOK_PAGE_ID}/insights"
            params = {
                'metric': 'page_impressions,page_reach,page_engaged_users,page_post_engagements',
                'since': since,
                'until': until
            }

            response_data = self._make_request(endpoint, params=params)

            if 'error' in response_data:
                result['error'] = response_data['error'].get('message', 'Unknown error')
                return result

            insights = {}
            for metric in response_data.get('data', []):
                name = metric.get('name')
                values = metric.get('values', [])
                if values:
                    insights[name] = sum(v.get('value', 0) for v in values)

            result['success'] = True
            result['insights'] = insights
            result['period'] = {'since': since, 'until': until}

            self._log_activity('facebook', 'insights', insights, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('facebook', 'insights', {'error': str(e)}, 'error')

        return result

    def get_instagram_insights(self, media_id: str = None) -> Dict[str, Any]:
        """
        Get Instagram media insights.

        Args:
            media_id: Specific media ID (optional, gets account insights if not provided)

        Returns:
            Dict with insights
        """
        result = {
            'success': False,
            'insights': {},
            'error': None
        }

        if not self.config.is_instagram_configured():
            result['error'] = 'Instagram credentials not configured'
            return result

        try:
            if media_id:
                # Get insights for specific media
                endpoint = f"{media_id}/insights"
                params = {
                    'metric': 'impressions,reach,saves,likes,comments'
                }
            else:
                # Get account-level insights
                endpoint = f"{self.config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/insights"
                params = {
                    'metric': 'impressions,reach,profile_views,follower_count'
                }

            response_data = self._make_request(endpoint, params=params)

            if 'error' in response_data:
                result['error'] = response_data['error'].get('message', 'Unknown error')
                return result

            insights = {}
            for metric in response_data.get('data', []):
                name = metric.get('name')
                values = metric.get('values', [])
                if values:
                    insights[name] = values[-1].get('value', 0)

            result['success'] = True
            result['insights'] = insights

            self._log_activity('instagram', 'insights', insights, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('instagram', 'insights', {'error': str(e)}, 'error')

        return result

    def delete_post(self, platform: str, post_id: str) -> Dict[str, Any]:
        """
        Delete a post.

        Args:
            platform: Platform (facebook or instagram)
            post_id: Post/media ID to delete

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'error': None
        }

        if platform == 'facebook':
            if not self.config.is_facebook_configured():
                result['error'] = 'Facebook credentials not configured'
                return result

            response_data = self._make_request(post_id, method='DELETE')

            if 'error' in response_data:
                result['error'] = response_data['error'].get('message', 'Delete failed')
            else:
                result['success'] = response_data.get('success', False)

        elif platform == 'instagram':
            if not self.config.is_instagram_configured():
                result['error'] = 'Instagram credentials not configured'
                return result

            response_data = self._make_request(post_id, method='DELETE')

            if 'error' in response_data:
                result['error'] = response_data['error'].get('message', 'Delete failed')
            else:
                result['success'] = response_data.get('success', False)
        else:
            result['error'] = f'Unknown platform: {platform}'

        self._log_activity(platform, 'delete', {'post_id': post_id}, 'success' if result['success'] else 'error')
        return result


# ============================================================================
# Skill Entry Point
# ============================================================================

def social_meta_skill(platform: str, action: str, **kwargs) -> Dict[str, Any]:
    """
    Main entry point for the social-meta skill.

    Args:
        platform: Platform (facebook, instagram, both)
        action: Action (post, insights, delete)
        **kwargs: Action-specific parameters

    Returns:
        Result dictionary
    """
    poster = SocialMediaPoster()

    if action == 'post':
        content = kwargs.get('content', '')
        image_path = kwargs.get('image_path')
        image_url = kwargs.get('image_url')

        if platform == 'facebook':
            return poster.post_facebook(content, image_path)
        elif platform == 'instagram':
            if image_url:
                return poster.post_instagram_direct(content, image_url)
            else:
                return poster.post_instagram(content, image_path)
        elif platform == 'both':
            fb_result = poster.post_facebook(content, image_path)
            ig_result = {'success': False, 'error': 'Instagram requires separate call with image_url'}

            if image_url:
                ig_result = poster.post_instagram_direct(content, image_url)

            return {
                'facebook': fb_result,
                'instagram': ig_result,
                'platform': 'both'
            }
        else:
            return {'success': False, 'error': f'Unknown platform: {platform}'}

    elif action == 'insights':
        since = kwargs.get('since')
        until = kwargs.get('until')
        media_id = kwargs.get('media_id')

        if platform == 'facebook':
            return poster.get_facebook_insights(since, until)
        elif platform == 'instagram':
            return poster.get_instagram_insights(media_id)
        elif platform == 'both':
            return {
                'facebook': poster.get_facebook_insights(since, until),
                'instagram': poster.get_instagram_insights(media_id)
            }
        else:
            return {'success': False, 'error': f'Unknown platform: {platform}'}

    elif action == 'delete':
        post_id = kwargs.get('post_id')
        return poster.delete_post(platform, post_id)

    else:
        return {'success': False, 'error': f'Unknown action: {action}'}


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Social Media Poster Skill')
    parser.add_argument('--platform', '-p', required=True,
                       choices=['facebook', 'instagram', 'both'],
                       help='Platform to post to')
    parser.add_argument('--action', '-a', required=True,
                       choices=['post', 'insights', 'delete'],
                       help='Action to perform')
    parser.add_argument('--content', '-c', help='Post content/caption')
    parser.add_argument('--image-path', '-i', help='Path to image file')
    parser.add_argument('--image-url', '-u', help='Public URL to image (for Instagram)')
    parser.add_argument('--post-id', '-d', help='Post ID for deletion/insights')
    parser.add_argument('--since', help='Start date for insights (YYYY-MM-DD)')
    parser.add_argument('--until', help='End date for insights (YYYY-MM-DD)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    result = social_meta_skill(
        platform=args.platform,
        action=args.action,
        content=args.content,
        image_path=args.image_path,
        image_url=args.image_url,
        post_id=args.post_id,
        since=args.since,
        until=args.until
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if isinstance(result, dict) and result.get('success'):
            print(f"SUCCESS: {args.action.title()} on {args.platform} completed")
            if 'post_url' in result:
                print(f"Post URL: {result['post_url']}")
            if 'media_url' in result:
                print(f"Media URL: {result['media_url']}")
            if 'insights' in result:
                print(f"Insights: {json.dumps(result['insights'], indent=2)}")
        elif isinstance(result, dict) and 'facebook' in result:
            # Both platforms
            if result['facebook'].get('success'):
                print(f"SUCCESS: Facebook post completed")
            if result['instagram'].get('success'):
                print(f"SUCCESS: Instagram post completed")
        else:
            print(f"ERROR: {result.get('error', 'Unknown error')}")

    sys.exit(0 if (isinstance(result, dict) and result.get('success')) else 1)
