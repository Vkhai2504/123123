import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Component
const AuthForm = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { username: formData.username, password: formData.password }
        : formData;

      console.log('Attempting authentication:', endpoint, payload);
      const response = await axios.post(`${API}${endpoint}`, payload, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 10000
      });
      
      console.log('Authentication response:', response.data);
      
      if (response.data.access_token && response.data.user) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        onLogin(response.data.user);
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (err) {
      console.error('Authentication error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Authentication failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 w-full max-w-md border border-white/20">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🎮 GameHub</h1>
          <p className="text-white/70">Your Gaming Adventure Awaits</p>
        </div>

        <div className="flex mb-6 bg-white/5 rounded-lg p-1">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 px-4 rounded-md transition-all ${
              isLogin ? 'bg-blue-600 text-white' : 'text-white/70 hover:text-white'
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 px-4 rounded-md transition-all ${
              !isLogin ? 'bg-blue-600 text-white' : 'text-white/70 hover:text-white'
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Username"
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          
          {!isLogin && (
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          )}
          
          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />

          {error && (
            <div className="text-red-400 text-sm bg-red-400/10 p-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('webshop');
  const [items, setItems] = useState([]);
  const [userCoins, setUserCoins] = useState(user.coins);
  const [inventory, setInventory] = useState(user.inventory);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadItems();
  }, []);

  const getAuthHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem('token')}`
  });

  const loadItems = async () => {
    try {
      const response = await axios.get(`${API}/items`);
      setItems(response.data);
    } catch (err) {
      console.error('Failed to load items:', err);
    }
  };

  const purchaseItem = async (itemId) => {
    setLoading(true);
    try {
      console.log('Attempting to purchase item:', itemId);
      const response = await axios.post(
        `${API}/purchase`, 
        { item_id: itemId },
        { 
          headers: getAuthHeaders(),
          timeout: 10000
        }
      );
      
      console.log('Purchase response:', response.data);
      setUserCoins(response.data.coins_remaining);
      const item = items.find(i => i.id === itemId);
      if (item) {
        setInventory([...inventory, item.item_name]);
      }
      setMessage(response.data.message);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error('Purchase error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Purchase failed';
      setMessage(errorMessage);
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const playLuckySpin = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/games/lucky-spin`,
        {},
        { headers: getAuthHeaders() }
      );
      
      setUserCoins(userCoins - 50 + response.data.coins_won);
      setMessage(response.data.message);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Game failed');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const playEggSmash = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/games/egg-smash`,
        {},
        { headers: getAuthHeaders() }
      );
      
      setUserCoins(userCoins - 25 + response.data.coins_won);
      setMessage(response.data.message);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Game failed');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const renderWebshop = () => (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-white mb-6">🛒 Webshop</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((item) => (
          <div key={item.id} className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="aspect-square bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg mb-4 flex items-center justify-center text-4xl">
              {item.item_type === 'Weapon' && '⚔️'}
              {item.item_type === 'Tool' && '🔨'}
              {item.item_type === 'Cosmetic' && '👑'}
              {item.item_type === 'Power-up' && '🧪'}
            </div>
            <h3 className="text-xl font-bold text-white mb-2">{item.item_name}</h3>
            <p className="text-white/70 text-sm mb-3">{item.description}</p>
            <div className="flex items-center justify-between">
              <span className="text-yellow-400 font-bold">💰 {item.coin_price} coins</span>
              <button
                onClick={() => purchaseItem(item.id)}
                disabled={loading || userCoins < item.coin_price}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Buy
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderLuckySpin = () => (
    <div className="text-center space-y-8">
      <h2 className="text-3xl font-bold text-white mb-6">🎰 Lucky Spin</h2>
      <div className="bg-white/10 backdrop-blur-sm rounded-3xl p-12 max-w-md mx-auto border border-white/20">
        <div className="text-8xl mb-6">🎰</div>
        <p className="text-white/70 mb-6">Spin the wheel of fortune!</p>
        <p className="text-yellow-400 mb-6">Cost: 50 coins | Win: 10-500 coins</p>
        <button
          onClick={playLuckySpin}
          disabled={loading || userCoins < 50}
          className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full font-bold text-xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105"
        >
          {loading ? 'Spinning...' : 'SPIN! 🎰'}
        </button>
      </div>
    </div>
  );

  const renderEggSmash = () => (
    <div className="text-center space-y-8">
      <h2 className="text-3xl font-bold text-white mb-6">🥚 Egg Smashing</h2>
      <div className="bg-white/10 backdrop-blur-sm rounded-3xl p-12 max-w-md mx-auto border border-white/20">
        <div className="text-8xl mb-6">🥚</div>
        <p className="text-white/70 mb-6">Smash eggs to find treasures!</p>
        <p className="text-yellow-400 mb-6">Cost: 25 coins | Win: 5-200 coins</p>
        <button
          onClick={playEggSmash}
          disabled={loading || userCoins < 25}
          className="px-8 py-4 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-full font-bold text-xl hover:from-orange-700 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105"
        >
          {loading ? 'Smashing...' : 'SMASH! 🔨'}
        </button>
      </div>
    </div>
  );

  const renderInventory = () => (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-white mb-6">🎒 My Inventory</h2>
      {inventory.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📦</div>
          <p className="text-white/70">Your inventory is empty. Visit the webshop to buy items!</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {inventory.map((itemName, index) => (
            <div key={index} className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20 text-center">
              <div className="text-2xl mb-2">🎁</div>
              <p className="text-white text-sm">{itemName}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-sm border-b border-white/10 p-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white">🎮 GameHub</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-yellow-600/20 px-4 py-2 rounded-full">
              <span className="text-2xl">💰</span>
              <span className="text-white font-bold">{userCoins} coins</span>
            </div>
            <span className="text-white">Welcome, {user.username}!</span>
            <button
              onClick={onLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Left Sidebar */}
        <aside className="w-64 bg-black/30 backdrop-blur-sm min-h-screen p-6 border-r border-white/10">
          <nav className="space-y-2">
            {[
              { id: 'webshop', label: '🛒 Webshop', icon: '🛒' },
              { id: 'lucky-spin', label: '🎰 Lucky Spin', icon: '🎰' },
              { id: 'egg-smash', label: '🥚 Egg Smashing', icon: '🥚' },
              { id: 'inventory', label: '🎒 Inventory', icon: '🎒' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'text-white/70 hover:text-white hover:bg-white/10'
                }`}
              >
                <span className="mr-3">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {message && (
            <div className="mb-6 p-4 bg-green-600/20 border border-green-600/30 rounded-lg text-green-400">
              {message}
            </div>
          )}

          {activeTab === 'webshop' && renderWebshop()}
          {activeTab === 'lucky-spin' && renderLuckySpin()}
          {activeTab === 'egg-smash' && renderEggSmash()}
          {activeTab === 'inventory' && renderInventory()}
        </main>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        console.log('Loaded user from localStorage:', parsedUser);
        setUser(parsedUser);
      } catch (err) {
        console.error('Error parsing user data:', err);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    );
  }

  return user ? (
    <Dashboard user={user} onLogout={handleLogout} />
  ) : (
    <AuthForm onLogin={handleLogin} />
  );
}

export default App;