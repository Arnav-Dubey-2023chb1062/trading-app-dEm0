from fastapi import FastAPI

app = FastAPI()

# Import routers
from app.routes import user_routes
from app.routes import portfolio_routes
from app.routes import trade_routes

app.include_router(user_routes.router)
app.include_router(portfolio_routes.router) # Handles /portfolios
# trade_routes router will handle paths like /portfolios/{portfolio_id}/trades
app.include_router(trade_routes.router, prefix="/portfolios/{portfolio_id}/trades")


@app.get("/")
async def root():
    return {"message": "Hello World"}
