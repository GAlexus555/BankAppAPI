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

Das System besteht aus **5 Tabellen**:

|Tabelle|Beschreibung|
|---|---|
|`Accounts`|Alle Benutzer (Clients + Manager) mit Rolle, Email, Passwort-Hash, Adresse, Geburtsdatum|
|`Cards`|Bankkarten eines Accounts (IBAN, CardNr, Ablaufdatum, CVC, Status)|
|`Transactions`|Überweisungen zwischen zwei Karten (Betrag, Datum, Beschreibung, Status)|
|`InterestAccounts`|Sparzinskonten — genau einer Karte zugeordnet (Betrag, Zinssatz)|
|`AuditLog`|Protokollierung aller relevanten Aktionen nach Account|

### Kardinalitäten

|Typ|Beziehung|Beispiel|
|---|---|---|
|**1:n**|Account → Cards|Ein Client hat mehrere Karten|
|**1:n**|Card → Transactions|Eine Karte ist an vielen Transaktionen beteiligt|
|**1:1**|Card ↔ InterestAccount|Eine Karte hat maximal ein Sparkonto|

> Die m:n-Beziehung wird durch `Transactions` realisiert: eine Karte sendet an viele Karten (`CardFromId`) und empfängt von vielen Karten (`CardToId`). Diese wird als eigene Zwischentabelle mit zwei Fremdschlüsseln umgesetzt.

---

## 3. Relationales Modell

**Accounts** (<u>Id</u>, Email, PasswordHash, FirstName, LastName, PhoneNumber, Address, Birthdate, Role, CreatedAt)

**Cards** (<u>Id</u>, _AccountId_, IBAN, CardNr, ExpireDate, CVC, Status)

**Transactions** (<u>Id</u>, _CardFromId_, _CardToId_, Amount, Date, Description, Status)

**InterestAccounts** (<u>Id</u>, _CardId_, Amount, InterestRate, CreatedAt)

**AuditLog** (<u>Id</u>, _AccountId_, Action, TableName, Details, Timestamp)

---

## 4. Normalformen

### `Accounts`

- **1NF:** Alle Attribute sind atomar (keine Listen, keine Wiederholungsgruppen).
- **2NF:** Kein zusammengesetzter Primärschlüssel → 2NF automatisch erfüllt.
- **3NF:** Alle Nicht-Schlüssel-Attribute hängen direkt vom Primärschlüssel `Id` ab. Keine transitiven Abhängigkeiten.

### `Cards`

- **1NF:** Alle Attribute atomar. Jede Karte hat genau eine IBAN, eine CardNr usw.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** `AccountId` ist FK, alle anderen Attribute beschreiben direkt die Karte selbst, nicht den Account.

### `Transactions`

- **1NF:** Atomar. `CardFromId` und `CardToId` sind zwei separate FK-Felder.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** Betrag, Datum und Status beschreiben die Transaktion, nicht die Karten. Keine transitiven Abhängigkeiten.

### `InterestAccounts`

- **1NF:** Atomar. Zinssatz und Betrag sind einzelne Felder.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** `Amount` und `InterestRate` hängen direkt von `Id` ab, nicht von `CardId`.

### `AuditLog`

- **1NF:** Atomar. Jeder Eintrag beschreibt genau eine Aktion zu einem Zeitpunkt.
- **2NF:** Einfacher PK → automatisch erfüllt.
- **3NF:** `Action`, `TableName`, `Details` beschreiben den Log-Eintrag direkt. `AccountId` ist nur FK-Referenz.

---

## 5. REST-API Endpunkte

**Stack:** Python · FastAPI · uvicorn · SQLite · Pydantic  
**Authentifizierung:** API-Key im Header (`X-API-Key`), zwei Keys in `.env` (einer für `user`, einer für `manager`)

### 5.1 Auth

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|POST|`/auth/login`|Login mit Email + Passwort → gibt API-Key zurück|alle|200, 401|

### 5.2 Accounts – Haupt-CRUD (Pflicht)

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/accounts`|Alle Clients auflisten (Filterparameter: `name`)|manager|200|
|GET|`/accounts/{id}`|Einzelnen Account abrufen|user, manager|200, 404|
|POST|`/accounts`|Neuen Client anlegen (nur Manager darf registrieren)|manager|201, 409, 422|
|PUT|`/accounts/{id}`|Account vollständig aktualisieren|manager|200, 404, 422|
|DELETE|`/accounts/{id}`|Account löschen|manager|200, 404|

### 5.3 Cards – Karten CRUD

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/accounts/{id}/cards`|Alle Karten eines Accounts — JOIN mit Accounts|user, manager|200, 404|
|POST|`/accounts/{id}/cards`|Neue Karte erstellen (IBAN + CVC auto-generiert)|manager|201, 404|
|PUT|`/cards/{id}`|Karte bearbeiten (z.B. Status sperren/aktiv)|manager|200, 404|
|DELETE|`/cards/{id}`|Karte löschen|manager|200, 404|

