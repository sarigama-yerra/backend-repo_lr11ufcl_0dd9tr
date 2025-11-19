import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Expense

app = FastAPI(title="Expense Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExpenseCreate(Expense):
    pass

class ExpenseOut(BaseModel):
    id: str
    amount: float
    category: str
    note: Optional[str]
    date: str
    month: str


def _doc_to_expense_out(doc) -> ExpenseOut:
    return ExpenseOut(
        id=str(doc.get("_id")),
        amount=float(doc.get("amount", 0)),
        category=doc.get("category", ""),
        note=doc.get("note"),
        date=(doc.get("date").strftime("%Y-%m-%d") if isinstance(doc.get("date"), datetime) else str(doc.get("date"))),
        month=doc.get("month", ""),
    )


@app.get("/")
def read_root():
    return {"message": "Expense Tracker Backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# API Endpoints
@app.post("/api/expenses", response_model=dict)
async def add_expense(expense: ExpenseCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # derive month as YYYY-MM for quick monthly filters
    expense_dict = expense.model_dump()
    # normalize date to datetime
    if isinstance(expense_dict.get("date"), str):
        try:
            d = datetime.strptime(expense_dict["date"], "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    else:
        # pydantic sends date object
        d = datetime.combine(expense_dict["date"], datetime.min.time())
    expense_dict["month"] = d.strftime("%Y-%m")
    expense_dict["date"] = d

    inserted_id = create_document("expense", expense_dict)
    return {"id": inserted_id}


@app.get("/api/expenses", response_model=List[ExpenseOut])
async def list_expenses(month: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_query = {}
    if month:
        filter_query["month"] = month  # expect YYYY-MM

    docs = get_documents("expense", filter_query)
    # sort by date desc
    docs.sort(key=lambda x: x.get("date", datetime.min), reverse=True)
    return [_doc_to_expense_out(doc) for doc in docs]


@app.get("/api/summary", response_model=dict)
async def summary(month: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_query = {"month": month} if month else {}
    docs = get_documents("expense", filter_query)
    total = sum(float(d.get("amount", 0)) for d in docs)

    # simple category breakdown
    breakdown = {}
    for d in docs:
        cat = d.get("category", "Other")
        breakdown[cat] = breakdown.get(cat, 0) + float(d.get("amount", 0))

    # last 6 months totals for trend
    # We can compute based on existing docs' month values
    trends = {}
    for d in docs:
        m = d.get("month")
        if m:
            trends[m] = trends.get(m, 0) + float(d.get("amount", 0))

    return {
        "total": total,
        "count": len(docs),
        "breakdown": breakdown,
        "trends": trends,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
