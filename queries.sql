-- Search upcoming screenings by title, genre, language, date and time, with ticket price and available seats
SET @title = NULL, @genre = NULL, @language = NULL, @date = NULL, @time = NULL;
SELECT
    s.id,
    m.title,
    s.theater_id,
    s.starts_at,
    l.name AS language,
    ROUND(
        (15
         + CASE WHEN t.supports_3d THEN 5 ELSE 0 END
         + CASE WHEN t.has_enhanced_sound THEN 3 ELSE 0 END)
        * CASE WHEN m.release_date < DATE(s.starts_at) - INTERVAL 2 YEAR THEN 0.8 ELSE 1 END,
        2
    ) AS ticket_price,
    t.max_occupancy - s.tickets_sold AS available_seats,
    t.supports_3d,
    t.has_enhanced_sound
FROM screening s
JOIN movie m ON m.id = s.movie_id
JOIN theater t ON t.id = s.theater_id
JOIN language l ON l.id = s.language_id
WHERE s.starts_at > NOW()
  AND (@title IS NULL OR m.title LIKE CONCAT('%', @title, '%'))
  AND (@genre IS NULL OR m.id IN (
        SELECT mg.movie_id
        FROM movie_genre mg
        JOIN genre g ON g.id = mg.genre_id
        WHERE g.name = @genre))
  AND (@language IS NULL OR l.name = @language)
  AND (@date IS NULL OR DATE(s.starts_at) = @date)
  AND (@time IS NULL OR TIME(s.starts_at) >= @time)
ORDER BY s.starts_at, s.theater_id;

-- A client's previous purchases, newest first
SET @client_id = 2;
SELECT
    p.id,
    p.purchased_at,
    m.title,
    s.theater_id,
    s.starts_at,
    l.name AS language,
    p.num_tickets,
    p.total_amount,
    pm.type AS card_type,
    RIGHT(pm.card_number, 4) AS card_last_digits
FROM purchase p
JOIN payment_method pm ON pm.id = p.payment_method_id
JOIN screening s ON s.id = p.screening_id
JOIN movie m ON m.id = s.movie_id
JOIN language l ON l.id = s.language_id
WHERE pm.client_id = @client_id
ORDER BY p.purchased_at DESC;

-- Screenings in a theater that overlap a new screening or are less than 10 minutes apart from it
SET @theater_id = 1, @starts_at = TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '18:40'), @movie_id = 29;
SELECT
    s.id,
    m.title,
    s.starts_at,
    s.starts_at + INTERVAL m.running_time_minutes MINUTE AS ends_at
FROM screening s
JOIN movie m ON m.id = s.movie_id
WHERE s.theater_id = @theater_id
  AND s.starts_at < @starts_at + INTERVAL (
        SELECT running_time_minutes FROM movie WHERE id = @movie_id) + 10 MINUTE
  AND s.starts_at + INTERVAL m.running_time_minutes + 10 MINUTE > @starts_at;

-- Remaining capacity of upcoming screenings
SELECT
    s.id,
    m.title,
    s.theater_id,
    s.starts_at,
    s.tickets_sold,
    t.max_occupancy,
    t.max_occupancy - s.tickets_sold AS remaining_seats,
    ROUND(100 * s.tickets_sold / t.max_occupancy, 1) AS occupancy_percent
FROM screening s
JOIN movie m ON m.id = s.movie_id
JOIN theater t ON t.id = s.theater_id
WHERE s.starts_at > NOW()
ORDER BY s.starts_at, s.theater_id;

-- Screenings, tickets sold, average occupancy and revenue by movie
SELECT
    m.title,
    COUNT(*) AS screenings,
    SUM(s.tickets_sold) AS tickets_sold,
    ROUND(100 * AVG(s.tickets_sold / t.max_occupancy), 1) AS average_occupancy_percent,
    SUM(COALESCE(r.revenue, 0)) AS revenue
FROM screening s
JOIN movie m ON m.id = s.movie_id
JOIN theater t ON t.id = s.theater_id
LEFT JOIN (
    SELECT screening_id, SUM(total_amount) AS revenue
    FROM purchase
    GROUP BY screening_id
) r ON r.screening_id = s.id
WHERE s.starts_at < NOW()
GROUP BY m.id, m.title
ORDER BY revenue DESC, m.title;
