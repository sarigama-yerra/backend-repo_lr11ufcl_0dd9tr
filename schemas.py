"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional
import datetime as _dt

# Example schemas (you can keep these for reference or ignore):

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Expense tracking schemas

class Expense(BaseModel):
    """
    Expenses collection schema
    Collection name: "expense"
    """
    amount: float = Field(..., gt=0, description="Amount spent")
    category: str = Field(..., description="Category of expense, e.g., Food, Rent")
    note: Optional[str] = Field(None, description="Optional note or description")
    date: _dt.date = Field(..., description="Date of expense")
    month: Optional[str] = Field(None, description="Derived field: YYYY-MM for quick monthly queries")
