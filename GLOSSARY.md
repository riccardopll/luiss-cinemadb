# Cinema

A single cinema that schedules movies in its theaters, sells tickets to registered clients, and recommends movies from a short description of a client's interests.

## People

**User**:
Anyone who can log in with an email address and password. Every user has exactly one role, stored by the system: client or administrator.
_Avoid_: Account, login

**Client**:
A user who searches screenings, buys tickets and asks for recommendations.
_Avoid_: Customer, buyer

**Administrator**:
A user who manages the schedule and reads analytics. An administrator never buys tickets.
_Avoid_: Admin user, staff, manager

**Payment Method**:
A card a client has registered to pay for purchases, with its type, card number and, when relevant, a billing address.
_Avoid_: Card, wallet

## Catalog and schedule

**Movie**:
A film the cinema can show, with its title, release date, running time, original language, available languages, genres and short description.
_Avoid_: Film, title

**Available Language**:
A language a movie can be screened in. The original language is one of them.
_Avoid_: Dub, audio track

**Theater**:
A room in the cinema with a fixed maximum occupancy, optional 3D support and optional enhanced sound.
_Avoid_: Hall, room, screen

**Screening**:
One showing of a movie in a theater, at a date and start time, in one of that movie's available languages.
_Avoid_: Show, showing, session, projection

**Schedule**:
The set of all screenings.
_Avoid_: Programme, timetable

**Opening Hours**:
10:00 to 23:59 every day. A screening, including the movie's running time, must start and end within them.

## Sales

**Purchase**:
A single payment by a client for one or more tickets to one screening, paid with one of their payment methods.
_Avoid_: Order, booking, transaction

**Ticket**:
The right of one person to attend one screening. A purchase holds a number of tickets.
_Avoid_: Seat, admission

**Ticket Price**:
The price of one ticket to a screening: 15 EUR, plus 5 EUR in a 3D theater, plus 3 EUR with enhanced sound, minus 20% if the movie was released more than two years before the screening date.
_Avoid_: Fare, cost

**Available Seats**:
A screening's theater maximum occupancy minus the tickets already sold for it. Never negative.
_Avoid_: Free places, capacity

## Recommendations

**Interest Description**:
A short free text, in English or Italian, in which a client describes what they like to watch.
_Avoid_: Prompt, query, preferences

**Movie Text**:
The textual representation of a movie built from its stored information, used to compare it with an interest description.
_Avoid_: Document, movie profile

**Text Template**:
The rule that decides which movie information goes into the movie text, and in what order.

**Embedding Model**:
The pretrained model that turns movie texts and interest descriptions into vectors so they can be compared.
_Avoid_: AI model, encoder

**Recommendation**:
The three movies in the cinema's catalog whose movie text is most similar to a client's interest description, or all of them if there are fewer than three.
_Avoid_: Suggestion, match
