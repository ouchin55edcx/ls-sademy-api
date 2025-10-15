#!/usr/bin/env python3
"""
Review API Test Script

This script demonstrates how to use the Review API endpoints.
Make sure to update the BASE_URL and credentials before running.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "client1"  # Update with your client username
PASSWORD = "client123"  # Update with your client password

class ReviewAPITester:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.auth_token = None
        self.session = requests.Session()
    
    def login(self):
        """Login and get authentication token"""
        print("🔐 Logging in...")
        
        login_data = {
            "username_or_phone": self.username,
            "password": self.password
        }
        
        response = self.session.post(f"{self.base_url}/login/", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('token')
            self.session.headers.update({
                'Authorization': f'Token {self.auth_token}',
                'Content-Type': 'application/json'
            })
            print(f"✅ Login successful! Token: {self.auth_token[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def list_client_reviews(self):
        """List all reviews for the authenticated client"""
        print("\n📋 Listing client reviews...")
        
        response = self.session.get(f"{self.base_url}/client/reviews/")
        
        if response.status_code == 200:
            reviews = response.json()
            print(f"✅ Found {len(reviews)} reviews:")
            for review in reviews:
                print(f"  - Review {review['id']}: {review['rating']} stars for Order {review['order_id']}")
                print(f"    Comment: {review['comment'][:50]}...")
                print(f"    Can be updated: {review['can_be_updated']}")
        else:
            print(f"❌ Failed to list reviews: {response.status_code} - {response.text}")
    
    def create_review(self, order_id, rating, comment):
        """Create a new review"""
        print(f"\n✍️ Creating review for Order {order_id}...")
        
        review_data = {
            "order": order_id,
            "rating": rating,
            "comment": comment
        }
        
        response = self.session.post(f"{self.base_url}/client/reviews/", json=review_data)
        
        if response.status_code == 201:
            review = response.json()
            print(f"✅ Review created successfully!")
            print(f"  - Review ID: {review['id']}")
            print(f"  - Rating: {review['rating']} stars")
            print(f"  - Comment: {review['comment']}")
            print(f"  - Can be updated: {review['can_be_updated']}")
            return review
        else:
            print(f"❌ Failed to create review: {response.status_code} - {response.text}")
            return None
    
    def get_review_details(self, review_id):
        """Get details of a specific review"""
        print(f"\n🔍 Getting review details for Review {review_id}...")
        
        response = self.session.get(f"{self.base_url}/client/reviews/{review_id}/")
        
        if response.status_code == 200:
            review = response.json()
            print(f"✅ Review details:")
            print(f"  - ID: {review['id']}")
            print(f"  - Order ID: {review['order_id']}")
            print(f"  - Service: {review['service_name']}")
            print(f"  - Rating: {review['rating']} stars")
            print(f"  - Comment: {review['comment']}")
            print(f"  - Created: {review['date']}")
            print(f"  - Updated: {review['updated_at']}")
            print(f"  - Can be updated: {review['can_be_updated']}")
        else:
            print(f"❌ Failed to get review details: {response.status_code} - {response.text}")
    
    def update_review(self, review_id, rating=None, comment=None):
        """Update an existing review"""
        print(f"\n✏️ Updating review {review_id}...")
        
        update_data = {}
        if rating is not None:
            update_data['rating'] = rating
        if comment is not None:
            update_data['comment'] = comment
        
        response = self.session.patch(f"{self.base_url}/client/reviews/{review_id}/", json=update_data)
        
        if response.status_code == 200:
            review = response.json()
            print(f"✅ Review updated successfully!")
            print(f"  - New rating: {review['rating']} stars")
            print(f"  - New comment: {review['comment']}")
            print(f"  - Updated at: {review['updated_at']}")
        else:
            print(f"❌ Failed to update review: {response.status_code} - {response.text}")
    
    def delete_review(self, review_id):
        """Delete a review"""
        print(f"\n🗑️ Deleting review {review_id}...")
        
        response = self.session.delete(f"{self.base_url}/client/reviews/{review_id}/")
        
        if response.status_code == 200:
            print(f"✅ Review deleted successfully!")
        else:
            print(f"❌ Failed to delete review: {response.status_code} - {response.text}")
    
    def get_public_reviews(self, service_id=None, rating=None):
        """Get public reviews with optional filtering"""
        print(f"\n🌐 Getting public reviews...")
        
        params = {}
        if service_id:
            params['service_id'] = service_id
        if rating:
            params['rating'] = rating
        
        response = self.session.get(f"{self.base_url}/reviews/", params=params)
        
        if response.status_code == 200:
            reviews = response.json()
            print(f"✅ Found {len(reviews)} public reviews:")
            for review in reviews[:5]:  # Show first 5
                print(f"  - Review {review['id']}: {review['rating']} stars for {review['service_name']}")
                print(f"    By: {review['client_name']}")
                print(f"    Comment: {review['comment'][:50]}...")
        else:
            print(f"❌ Failed to get public reviews: {response.status_code} - {response.text}")
    
    def get_review_statistics(self):
        """Get review statistics"""
        print(f"\n📊 Getting review statistics...")
        
        response = self.session.get(f"{self.base_url}/reviews/statistics/")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Review statistics:")
            print(f"  - Total reviews: {stats['total_reviews']}")
            print(f"  - Average rating: {stats['average_rating']}")
            print(f"  - Services with reviews: {stats['services_with_reviews']}")
            print(f"  - Rating distribution:")
            for rating, count in stats['rating_distribution'].items():
                print(f"    {rating} stars: {count} reviews")
        else:
            print(f"❌ Failed to get statistics: {response.status_code} - {response.text}")

def main():
    """Main test function"""
    print("🚀 Review API Test Script")
    print("=" * 50)
    
    # Initialize tester
    tester = ReviewAPITester(BASE_URL, USERNAME, PASSWORD)
    
    # Login
    if not tester.login():
        print("❌ Cannot proceed without authentication")
        return
    
    # Test public endpoints first
    tester.get_public_reviews()
    tester.get_review_statistics()
    
    # Test client endpoints
    tester.list_client_reviews()
    
    # Test creating a review (update order_id as needed)
    # Note: This will only work if you have a completed order that meets all requirements
    # tester.create_review(order_id=1, rating=5, comment="Test review from API script")
    
    # Test getting review details (update review_id as needed)
    # tester.get_review_details(review_id=1)
    
    # Test updating a review (update review_id as needed)
    # tester.update_review(review_id=1, rating=4, comment="Updated test review")
    
    # Test deleting a review (update review_id as needed)
    # tester.delete_review(review_id=1)
    
    print("\n✅ Test script completed!")
    print("\nNote: Some tests are commented out because they require specific data.")
    print("Uncomment and update the IDs as needed for your specific test data.")

if __name__ == "__main__":
    main()