### 5.4 Transactions – Überweisungen

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/transactions`|Alle Transaktionen — JOIN Cards + Accounts|manager|200|
|GET|`/accounts/{id}/transactions`|Transaktionen eines Users inkl. Kartendetails (JOIN)|user, manager|200, 404|
|POST|`/transactions`|Überweisung erstellen (PIN-Prüfung, Betrag > 0)|user|201, 400, 404, 422|
|GET|`/stats/transactions-per-account`|Aggregation: COUNT + SUM pro Account (GROUP BY)|manager|200|

### 5.5 Interest Accounts – Sparzinskonten

|Methode|Pfad|Beschreibung|Rolle|Codes|
|---|---|---|---|---|
|GET|`/interests`|Alle Sparzinskonten — JOIN Cards + Accounts|manager|200|
|POST|`/interests`|Sparkonto eröffnen (Amount > 0, Rate > 0)|manager|201, 400, 404, 409|
|PUT|`/interests/{id}/apply`|Zinsen anwenden — erhöht Amount um Rate%|manager|200, 404|
|DELETE|`/interests/{id}`|Sparkonto auflösen|manager|200, 404|


---

## 6. Rollen & Authentifizierung

|Rolle|Erlaubte Operationen|
|---|---|
|`user` (Client)|GET eigene Accounts/Karten/Transaktionen, POST Überweisung|
|`manager` (Bank Manager)|Alles — vollständiger CRUD auf allen Ressourcen|

Umsetzung via **API-Key im Header** (`X-API-Key`). Die Keys werden in einer `.env`-Datei gespeichert und mit `python-dotenv` geladen. Fehlender oder falscher Key → `401 Unauthorized`.

---

## 7. Optionale Features (Nice-to-Have)

|Feature|Beschreibung|
|---|---|
|Erweiterte Filterung|`GET /accounts?name=Max` — Suche nach Name, Filterung nach Rolle|
|Pagination|`limit` und `offset` auf allen Listen-Endpunkten|
|Erweiterte Aggregation|`GET /stats/balance-per-account` — Durchschnittsguthaben pro Client (AVG)|

---

## 8. Ordnerstruktur

```
BankApp/
├── .env                    # API_KEY_USER=... API_KEY_MANAGER=...
│
├── src/
│   ├── main.py             # App-Start, Logger-Konfiguration, Router einbinden
│   ├── database.py         # SQLite-Verbindung, get_db()-Funktion
│   ├── models.py           # Pydantic Request- & Response-Schemas
│   ├── auth.py             # API-Key-Prüfung, Rollen-Dependency
│   │
│   └── routers/
│       ├── accounts.py     # CRUD Accounts (Hauptressource)
│       ├── cards.py        # CRUD Karten
│       ├── transactions.py # Überweisungen + Stats-Endpunkt
│       └── interests.py    # Sparzinskonten
│
└── doc/
    ├── DBI_Dokumentation_BankApp.pdf
    └── erm.drawio
```

---

## 9. Milestones

| Datum      | Ziel                                          | Zuständigkeit   |
| ---------- | --------------------------------------------- | --------------- |
| 27.05.2026 | RMs und ERMs                                  | Chiara / Alexei |
| 28.05.2026 | Modelle implementieren                        | Alexei          |
| 03.06.2026 | Endpoints implementiert                       | Alexei / Chiara |
| 04.06.2026 | **Erste Demo**                                | Alexei / Chiara |
| 10.06.2026 | Zusätzliche Endpoints implementieren          | Chiara          |
| 11.06.2026 | Refactoring                                   | Alexei / Chiara |
| 17.06.2026 | Backend funktioniert perfekt mit dem Frontend | Alexei          |
| 18.06.2026 | **Projektende — Abgabe**                      | Alexei / Chiara |

---

## 10. Must-Have vs. Nice-to-Have

### Must-Have

- Login für User und Manager
- Client CRUD (Manager)
- Karten CRUD (Manager)
- Eigene Konten & Karten einsehen (Client)
- Überweisung erstellen (Client)
- Sparzinskonten verwalten (Manager)
- JOIN-Endpunkt (Transaktionen + Kartendetails)
- Aggregationsendpunkt (Transaktionen pro Account)
- Logging in Datei + Konsole
- Parametrisierte SQL-Abfragen (SQL-Injection-Schutz)
- KI-Kennzeichnung im Code

### Nice-to-Have

- Filterparameter auf Listen-Endpunkten (`?name=...`)
- Pagination (`limit` / `offset`)
- Durchschnitts-Guthaben-Statistik (AVG)