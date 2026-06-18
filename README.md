# BankAppAPI

**Klasse:** 3HIF · **Schuljahr:** 2025/26  
**Team:** Alexei & Chiara

Python-FastAPI-Backend für eine fiktive Bank. Verwaltet Kunden, Karten, Überweisungen und Sparzinskonten. Vollständige interaktive Dokumentation unter `http://127.0.0.1:8000/docs` (Swagger UI).

Frontend (WPF/C#): [BankApp](https://github.com/GAlexus555/BankApp)

---

## Rollen

| Rolle | Wert | Rechte |
|---|---|---|
| **Client** | `0` | Eigene Karten/Transaktionen/Sparzinsen verwalten, Überweisungen tätigen |
| **Manager** | `1` | Vollständiger CRUD auf allen Ressourcen, Statistiken & Audit-Log |

---

## Voraussetzungen & Installation

```bash
pip install fastapi uvicorn sqlalchemy "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]" fastapi-restful python-multipart
```

| Paket | Version | Zweck |
|---|---|---|
| `fastapi` | 0.115.x | Web-Framework |
| `uvicorn` | 0.30.x | ASGI-Server |
| `sqlalchemy` | 2.0.x | ORM / Datenbankanbindung |
| `pydantic[email]` | 2.x | Request- & Response-Validierung |
| `python-jose[cryptography]` | 3.3.x | JWT |
| `passlib[bcrypt]` | 1.7.x | Passwort-Hashing |
| `fastapi-restful` | 0.6.x | Class-Based Views (`@cbv`) |
| `python-multipart` | 0.0.x | OAuth2-Login (Form-Daten) |

---

## Starten

```bash
# 1. Datenbank initialisieren (einmalig)
python init_db.py

# 2. API starten
uvicorn src.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`

---

## Datenbankschema

**6 Tabellen:**

| Tabelle | Beschreibung |
|---|---|
| `accounts` | Benutzer (Clients + Manager) mit Rolle, Email, Passwort-Hash, Adresse, Geburtsdatum |
| `cards` | Bankkarten (IBAN, CardNr, Ablaufdatum, CVC, Status, Guthaben in Cent) |
| `transactions` | Überweisungen zwischen zwei Karten (Betrag in Cent, Datum, Beschreibung, Status) |
| `interests` | Sparzinskonten — einer Karte zugeordnet (Betrag, Zinssatz, ausgezahlt?) |
| `bank` | Bankdaten (Name, aktueller Zinssatz) |
| `audit_logs` | Protokoll aller schreibenden Aktionen |

**Relationales Modell:**

```
accounts   (<u>id</u>, email, password, firstname, lastname, phonenumber, address, birthdate, role, created_at)
cards      (<u>id</u>, owner_id→accounts, iban, card_nr, expire_date, cvc, status, cents, created_at)
transactions (<u>id</u>, from_id→cards, to_id→cards, amount_cents, description, status, created_at)
interests  (<u>id</u>, card_id→cards, amount, interest_rate, withdrawn, created_at)
bank       (<u>id</u>, bankname, interest_rate)
audit_logs (<u>id</u>, account_id→accounts, action, tablename, details, timestamp)
```

**Kardinalitäten:** Account → Cards (1:n) · Card → Interests (1:n) · Cards ↔ Cards via Transactions (m:n)

---

## API Endpunkte

Authentifizierung: `Authorization: Bearer <token>` (JWT, 30 min gültig)

### Accounts

| Methode | Pfad | Beschreibung | Rolle | Codes |
|---|---|---|---|---|
| POST | `/accounts/register` | Neuen Benutzer registrieren | – | 201, 409, 422 |
| POST | `/accounts/login` | Login → gibt JWT zurück (form-data) | – | 200, 401 |
| GET | `/accounts/me` | Eigenen Account abrufen | alle | 200, 401 |
| GET | `/accounts` | Alle Accounts auflisten | manager | 200 |
| GET | `/accounts/{id}` | Einzelnen Account abrufen | alle | 200, 404 |
| PUT | `/accounts/me` | Eigenes Profil aktualisieren | alle | 200, 422 |
| PUT | `/accounts/{id}` | Account vollständig aktualisieren | manager | 200, 404, 422 |
| DELETE | `/accounts/{id}` | Account löschen | manager | 200, 400, 404 |

### Cards

| Methode | Pfad | Beschreibung | Rolle | Codes |
|---|---|---|---|---|
| GET | `/cards` | Eigene Karten | alle | 200 |
| GET | `/cards/all` | Alle Karten | manager | 200 |
| GET | `/cards/{account_id}` | Karten eines Accounts | manager | 200 |
| POST | `/cards` | Neue Karte erstellen | manager | 201, 404 |
| PUT | `/cards/{card_id}` | Karte bearbeiten | manager | 200, 404 |
| DELETE | `/cards/{card_id}` | Karte löschen | manager | 200, 404 |

### Transactions

| Methode | Pfad | Beschreibung | Rolle | Codes |
|---|---|---|---|---|
| GET | `/transactions` | Eigene Transaktionen | alle | 200 |
| GET | `/transactions/all` | Alle Transaktionen | manager | 200 |
| GET | `/transactions/account/{id}` | Transaktionen eines Accounts | manager | 200 |
| POST | `/transactions` | Überweisung erstellen | alle | 200, 400, 403, 404 |

### Interests

| Methode | Pfad | Beschreibung | Rolle | Codes |
|---|---|---|---|---|
| GET | `/interests` | Eigene Sparzinskonten | alle | 200 |
| GET | `/interests/all` | Alle Sparzinskonten | manager | 200 |
| POST | `/interests` | Sparkonto eröffnen | alle | 200, 400, 403, 404 |
| POST | `/interests/{id}/withdraw` | Zinsen auszahlen (Zinseszins) | alle | 200, 400, 403, 404 |

### Banks / Stats / Audit-Logs

| Methode | Pfad | Beschreibung | Rolle |
|---|---|---|---|
| GET | `/banks` | Bankdaten abrufen | – |
| POST | `/banks` | Bank anlegen | manager |
| PUT | `/banks/{bank_id}` | Bank aktualisieren | manager |
| GET | `/stats/transactions-per-account` | COUNT + SUM pro Account (GROUP BY) | manager |
| GET | `/audit-logs` | Alle Audit-Einträge | manager |
| GET | `/audit-logs/{account_id}` | Logs eines Accounts | manager |

---

## Wertebereiche

| Feld | Wertebereich |
|---|---|
| `firstname`, `lastname` | 3–30 Zeichen |
| `email` | Gültige E-Mail, eindeutig |
| `password` | ≥ 8 Zeichen, mind. 1 Großbuchstabe, mind. 1 Ziffer |
| `phonenumber` | 7–15 Zeichen |
| `role` | `0` = client, `1` = manager |
| `cents` / `amount` | ≥ 0 (Guthaben), > 0 (Überweisungen/Spareinlagen) |
| `iban` | 15–34 Zeichen |
| `card_nr` | 13–16 Ziffern |
| `cvc` | 100–9999 |
| `interest_rate` | 0 < Wert ≤ 1 (z. B. `0.035` = 3,5 % p.a.) |

---

## Ordnerstruktur

```
BankAppAPI/
├── init_db.py          # Datenbank initialisieren
├── src/
│   ├── main.py         # App-Start, Middleware, Router
│   ├── database.py     # SQLite-Verbindung, get_db()
│   ├── models.py       # SQLAlchemy ORM-Modelle
│   ├── schemas.py      # Pydantic Schemas mit Field-Constraints
│   ├── auth.py         # JWT, Passwort-Hashing, Rollen-Dependency
│   ├── audit.py        # AuditLogger
│   └── routers/
│       ├── accounts.py
│       ├── cards.py
│       ├── transactions.py
│       ├── interests.py
│       ├── bank.py
│       ├── auditlogs.py
│       └── stats.py
└── doc/
    └── DBI Projekt – BankApp.md
```

---

## Bekannte Probleme & Lösungen

| Problem | Lösung |
|---|---|
| Route-Konflikt `/cards/all` vs `/cards/{account_id}` | `/cards/all` vor `/cards/{account_id}` definieren |
| `func.now()` erzeugt leere Zeitstempel in SQLite | `server_default="CURRENT_TIMESTAMP"` verwenden |
| AuditLogger erzeugte doppelte Einträge | `db.flush()` vor Logger, ein einziges `db.commit()` am Ende |
| 307-Redirect löscht Authorization-Header im Frontend | API immer ohne trailing Slash aufrufen |
| JWT lief nach 5 Minuten ab | Token-Ablaufzeit in `auth.py` auf 30 Minuten erhöht |

---

## Projekttagebuch

| Datum | Was wurde gemacht | Wer |
|---|---|---|
| 27.05.2026 | ERM und RM erstellt, Domäne festgelegt | Alexei & Chiara |
| 28.05.2026 | SQLAlchemy-Modelle, Pydantic-Schemas, Datenbankverbindung | Alexei |
| 03.06.2026 | JWT-Auth, Accounts-, Cards-, Transactions-, Interests-Router | Alexei |
| 04.06.2026 | **Erste Demo** — Swagger UI funktioniert | Alexei & Chiara |
| 05.06.2026 | AuditLogger, Bank-Router | Alexei |
| 10.06.2026 | PUT-Endpunkte, Stats-Aggregation, Logging, Route-Konflikt gefixt | Alexei |
| 11.06.2026 | GET /transactions/account/{id}, PUT /accounts/me | Alexei |
| 13.06.2026 | GET /audit-logs/{account_id} | Alexei |
| 16.06.2026 | Swagger-Dokumentation, Pydantic Field-Constraints | Alexei & Chiara |
| 17.06.2026 | **Endpräsentation + Abgabe** | Alexei & Chiara |
