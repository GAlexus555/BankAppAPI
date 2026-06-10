from starlette import status
from database import engine
import models
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
import uvicorn
from routers import accounts, cards, transactions, interests, bank, auditlogs
from starlette.responses import JSONResponse


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="myApp", description="myApp", version="1.0.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = error.get('loc')[-1]
        err_msg = error.get('msg')

        errors.append(({"field": field, "msg": err_msg}))

    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
        "status": "validation_error",
        "errors": errors
    })


# Include routers
app.include_router(accounts.router)
app.include_router(cards.router)
app.include_router(transactions.router)
app.include_router(interests.router)
app.include_router(bank.router)
app.include_router(auditlogs.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)