from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    coins: int = 1000
    inventory: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    coins: int
    inventory: List[str]

class Item(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_type: str
    item_name: str
    coin_price: int
    description: str
    image_url: str = ""

class PurchaseRequest(BaseModel):
    item_id: str

class GameResult(BaseModel):
    success: bool
    coins_won: int = 0
    item_won: Optional[str] = None
    message: str

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

# Initialize sample items
async def init_sample_items():
    existing_items = await db.items.find_one()
    if not existing_items:
        sample_items = [
            {"item_type": "Weapon", "item_name": "Steel Sword", "coin_price": 150, "description": "A sharp steel sword for battle", "image_url": "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=300&h=300&fit=crop"},
            {"item_type": "Weapon", "item_name": "Magic Staff", "coin_price": 300, "description": "A powerful magic staff", "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=300&fit=crop"},
            {"item_type": "Tool", "item_name": "Pickaxe", "coin_price": 75, "description": "Perfect for mining", "image_url": "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=300&h=300&fit=crop"},
            {"item_type": "Tool", "item_name": "Fishing Rod", "coin_price": 50, "description": "Catch the biggest fish", "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=300&h=300&fit=crop"},
            {"item_type": "Cosmetic", "item_name": "Golden Crown", "coin_price": 500, "description": "Show your royal status", "image_url": "https://images.unsplash.com/photo-1611652022419-a9419f74343d?w=300&h=300&fit=crop"},
            {"item_type": "Cosmetic", "item_name": "Cape of Shadows", "coin_price": 200, "description": "A mysterious dark cape", "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=300&fit=crop"},
            {"item_type": "Power-up", "item_name": "Speed Potion", "coin_price": 25, "description": "Increases your speed temporarily", "image_url": "https://images.unsplash.com/photo-1559181567-c3190ca9959b?w=300&h=300&fit=crop"},
            {"item_type": "Power-up", "item_name": "Strength Elixir", "coin_price": 35, "description": "Doubles your strength for 10 minutes", "image_url": "https://images.unsplash.com/photo-1582719471384-894fbb16e074?w=300&h=300&fit=crop"},
        ]
        
        for item_data in sample_items:
            item = Item(**item_data)
            await db.items.insert_one(item.dict())

# Authentication endpoints
@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer", "user": UserResponse(**user.dict())}

@api_router.post("/auth/login", response_model=dict)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["username"]})
    
    return {"access_token": access_token, "token_type": "bearer", "user": UserResponse(**user)}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# Webshop endpoints
@api_router.get("/items", response_model=List[Item])
async def get_items():
    items = await db.items.find().to_list(1000)
    return [Item(**item) for item in items]

@api_router.post("/purchase", response_model=dict)
async def purchase_item(purchase: PurchaseRequest, current_user: User = Depends(get_current_user)):
    # Get item
    item = await db.items.find_one({"id": purchase.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_obj = Item(**item)
    
    # Check if user has enough coins
    if current_user.coins < item_obj.coin_price:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    # Update user coins and inventory
    new_coins = current_user.coins - item_obj.coin_price
    new_inventory = current_user.inventory + [item_obj.item_name]
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"coins": new_coins, "inventory": new_inventory}}
    )
    
    return {"message": f"Successfully purchased {item_obj.item_name}!", "coins_remaining": new_coins}

# Game endpoints
@api_router.post("/games/lucky-spin", response_model=GameResult)
async def play_lucky_spin(current_user: User = Depends(get_current_user)):
    SPIN_COST = 50
    
    if current_user.coins < SPIN_COST:
        raise HTTPException(status_code=400, detail="Insufficient coins to play")
    
    # Random rewards
    outcomes = [
        {"coins": 10, "probability": 0.3},
        {"coins": 25, "probability": 0.25},
        {"coins": 50, "probability": 0.2},
        {"coins": 100, "probability": 0.15},
        {"coins": 200, "probability": 0.08},
        {"coins": 500, "probability": 0.02},
    ]
    
    rand = random.random()
    cumulative = 0
    coins_won = 10  # fallback
    
    for outcome in outcomes:
        cumulative += outcome["probability"]
        if rand <= cumulative:
            coins_won = outcome["coins"]
            break
    
    # Update user coins
    new_coins = current_user.coins - SPIN_COST + coins_won
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"coins": new_coins}}
    )
    
    net_gain = coins_won - SPIN_COST
    message = f"You won {coins_won} coins! Net: {'+' if net_gain >= 0 else ''}{net_gain} coins"
    
    return GameResult(
        success=True,
        coins_won=coins_won,
        message=message
    )

@api_router.post("/games/egg-smash", response_model=GameResult)
async def play_egg_smash(current_user: User = Depends(get_current_user)):
    SMASH_COST = 25
    
    if current_user.coins < SMASH_COST:
        raise HTTPException(status_code=400, detail="Insufficient coins to play")
    
    # Random rewards
    outcomes = [
        {"coins": 5, "probability": 0.4},
        {"coins": 15, "probability": 0.3},
        {"coins": 30, "probability": 0.15},
        {"coins": 50, "probability": 0.1},
        {"coins": 100, "probability": 0.04},
        {"coins": 200, "probability": 0.01},
    ]
    
    rand = random.random()
    cumulative = 0
    coins_won = 5  # fallback
    
    for outcome in outcomes:
        cumulative += outcome["probability"]
        if rand <= cumulative:
            coins_won = outcome["coins"]
            break
    
    # Update user coins
    new_coins = current_user.coins - SMASH_COST + coins_won
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"coins": new_coins}}
    )
    
    net_gain = coins_won - SMASH_COST
    message = f"You smashed an egg and won {coins_won} coins! Net: {'+' if net_gain >= 0 else ''}{net_gain} coins"
    
    return GameResult(
        success=True,
        coins_won=coins_won,
        message=message
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_sample_items()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()