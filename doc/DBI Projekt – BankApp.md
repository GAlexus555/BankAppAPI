**Klasse:** 3HIF · **Schuljahr:** 2025/26  
**Team:** Alexei & Chiara  

---

## 1. Projektbeschreibung

Die BankApp ist ein datenbankgestütztes Backend-System für eine fiktive Bank. Das System verwaltet Kunden (Clients), ihre Konten, Bankkarten, Überweisungen und Sparzinskonten.

Es gibt zwei Rollen:

- **Client (user):** Kann sich anmelden, seine eigenen Konten und Karten einsehen und Überweisungen an andere Karten tätigen.
- **Bank Manager:** Kann alles verwalten — Clients anlegen/bearbeiten/löschen, Karten ausgeben, Transaktionen einsehen und Sparzinskonten verwalten. Nur der Manager darf neue Clients registrieren.

Das Frontend wird als WPF-Anwendung (C#, MVVM) gebaut und kommuniziert mit dem Backend über HTTP-Requests. Das Backend wird mit Python + FastAPI + SQLite umgesetzt und ist über Swagger UI (`/docs`) testbar.

---

## 2. Domäne & Tabellen

Das System besteht aus **6 Tabellen**:

|Tabelle|Beschreibung|
|---|---|
|`accounts`|Alle Benutzer (Clients + Manager) mit Rolle, Email, Passwort-Hash, Adresse, Geburtsdatum|
|`cards`|Bankkarten eines Accounts (IBAN, CardNr, Ablaufdatum, CVC, Status, Guthaben in Cent)|
|`transactions`|Überweisungen zwischen zwei Karten (Betrag in Cent, Datum, Beschreibung, Status)|
|`interests`|Sparzinskonten — einer Karte zugeordnet (Betrag, Zinssatz, ausgezahlt?)|
|`bank`|Bankdaten (Name, aktueller Zinssatz)|
|`audit_logs`|Protokollierung aller relevanten Aktionen nach Account|

### Kardinalitäten

|Typ|Beziehung|Beispiel|
|---|---|---|
|**1:n**|Account → Cards|Ein Client hat mehrere Karten|
|**1:n**|Card → Interests|Eine Karte kann mehrere Sparzinskonten haben|
|**m:n**|Cards ↔ Cards via Transactions|Eine Karte sendet an viele, empfängt von vielen|

> Die m:n-Beziehung wird durch `transactions` realisiert: eine Karte sendet an viele Karten (`from_id`) und empfängt von vielen Karten (`to_id`). Diese wird als eigene Zwischentabelle mit zwei Fremdschlüsseln umgesetzt.

---

## 3. Relationales Modell

**accounts** (<u>id</u>, email, password, firstname, lastname, phonenumber, address, birthdate, role, created_at)

**cards** (<u>id</u>, *owner_id*, iban, card_nr, expire_date, cvc, status, cents, created_at)

**transactions** (<u>id</u>, *from_id*, *to_id*, amount_cents, description, status, created_at)

**interests** (<u>id</u>, *card_id*, amount, interest_rate, withdrawn, created_at)

**bank** (<u>id</u>, bankname, interest_rate)

**audit_logs** (<u>id</u>, *account_id*, action, tablename, details, timestamp)

---

## 4. Normalformen

### `accounts`

- **1NF:** Alle Attribute sind atomar (keine Listen, keine Wiederholungsgruppen).
- **2NF:** Kein zusammengesetzter Primärschlüssel → 2NF automatisch erfüllt.
- **3NF:** Alle Nicht-Schlüssel-Attribute hängen direkt vom Primärschlüssel `id` ab. Keine transitiven Abhängigkeiten.

### `cards`

- **1NF:** Alle Attribute atomar. Jede Karte hat genau eine IBAN, eine card_nr usw.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** `owner_id` ist FK, alle anderen Attribute beschreiben direkt die Karte selbst, nicht den Account.

### `transactions`

- **1NF:** Atomar. `from_id` und `to_id` sind zwei separate FK-Felder.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** Betrag, Datum und Status beschreiben die Transaktion, nicht die Karten. Keine transitiven Abhängigkeiten.

### `interests`

- **1NF:** Atomar. Zinssatz und Betrag sind einzelne Felder.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** `amount` und `interest_rate` hängen direkt von `id` ab, nicht von `card_id`.

### `bank`

- **1NF:** Atomar. Bankname und Zinssatz sind einzelne Felder.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** Alle Attribute beschreiben direkt die Bank. Keine transitiven Abhängigkeiten.

### `audit_logs`

- **1NF:** Atomar. Jeder Eintrag beschreibt genau eine Aktion zu einem Zeitpunkt.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** `action`, `tablename`, `details` beschreiben den Log-Eintrag direkt. `account_id` ist nur FK-Referenz.

---

## 5. REST-API Endpunkte

**Stack:** Python · FastAPI · uvicorn · SQLite · Pydantic  
**Authentifizierung:** JWT Bearer Token (OAuth2). Login über `/accounts/login` → gibt `access_token` zurück. Token wird im Header als `Authorization: Bearer <token>` mitgeschickt. Fehlender oder ungültiger Token → `401 Unauthorized`.

### 5.1 Accounts – Haupt-CRUD (Pflicht)

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|POST|`/accounts/register`|Neuen Client registrieren|manager|201, 409, 422|
|POST|`/accounts/login`|Login → gibt JWT zurück|alle|200, 401|
|GET|`/accounts/me`|Eigenen Account abrufen|user, manager|200, 401|
|GET|`/accounts`|Alle Accounts auflisten|manager|200|
|GET|`/accounts/{id}`|Einzelnen Account abrufen|user, manager|200, 404|
|PUT|`/accounts/{id}`|Account vollständig aktualisieren|manager|200, 404, 422|
|DELETE|`/accounts/{id}`|Account löschen|manager|200, 400, 404|

### 5.2 Cards – Karten CRUD

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/cards`|Eigene Karten abrufen|user, manager|200|
|GET|`/cards/all`|Alle Karten abrufen|manager|200|
|GET|`/cards/{account_id}`|Karten eines bestimmten Accounts|manager|200|
|POST|`/cards`|Neue Karte erstellen|manager|201, 404|
|PUT|`/cards/{card_id}`|Karte bearbeiten (Status, Ablaufdatum)|manager|200, 404|
|DELETE|`/cards/{card_id}`|Karte löschen|manager|200, 404|

### 5.3 Transactions – Überweisungen

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/transactions`|Eigene Transaktionen (JOIN Cards)|user, manager|200|
|GET|`/transactions/all`|Alle Transaktionen|manager|200|
|POST|`/transactions`|Überweisung erstellen (Betrag > 0, Guthaben prüfen)|user, manager|200, 400, 403, 404|

### 5.4 Stats – Aggregation (Pflicht)

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/stats/transactions-per-account`|COUNT + SUM Transaktionen pro Account (GROUP BY, JOIN)|manager|200|

### 5.5 Interests – Sparzinskonten

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/interests`|Eigene Sparzinskonten|user, manager|200|
|GET|`/interests/all`|Alle Sparzinskonten|manager|200|
|POST|`/interests`|Sparkonto eröffnen|user, manager|200, 400, 403, 404|
|POST|`/interests/{id}/withdraw`|Zinsen auszahlen (Zinseszins)|user, manager|200, 400, 403, 404|

### 5.6 Banks

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/banks`|Bankdaten abrufen (inkl. Zinssatz)|alle|200, 404|
|POST|`/banks`|Bank anlegen|manager|200|

### 5.7 Audit Logs

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/audit-logs`|Alle Audit-Log-Einträge|manager|200|
|GET|`/audit-logs/{account_id}`|Logs eines bestimmten Accounts|manager|200|

---

## 6. Rollen & Authentifizierung

|Rolle|Erlaubte Operationen|
|---|---|
|`client` (0)|GET eigene Accounts/Karten/Transaktionen/Interessen, POST Überweisung, POST Sparkonto|
|`manager` (1)|Alles — vollständiger CRUD auf allen Ressourcen|

Umsetzung via **JWT Bearer Token**. Token-Erstellung beim Login, Ablauf nach 5 Minuten. Passwörter werden mit `bcrypt` gehasht (via `passlib`). Rolle wird im Token-Payload mitgespeichert und bei jedem Request geprüft.

---

## 7. Optionale Features (Nice-to-Have)

|Feature|Beschreibung|Status|
|---|---|---|
|Erweiterte Filterung|`GET /accounts?name=Max` — Suche nach Name, Filterung nach Rolle|offen|
|Pagination|`limit` und `offset` auf allen Listen-Endpunkten|offen|
|Erweiterte Aggregation|`GET /stats/balance-per-account` — Durchschnittsguthaben pro Client (AVG)|offen|

---

## 8. Ordnerstruktur

```
BankAppAPI/
├── init_db.py              # Datenbank initialisieren (Tabellen anlegen)
│
├── src/
│   ├── main.py             # App-Start, Logging, Middleware, Router einbinden
│   ├── database.py         # SQLite-Verbindung, get_db()-Funktion
│   ├── models.py           # SQLAlchemy ORM-Modelle
│   ├── schemas.py          # Pydantic Request- & Response-Schemas
│   ├── auth.py             # JWT-Erstellung, Passwort-Hashing, Rollen-Dependency
│   ├── audit.py            # AuditLogger-Klasse
│   │
│   └── routers/
│       ├── accounts.py     # CRUD Accounts (Hauptressource)
│       ├── cards.py        # CRUD Karten
│       ├── transactions.py # Überweisungen
│       ├── interests.py    # Sparzinskonten
│       ├── bank.py         # Bankdaten
│       ├── auditlogs.py    # Audit-Log-Abfragen
│       └── stats.py        # Aggregationsendpunkte
│
└── doc/
    ├── DBI Projekt – BankApp.md
    └── erm.drawio
```

---

## 9. Bedienungsanleitung

### Voraussetzungen

```bash
pip install fastapi uvicorn sqlalchemy pydantic[email] python-jose[cryptography] passlib[bcrypt] fastapi-restful python-multipart
```

### Datenbank initialisieren

```bash
python init_db.py
```

### API starten

```bash
uvicorn src.main:app --reload
```

Swagger UI erreichbar unter: `http://127.0.0.1:8000/docs`

### Beispiel-Requests

**1. Manager registrieren (POST /accounts/register)**
```json
POST /accounts/register
{
  "firstname": "Max",
  "lastname": "Mustermann",
  "email": "max@bank.at",
  "password": "Sicher123",
  "phonenumber": "0664123456",
  "address": "Musterstraße 1",
  "birthdate": "1990-01-01",
  "role": 1
}
→ 201 Created
```

**2. Login (POST /accounts/login)**
```
POST /accounts/login
username=max@bank.at&password=Sicher123   (form-data)
→ 200 OK  { "access_token": "eyJ...", "token_type": "bearer" }
```

**3. Überweisung (POST /transactions)**
```json
Authorization: Bearer <token>
{
  "iban_from": "AT123456789012345678",
  "iban_to":   "AT987654321098765432",
  "amount_cents": 5000,
  "description": "Miete März"
}
→ 200 OK
```

**4. Statistik (GET /stats/transactions-per-account)**
```
Authorization: Bearer <token>  (manager)
→ 200 OK
[
  { "account_id": 1, "firstname": "Max", "lastname": "Mustermann",
    "transaction_count": 3, "total_cents": 15000 }
]
```

---

## 10. Must-Have vs. Nice-to-Have

### Must-Have

- Login für User und Manager (JWT)
- Client CRUD (Manager)
- Karten CRUD (Manager)
- Eigene Konten & Karten einsehen (Client)
- Überweisung erstellen (Client)
- Sparzinskonten verwalten
- JOIN-Endpunkt (Transaktionen + Kartendetails)
- Aggregationsendpunkt (Transaktionen pro Account, GROUP BY + COUNT/SUM)
- Logging in Datei (`api.log`) + Konsole
- Audit-Log für alle schreibenden Aktionen
- Parametrisierte SQL-Abfragen (SQL-Injection-Schutz via SQLAlchemy ORM)
- KI-Kennzeichnung im Code

### Nice-to-Have

- Filterparameter auf Listen-Endpunkten (`?name=...`)
- Pagination (`limit` / `offset`)
- Durchschnitts-Guthaben-Statistik (AVG)

---

## 11. Milestones

| Datum      | Ziel                                          | Zuständigkeit   |
| ---------- | --------------------------------------------- | --------------- |
| 27.05.2026 | RMs und ERMs                                  |                 |
| 28.05.2026 | Modelle implementieren                        |                 |
| 03.06.2026 | Endpoints implementiert                       |                 |
| 04.06.2026 | **Erste Demo**                                |                 |
| 10.06.2026 | Zusätzliche Endpoints implementieren          |                 |
| 11.06.2026 | Refactoring                                   |                 |
| 17.06.2026 | Backend funktioniert perfekt mit dem Frontend |                 |
| 18.06.2026 | **Projektende — Abgabe**                      |                 |

---

## 12. Projekttagebuch

| Datum      | Was wurde gemacht                                                                 | Wer |
| ---------- | --------------------------------------------------------------------------------- | --- |
| 27.05.2026 | ERM und RM erstellt, Domäne festgelegt                                            |     |
| 28.05.2026 | SQLAlchemy-Modelle angelegt (accounts, cards, transactions, interests, audit_logs)|     |
| 28.05.2026 | Datenbankverbindung (database.py) und Pydantic-Schemas (schemas.py) erstellt      |     |
| 03.06.2026 | JWT-Authentifizierung implementiert (auth.py)                                     |     |
| 03.06.2026 | Accounts-Router mit Register, Login, GET, DELETE                                  |     |
| 03.06.2026 | Cards-Router mit GET, POST, DELETE                                                |     |
| 03.06.2026 | Transactions-Router mit GET und POST (Überweisung mit Guthaben-Prüfung)           |     |
| 03.06.2026 | Interests-Router mit GET, POST, Withdraw-Endpunkt (Zinseszins-Berechnung)         |     |
| 04.06.2026 | **Erste Demo** — API läuft, Swagger UI funktioniert                               |     |
| 05.06.2026 | AuditLogger implementiert, Bank-Router hinzugefügt                                |     |
| 10.06.2026 | GET /accounts/{id} und PUT /accounts/{id} ergänzt                                 |     |
| 10.06.2026 | PUT /cards/{id} ergänzt, Route-Konflikt /cards/all gefixt                         |     |
| 10.06.2026 | Aggregationsendpunkt GET /stats/transactions-per-account implementiert            |     |
| 10.06.2026 | Python-Logging (Konsole + api.log) via Middleware konfiguriert                    |     |
| 10.06.2026 | AuditLogger in alle schreibenden Endpunkte integriert (Doppel-Commit-Bug gefixt) |     |
| 10.06.2026 | HTTP-Statuscodes korrigiert (409 Conflict, 200 OK bei DELETE)                     |     |
| 11.06.2026 | Dokumentation vervollständigt                                                     |     |
| 17.06.2026 | Backend-Frontend-Integration getestet                                             |     |
| 18.06.2026 | **Abgabe**                                                                        |     |
