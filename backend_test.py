import requests
import unittest
import random
import string
import time
import json
import os

class GamingWebsiteAPITest(unittest.TestCase):
    """Test suite for the Gaming Website API"""
    
    def setUp(self):
        """Set up test environment before each test method"""
        # Get the backend URL from the frontend .env file
        self.base_url = "https://40eecd8e-d3a1-432f-bd75-6ac76c3d82ed.preview.emergentagent.com/api"
        self.token = None
        self.user_data = None
        
        # Generate random username for testing
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.test_username = f"testuser_{random_suffix}"
        self.test_email = f"test_{random_suffix}@example.com"
        self.test_password = "TestPassword123!"
        
        print(f"\n🔍 Testing with username: {self.test_username}")
    
    def get_headers(self):
        """Get headers with authentication token if available"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def test_01_register_user(self):
        """Test user registration"""
        print("\n🔍 Testing user registration...")
        
        payload = {
            "username": self.test_username,
            "email": self.test_email,
            "password": self.test_password
        }
        
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=payload
        )
        
        self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
        data = response.json()
        
        # Verify response structure
        self.assertIn('access_token', data, "Token not found in response")
        self.assertIn('user', data, "User data not found in response")
        self.assertEqual(data['user']['username'], self.test_username, "Username mismatch")
        self.assertEqual(data['user']['email'], self.test_email, "Email mismatch")
        self.assertEqual(data['user']['coins'], 1000, "New user should start with 1000 coins")
        self.assertEqual(len(data['user']['inventory']), 0, "New user should have empty inventory")
        
        # Save token and user data for subsequent tests
        self.token = data['access_token']
        self.user_data = data['user']
        
        print("✅ User registration successful")
    
    def test_02_login_user(self):
        """Test user login"""
        print("\n🔍 Testing user login...")
        
        payload = {
            "username": self.test_username,
            "password": self.test_password
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=payload
        )
        
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        data = response.json()
        
        # Verify response structure
        self.assertIn('access_token', data, "Token not found in response")
        self.assertIn('user', data, "User data not found in response")
        self.assertEqual(data['user']['username'], self.test_username, "Username mismatch")
        
        # Update token
        self.token = data['access_token']
        
        print("✅ User login successful")
    
    def test_03_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        print("\n🔍 Testing login with invalid credentials...")
        
        payload = {
            "username": self.test_username,
            "password": "WrongPassword123"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=payload
        )
        
        self.assertEqual(response.status_code, 401, "Should return 401 for invalid credentials")
        
        print("✅ Invalid login correctly rejected")
    
    def test_04_get_current_user(self):
        """Test getting current user info"""
        print("\n🔍 Testing get current user info...")
        
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        
        self.assertEqual(response.status_code, 200, f"Get user info failed: {response.text}")
        data = response.json()
        
        # Verify user data
        self.assertEqual(data['username'], self.test_username, "Username mismatch")
        self.assertEqual(data['email'], self.test_email, "Email mismatch")
        
        print("✅ Get current user successful")
    
    def test_05_get_items(self):
        """Test getting webshop items"""
        print("\n🔍 Testing get webshop items...")
        
        response = requests.get(f"{self.base_url}/items")
        
        self.assertEqual(response.status_code, 200, f"Get items failed: {response.text}")
        items = response.json()
        
        # Verify items data
        self.assertGreaterEqual(len(items), 8, "Should have at least 8 sample items")
        
        # Check item structure
        item_types = set()
        for item in items:
            self.assertIn('id', item, "Item should have id")
            self.assertIn('item_type', item, "Item should have type")
            self.assertIn('item_name', item, "Item should have name")
            self.assertIn('coin_price', item, "Item should have price")
            self.assertIn('description', item, "Item should have description")
            item_types.add(item['item_type'])
        
        # Verify item categories
        expected_types = {'Weapon', 'Tool', 'Cosmetic', 'Power-up'}
        self.assertTrue(expected_types.issubset(item_types), 
                       f"Missing item types. Expected {expected_types}, got {item_types}")
        
        # Save first item for purchase test
        self.test_item = items[0]
        
        print(f"✅ Retrieved {len(items)} items from webshop")
    
    def test_06_purchase_item(self):
        """Test purchasing an item"""
        print("\n🔍 Testing item purchase...")
        
        # Get current user info to check coins
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user_before = response.json()
        initial_coins = user_before['coins']
        initial_inventory = user_before['inventory']
        
        # Purchase item
        payload = {"item_id": self.test_item['id']}
        response = requests.post(
            f"{self.base_url}/purchase",
            json=payload,
            headers=self.get_headers()
        )
        
        self.assertEqual(response.status_code, 200, f"Purchase failed: {response.text}")
        purchase_data = response.json()
        
        # Verify purchase response
        self.assertIn('message', purchase_data, "Purchase response should have message")
        self.assertIn('coins_remaining', purchase_data, "Purchase response should have coins_remaining")
        
        # Check if coins were deducted correctly
        expected_coins = initial_coins - self.test_item['coin_price']
        self.assertEqual(purchase_data['coins_remaining'], expected_coins, 
                        f"Coins not deducted correctly. Expected {expected_coins}, got {purchase_data['coins_remaining']}")
        
        # Get updated user info to verify inventory
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user_after = response.json()
        
        # Verify inventory update
        self.assertEqual(len(user_after['inventory']), len(initial_inventory) + 1, 
                        "Inventory size should increase by 1")
        self.assertIn(self.test_item['item_name'], user_after['inventory'], 
                     f"Item {self.test_item['item_name']} not found in inventory")
        
        print(f"✅ Successfully purchased {self.test_item['item_name']} for {self.test_item['coin_price']} coins")
    
    def test_07_insufficient_coins_purchase(self):
        """Test purchase with insufficient coins"""
        print("\n🔍 Testing purchase with insufficient coins...")
        
        # Get current user info
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user = response.json()
        
        # Find expensive item that costs more than user's coins
        response = requests.get(f"{self.base_url}/items")
        self.assertEqual(response.status_code, 200)
        items = response.json()
        
        expensive_items = [item for item in items if item['coin_price'] > user['coins']]
        
        if not expensive_items:
            print("⚠️ No items more expensive than user's coins, skipping test")
            return
        
        expensive_item = expensive_items[0]
        
        # Try to purchase expensive item
        payload = {"item_id": expensive_item['id']}
        response = requests.post(
            f"{self.base_url}/purchase",
            json=payload,
            headers=self.get_headers()
        )
        
        self.assertEqual(response.status_code, 400, "Should return 400 for insufficient coins")
        error_data = response.json()
        self.assertIn('detail', error_data, "Error response should have detail")
        self.assertIn('insufficient', error_data['detail'].lower(), 
                     f"Error message should mention insufficient coins, got: {error_data['detail']}")
        
        print("✅ Purchase with insufficient coins correctly rejected")
    
    def test_08_lucky_spin_game(self):
        """Test Lucky Spin game"""
        print("\n🔍 Testing Lucky Spin game...")
        
        # Get current user info
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user_before = response.json()
        initial_coins = user_before['coins']
        
        # Play Lucky Spin
        response = requests.post(
            f"{self.base_url}/games/lucky-spin",
            headers=self.get_headers()
        )
        
        self.assertEqual(response.status_code, 200, f"Lucky Spin failed: {response.text}")
        game_data = response.json()
        
        # Verify game response
        self.assertIn('success', game_data, "Game response should have success field")
        self.assertTrue(game_data['success'], "Game should be successful")
        self.assertIn('coins_won', game_data, "Game response should have coins_won")
        self.assertIn('message', game_data, "Game response should have message")
        
        # Get updated user info
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user_after = response.json()
        
        # Verify coins update (cost: 50, win: variable)
        expected_coins = initial_coins - 50 + game_data['coins_won']
        self.assertEqual(user_after['coins'], expected_coins, 
                        f"Coins not updated correctly. Expected {expected_coins}, got {user_after['coins']}")
        
        print(f"✅ Successfully played Lucky Spin, won {game_data['coins_won']} coins")
    
    def test_09_egg_smash_game(self):
        """Test Egg Smashing game"""
        print("\n🔍 Testing Egg Smashing game...")
        
        # Get current user info
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user_before = response.json()
        initial_coins = user_before['coins']
        
        # Play Egg Smash
        response = requests.post(
            f"{self.base_url}/games/egg-smash",
            headers=self.get_headers()
        )
        
        self.assertEqual(response.status_code, 200, f"Egg Smash failed: {response.text}")
        game_data = response.json()
        
        # Verify game response
        self.assertIn('success', game_data, "Game response should have success field")
        self.assertTrue(game_data['success'], "Game should be successful")
        self.assertIn('coins_won', game_data, "Game response should have coins_won")
        self.assertIn('message', game_data, "Game response should have message")
        
        # Get updated user info
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user_after = response.json()
        
        # Verify coins update (cost: 25, win: variable)
        expected_coins = initial_coins - 25 + game_data['coins_won']
        self.assertEqual(user_after['coins'], expected_coins, 
                        f"Coins not updated correctly. Expected {expected_coins}, got {user_after['coins']}")
        
        print(f"✅ Successfully played Egg Smash, won {game_data['coins_won']} coins")
    
    def test_10_insufficient_coins_games(self):
        """Test games with insufficient coins"""
        print("\n🔍 Testing games with insufficient coins...")
        
        # Get current user info
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        user = response.json()
        
        # If user has more than 50 coins, spend them until less than 50
        while user['coins'] >= 50:
            # Play Lucky Spin to reduce coins
            response = requests.post(
                f"{self.base_url}/games/lucky-spin",
                headers=self.get_headers()
            )
            self.assertEqual(response.status_code, 200)
            
            # Get updated user info
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=self.get_headers()
            )
            self.assertEqual(response.status_code, 200)
            user = response.json()
        
        print(f"User now has {user['coins']} coins")
        
        # Try Lucky Spin with insufficient coins
        if user['coins'] < 50:
            response = requests.post(
                f"{self.base_url}/games/lucky-spin",
                headers=self.get_headers()
            )
            
            self.assertEqual(response.status_code, 400, "Should return 400 for insufficient coins")
            error_data = response.json()
            self.assertIn('detail', error_data, "Error response should have detail")
            self.assertIn('insufficient', error_data['detail'].lower(), 
                         f"Error message should mention insufficient coins, got: {error_data['detail']}")
            
            print("✅ Lucky Spin with insufficient coins correctly rejected")
        
        # Try Egg Smash with insufficient coins
        if user['coins'] < 25:
            response = requests.post(
                f"{self.base_url}/games/egg-smash",
                headers=self.get_headers()
            )
            
            self.assertEqual(response.status_code, 400, "Should return 400 for insufficient coins")
            error_data = response.json()
            self.assertIn('detail', error_data, "Error response should have detail")
            self.assertIn('insufficient', error_data['detail'].lower(), 
                         f"Error message should mention insufficient coins, got: {error_data['detail']}")
            
            print("✅ Egg Smash with insufficient coins correctly rejected")

def run_tests():
    """Run all tests in order"""
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()
    
    # Add tests in specific order
    test_cases = [
        GamingWebsiteAPITest('test_01_register_user'),
        GamingWebsiteAPITest('test_02_login_user'),
        GamingWebsiteAPITest('test_03_login_invalid_credentials'),
        GamingWebsiteAPITest('test_04_get_current_user'),
        GamingWebsiteAPITest('test_05_get_items'),
        GamingWebsiteAPITest('test_06_purchase_item'),
        GamingWebsiteAPITest('test_07_insufficient_coins_purchase'),
        GamingWebsiteAPITest('test_08_lucky_spin_game'),
        GamingWebsiteAPITest('test_09_egg_smash_game'),
        GamingWebsiteAPITest('test_10_insufficient_coins_games'),
    ]
    
    for test_case in test_cases:
        test_suite.addTest(test_case)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"✅ Tests passed: {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun}")
    print(f"❌ Tests failed: {len(result.failures) + len(result.errors)}")
    
    return len(result.failures) + len(result.errors) == 0

if __name__ == "__main__":
    run_tests()