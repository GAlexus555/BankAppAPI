import logging
from starlette import status
from database import engine
import models
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
import uvicorn
from routers import accounts, cards, transactions, interests, bank, auditlogs, stats
from starlette.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("api.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BankApp API",
    description="""
## BankApp – REST API

Verwaltungs-API für die BankApp. Alle geschützten Endpunkte benötigen einen **Bearer-Token**,
der über `POST /accounts/login` bezogen wird.

### Rollen
| Wert | Bezeichnung | Berechtigungen |
|------|-------------|----------------|
| `0`  | `client`    | Eigene Daten, eigene Karten, eigene Transaktionen, Sparzinsen |
| `1`  | `manager`   | Alle Daten, Benutzerverwaltung, Statistiken, Audit-Log |

### Allgemeine Wertebereiche
- **Geldbeträge** werden immer in **Cent** (Integer) übergeben. `1000` = 10,00 €
- **Datumsfelder** im Format `YYYY-MM-DD`
- **IBAN**: 15–34 Zeichen, beginnt mit 2 Buchstaben (Ländercode)
""",
    version="1.0.0",
    contact={"name": "BankApp Team"},
    license_info={"name": "MIT"},
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


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


app.include_router(accounts.router)
app.include_router(cards.router)
app.include_router(transactions.router)
app.include_router(interests.router)
app.include_router(bank.router)
app.include_router(auditlogs.router)
app.include_router(stats.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
