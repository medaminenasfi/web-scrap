#!/usr/bin/env python3
"""
Test script to verify video quality prioritization works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from universal_scraper import get_best_video_source

def test_video_prioritization():
    """Test the video quality prioritization function captures all videos"""
    
    # Sample video sources that might be found on a responsive website
    test_videos = [
        {"src": "https://example.com/video_mobile_360.mp4", "type": "video/mp4", "width": "", "height": "", "attributes": {"source": "dom"}},
        {"src": "https://example.com/video_720p.mp4", "type": "video/mp4", "width": "", "height": "", "attributes": {"source": "dom"}},
        {"src": "https://example.com/video_1080p.mp4", "type": "video/mp4", "width": "", "height": "", "attributes": {"source": "dom"}},
        {"src": "https://example.com/video_low.webm", "type": "video/webm", "width": "", "height": "", "attributes": {"source": "dom"}},
        {"src": "https://example.com/video_hd.mp4", "type": "video/mp4", "width": "", "height": "", "attributes": {"source": "network"}},
    ]
    
    print(f"Original video sources ({len(test_videos)} total):")
    for i, video in enumerate(test_videos, 1):
        print(f"  {i}. {video['src']}")
    
    # Apply prioritization
    prioritized = get_best_video_source(test_videos, "https://example.com")
    
    print(f"\nPrioritized video sources ({len(prioritized)} total):")
    for i, video in enumerate(prioritized, 1):
        print(f"  {i}. {video['src']}")
    
    # Verify all videos are captured
    success = len(prioritized) == len(test_videos)
    print(f"\nAll videos captured: {success}")
    
    # Verify quality prioritization (highest quality first)
    expected_keywords = ["1080", "hd", "720"]
    quality_success = True
    
    print(f"\nTesting quality prioritization (first 3 should be highest quality):")
    for i, video in enumerate(prioritized[:3], 1):
        src_lower = video['src'].lower()
        found_quality = any(keyword in src_lower for keyword in expected_keywords)
        print(f"  Video {i}: {video['src']} - High quality: {found_quality}")
        if not found_quality:
            quality_success = False
    
    overall_success = success and quality_success
    print(f"\nTest {'PASSED' if overall_success else 'FAILED'}")
    print("The scraper should now capture ALL videos while prioritizing quality!")
    
    return overall_success

if __name__ == "__main__":
    test_video_prioritization()
