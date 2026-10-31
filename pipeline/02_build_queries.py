"""Build bilingual metadata and sequel evaluation queries from the movie CSV.

Italian descriptions were translated once by an LLM and are stored below.
Relevance matches every specified metadata category: all required genres,
at least one listed keyword, and at least one listed production company.
An empty category imposes no restriction.
Metadata labels are weak labels, not human relevance judgments. Sequel queries
instead use explicit, referenced immediate-sequel relationships, checked by ID
and title against the source CSV.
"""

import json
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

QUERY_DEFINITIONS = {
    "q001": {
        "text_en": "I want a science fiction movie about journeys through outer space.",
        "text_it": "Vorrei un film di fantascienza su viaggi nello spazio.",
        "genres_all": ["Science Fiction"],
        "keywords_any": ["space travel"],
    },
    "q002": {
        "text_en": "I like science fiction stories where people travel between different times.",
        "text_it": "Mi piacciono le storie di fantascienza con viaggi nel tempo.",
        "genres_all": ["Science Fiction"],
        "keywords_any": ["time travel"],
    },
    "q003": {
        "text_en": "I'm looking for science fiction about extraterrestrial beings.",
        "text_it": "Cerco un film di fantascienza con esseri extraterrestri.",
        "genres_all": ["Science Fiction"],
        "keywords_any": ["alien"],
    },
    "q004": {
        "text_en": "I'd like science fiction in which robots play a central role.",
        "text_it": "Vorrei un film di fantascienza in cui i robot hanno un ruolo centrale.",
        "genres_all": ["Science Fiction"],
        "keywords_any": ["robot"],
    },
    "q005": {
        "text_en": "I enjoy science fiction set in oppressive future societies.",
        "text_it": "Mi piace la fantascienza ambientata in società future oppressive.",
        "genres_all": ["Science Fiction"],
        "keywords_any": ["dystopia"],
    },
    "q006": {
        "text_en": "I'd like a horror movie about someone being possessed.",
        "text_it": "Vorrei un film horror su una persona posseduta.",
        "genres_all": ["Horror"],
        "keywords_any": ["possession"],
    },
    "q007": {
        "text_en": "I enjoy horror stories involving ghosts.",
        "text_it": "Mi piacciono le storie horror con fantasmi.",
        "genres_all": ["Horror"],
        "keywords_any": ["ghost"],
    },
    "q008": {
        "text_en": "I'm in the mood for horror about vampires.",
        "text_it": "Ho voglia di un film horror sui vampiri.",
        "genres_all": ["Horror"],
        "keywords_any": ["vampire"],
    },
    "q009": {
        "text_en": "I want a horror film about the living dead.",
        "text_it": "Vorrei un film horror sui morti viventi.",
        "genres_all": ["Horror"],
        "keywords_any": ["zombie"],
    },
    "q010": {
        "text_en": "I like horror stories involving witches.",
        "text_it": "Mi piacciono le storie horror con streghe.",
        "genres_all": ["Horror"],
        "keywords_any": ["witch"],
    },
    "q011": {
        "text_en": "I'd like a crime movie about planning or carrying out a major theft.",
        "text_it": (
            "Vorrei un film poliziesco sulla preparazione o realizzazione di un grande "
            "furto."
        ),
        "genres_all": ["Crime"],
        "keywords_any": ["heist"],
    },
    "q012": {
        "text_en": "I enjoy crime stories about the mafia.",
        "text_it": "Mi piacciono le storie criminali sulla mafia.",
        "genres_all": ["Crime"],
        "keywords_any": ["mafia"],
    },
    "q013": {
        "text_en": "I want a mystery where a detective works to uncover the truth.",
        "text_it": "Vorrei un giallo in cui un detective cerca di scoprire la verità.",
        "genres_all": ["Mystery"],
        "keywords_any": ["detective"],
    },
    "q014": {
        "text_en": "I'm looking for a thriller involving a serial murderer.",
        "text_it": "Cerco un thriller con un assassino seriale.",
        "genres_all": ["Thriller"],
        "keywords_any": ["serial killer"],
    },
    "q015": {
        "text_en": "I'd like a thriller about an abduction.",
        "text_it": "Vorrei un thriller su un rapimento.",
        "genres_all": ["Thriller"],
        "keywords_any": ["kidnapping"],
    },
    "q016": {
        "text_en": "I want an action movie featuring martial arts.",
        "text_it": "Vorrei un film d'azione con arti marziali.",
        "genres_all": ["Action"],
        "keywords_any": ["martial arts"],
    },
    "q017": {
        "text_en": "I'm in the mood for superhero action.",
        "text_it": "Ho voglia di un film d'azione con supereroi.",
        "genres_all": ["Action"],
        "keywords_any": ["superhero"],
    },
    "q018": {
        "text_en": "I enjoy action stories about spies.",
        "text_it": "Mi piacciono le storie d'azione con spie.",
        "genres_all": ["Action"],
        "keywords_any": ["spy"],
    },
    "q019": {
        "text_en": "I want an adventure about struggling to stay alive.",
        "text_it": "Vorrei un film d'avventura sulla lotta per sopravvivere.",
        "genres_all": ["Adventure"],
        "keywords_any": ["survival"],
    },
    "q020": {
        "text_en": "I enjoy adventure stories involving treasure.",
        "text_it": "Mi piacciono le storie d'avventura che coinvolgono un tesoro.",
        "genres_all": ["Adventure"],
        "keywords_any": ["treasure"],
    },
    "q021": {
        "text_en": "I'd like a fantasy movie involving magic.",
        "text_it": "Vorrei un film fantasy con la magia.",
        "genres_all": ["Fantasy"],
        "keywords_any": ["magic"],
    },
    "q022": {
        "text_en": "I'm looking for a fantasy story featuring dragons.",
        "text_it": "Cerco una storia fantasy con draghi.",
        "genres_all": ["Fantasy"],
        "keywords_any": ["dragon"],
    },
    "q023": {
        "text_en": "I want a fantasy movie inspired by fairy tales.",
        "text_it": "Vorrei un film fantasy ispirato alle fiabe.",
        "genres_all": ["Fantasy"],
        "keywords_any": ["fairy tale"],
    },
    "q024": {
        "text_en": "I'd like an animated movie made with stop-motion techniques.",
        "text_it": "Vorrei un film d'animazione realizzato con la tecnica della stop motion.",
        "genres_all": ["Animation"],
        "keywords_any": ["stop motion"],
    },
    "q025": {
        "text_en": "I'm in the mood for an anime film.",
        "text_it": "Ho voglia di guardare un film anime.",
        "genres_all": ["Animation"],
        "keywords_any": ["anime"],
    },
    "q026": {
        "text_en": "I want a family movie in which a dog plays a role.",
        "text_it": "Vorrei un film per famiglie in cui compare un cane.",
        "genres_all": ["Family"],
        "keywords_any": ["dog"],
    },
    "q027": {
        "text_en": "I'd like a family movie with a Christmas theme.",
        "text_it": "Vorrei un film per famiglie a tema natalizio.",
        "genres_all": ["Family"],
        "keywords_any": ["christmas"],
    },
    "q028": {
        "text_en": "I enjoy comedies about road trips.",
        "text_it": "Mi piacciono le commedie sui viaggi su strada.",
        "genres_all": ["Comedy"],
        "keywords_any": ["road trip"],
    },
    "q029": {
        "text_en": "I'd like a comedy that parodies familiar stories or conventions.",
        "text_it": "Vorrei una commedia che faccia la parodia di storie o convenzioni note.",
        "genres_all": ["Comedy"],
        "keywords_any": ["parody"],
    },
    "q030": {
        "text_en": "I'm in the mood for a satirical comedy.",
        "text_it": "Ho voglia di una commedia satirica.",
        "genres_all": ["Comedy"],
        "keywords_any": ["satire"],
    },
    "q031": {
        "text_en": "I want a romance involving a wedding.",
        "text_it": "Vorrei un film romantico che coinvolga un matrimonio.",
        "genres_all": ["Romance"],
        "keywords_any": ["wedding"],
    },
    "q032": {
        "text_en": "I enjoy romantic stories about love triangles.",
        "text_it": "Mi piacciono le storie romantiche sui triangoli amorosi.",
        "genres_all": ["Romance"],
        "keywords_any": ["love triangle"],
    },
    "q033": {
        "text_en": "I'd like a romance about experiencing love for the first time.",
        "text_it": "Vorrei un film romantico sull'esperienza del primo amore.",
        "genres_all": ["Romance"],
        "keywords_any": ["first love"],
    },
    "q034": {
        "text_en": "I want a drama about growing up and becoming an adult.",
        "text_it": "Vorrei un film drammatico sulla crescita e sul passaggio all'età adulta.",
        "genres_all": ["Drama"],
        "keywords_any": ["coming of age"],
    },
    "q035": {
        "text_en": "I'd like a drama exploring friendship.",
        "text_it": "Vorrei un film drammatico che esplori l'amicizia.",
        "genres_all": ["Drama"],
        "keywords_any": ["friendship"],
    },
    "q036": {
        "text_en": "I'm looking for a drama involving life in prison.",
        "text_it": "Cerco un film drammatico che racconti la vita in prigione.",
        "genres_all": ["Drama"],
        "keywords_any": ["prison"],
    },
    "q037": {
        "text_en": "I enjoy dramas about relationships between parents and their children.",
        "text_it": "Mi piacciono i film drammatici sui rapporti tra genitori e figli.",
        "genres_all": ["Drama"],
        "keywords_any": ["parent child relationship"],
    },
    "q038": {
        "text_en": "I want a war movie set during the Second World War.",
        "text_it": "Vorrei un film di guerra ambientato durante la Seconda guerra mondiale.",
        "genres_all": ["War"],
        "keywords_any": ["world war ii"],
    },
    "q039": {
        "text_en": "I'd like a war film about soldiers.",
        "text_it": "Vorrei un film di guerra sui soldati.",
        "genres_all": ["War"],
        "keywords_any": ["soldier"],
    },
    "q040": {
        "text_en": "I want a historical movie connected to ancient Rome.",
        "text_it": "Vorrei un film storico legato all'antica Roma.",
        "genres_all": ["History"],
        "keywords_any": ["ancient rome"],
    },
    "q041": {
        "text_en": "I'm interested in a historical film about the French Revolution.",
        "text_it": "Mi interessa un film storico sulla Rivoluzione francese.",
        "genres_all": ["History"],
        "keywords_any": ["french revolution"],
    },
    "q042": {
        "text_en": "I'd like a western involving gunfights.",
        "text_it": "Vorrei un western con scontri a fuoco.",
        "genres_all": ["Western"],
        "keywords_any": ["gunfight"],
    },
    "q043": {
        "text_en": "I want a western featuring cowboys.",
        "text_it": "Vorrei un western con cowboy.",
        "genres_all": ["Western"],
        "keywords_any": ["cowboy"],
    },
    "q044": {
        "text_en": "I'm looking for a documentary about the natural world.",
        "text_it": "Cerco un documentario sul mondo naturale.",
        "genres_all": ["Documentary"],
        "keywords_any": ["nature"],
    },
    "q045": {
        "text_en": "I'd like a documentary examining climate change.",
        "text_it": "Vorrei un documentario che esamini il cambiamento climatico.",
        "genres_all": ["Documentary"],
        "keywords_any": ["climate change"],
    },
    "q046": {
        "text_en": "I want a documentary about outer space.",
        "text_it": "Vorrei un documentario sullo spazio.",
        "genres_all": ["Documentary"],
        "keywords_any": ["space"],
    },
    "q047": {
        "text_en": "I'd like a music film featuring a concert.",
        "text_it": "Vorrei un film musicale che includa un concerto.",
        "genres_all": ["Music"],
        "keywords_any": ["concert"],
    },
    "q048": {
        "text_en": "I'm interested in a music film about jazz.",
        "text_it": "Mi interessa un film musicale sul jazz.",
        "genres_all": ["Music"],
        "keywords_any": ["jazz"],
    },
    "q049": {
        "text_en": "I want a drama involving boxing.",
        "text_it": "Vorrei un film drammatico che parli di pugilato.",
        "genres_all": ["Drama"],
        "keywords_any": ["boxing"],
    },
    "q050": {
        "text_en": "I'm looking for an adventure involving pirates.",
        "text_it": "Cerco un film d'avventura con pirati.",
        "genres_all": ["Adventure"],
        "keywords_any": ["pirate"],
    },
    "q051": {
        "text_en": "I'm looking for a movie produced by Pixar.",
        "text_it": "Cerco un film prodotto dalla Pixar.",
        "genres_all": [],
        "keywords_any": [],
        "production_companies_any": ["Pixar"],
    },
    "q052": {
        "text_en": "I'd like to watch a film produced by Studio Ghibli.",
        "text_it": "Vorrei guardare un film prodotto dallo Studio Ghibli.",
        "genres_all": [],
        "keywords_any": [],
        "production_companies_any": ["Studio Ghibli"],
    },
    "q053": {
        "text_en": "I want a movie produced by Metro-Goldwyn-Mayer.",
        "text_it": "Vorrei un film prodotto dalla Metro-Goldwyn-Mayer.",
        "genres_all": [],
        "keywords_any": [],
        "production_companies_any": ["Metro-Goldwyn-Mayer"],
    },
    "q054": {
        "text_en": "I want an animated film produced by Walt Disney Pictures.",
        "text_it": "Vorrei un film d'animazione prodotto dalla Walt Disney Pictures.",
        "genres_all": ["Animation"],
        "keywords_any": [],
        "production_companies_any": ["Walt Disney Pictures"],
    },
    "q055": {
        "text_en": "I'd like a horror film produced by Blumhouse Productions.",
        "text_it": "Vorrei un film horror prodotto dalla Blumhouse Productions.",
        "genres_all": ["Horror"],
        "keywords_any": [],
        "production_companies_any": ["Blumhouse Productions"],
    },
    "q056": {
        "text_en": "I'm looking for science fiction produced by Legendary Pictures.",
        "text_it": "Cerco un film di fantascienza prodotto dalla Legendary Pictures.",
        "genres_all": ["Science Fiction"],
        "keywords_any": [],
        "production_companies_any": ["Legendary Pictures"],
    },
    "q057": {
        "text_en": "I want a superhero action movie produced by Marvel Studios.",
        "text_it": "Vorrei un film d'azione con supereroi prodotto dai Marvel Studios.",
        "genres_all": ["Action"],
        "keywords_any": ["superhero"],
        "production_companies_any": ["Marvel Studios"],
    },
    "q058": {
        "text_en": "I'd like an animated story about friendship produced by Pixar.",
        "text_it": "Vorrei una storia d'animazione sull'amicizia prodotta dalla Pixar.",
        "genres_all": ["Animation"],
        "keywords_any": ["friendship"],
        "production_companies_any": ["Pixar"],
    },
    "q059": {
        "text_en": "I want a fantasy movie involving magic, produced by Warner Bros. Pictures.",
        "text_it": "Vorrei un film fantasy con la magia, prodotto dalla Warner Bros. Pictures.",
        "genres_all": ["Fantasy"],
        "keywords_any": ["magic"],
        "production_companies_any": ["Warner Bros. Pictures"],
    },
    "q060": {
        "text_en": "I'm looking for a mafia crime film produced by Paramount.",
        "text_it": "Cerco un film criminale sulla mafia prodotto dalla Paramount.",
        "genres_all": ["Crime"],
        "keywords_any": ["mafia"],
        "production_companies_any": ["Paramount", "Paramount Pictures"],
    },
    "q061": {
        "text_en": "I'd like science fiction about aliens produced by 20th Century Fox.",
        "text_it": "Vorrei un film di fantascienza con alieni prodotto dalla 20th Century Fox.",
        "genres_all": ["Science Fiction"],
        "keywords_any": ["alien"],
        "production_companies_any": ["20th Century Fox"],
    },
    "q062": {
        "text_en": "I want a nature documentary produced by Disneynature.",
        "text_it": "Vorrei un documentario sulla natura prodotto dalla Disneynature.",
        "genres_all": ["Documentary"],
        "keywords_any": ["nature"],
        "production_companies_any": ["Disneynature"],
    },
    "q063": {
        "query_type": "sequel",
        "text_en": 'What is the next movie after "Toy Story"?',
        "text_it": 'Qual è il film successivo a "Toy Story"?',
        "source_movie_id": 862,
        "source_movie_title": "Toy Story",
        "relevant_movie_ids": [863],
        "expected_sequel_title": "Toy Story 2",
        "ground_truth_source": "https://www.pixar.com/toy-story-2",
    },
    "q064": {
        "query_type": "sequel",
        "text_en": 'I watched "Toy Story 2". Which movie continues the story next?',
        "text_it": 'Ho visto "Toy Story 2". Quale film continua la storia subito dopo?',
        "source_movie_id": 863,
        "source_movie_title": "Toy Story 2",
        "relevant_movie_ids": [10193],
        "expected_sequel_title": "Toy Story 3",
        "ground_truth_source": "https://www.pixar.com/toy-story-3",
    },
    "q065": {
        "query_type": "sequel",
        "text_en": 'I want to watch the sequel to "Finding Nemo".',
        "text_it": 'Vorrei guardare il seguito di "Finding Nemo".',
        "source_movie_id": 12,
        "source_movie_title": "Finding Nemo",
        "relevant_movie_ids": [127380],
        "expected_sequel_title": "Finding Dory",
        "ground_truth_source": "https://www.pixar.com/finding-dory",
    },
    "q066": {
        "query_type": "sequel",
        "text_en": 'Which film follows "The Incredibles"?',
        "text_it": 'Quale film viene dopo "The Incredibles"?',
        "source_movie_id": 9806,
        "source_movie_title": "The Incredibles",
        "relevant_movie_ids": [260513],
        "expected_sequel_title": "Incredibles 2",
        "ground_truth_source": "https://www.pixar.com/incredibles-2",
    },
    "q067": {
        "query_type": "sequel",
        "text_en": 'What is the direct sequel to "Frozen"?',
        "text_it": 'Qual è il seguito diretto di "Frozen"?',
        "source_movie_id": 109445,
        "source_movie_title": "Frozen",
        "relevant_movie_ids": [330457],
        "expected_sequel_title": "Frozen II",
        "ground_truth_source": "https://movies.disney.com/frozen-2",
    },
    "q068": {
        "query_type": "sequel",
        "text_en": 'I enjoyed "Shrek". Show me its immediate sequel.',
        "text_it": 'Mi è piaciuto "Shrek". Mostrami il suo seguito diretto.',
        "source_movie_id": 808,
        "source_movie_title": "Shrek",
        "relevant_movie_ids": [809],
        "expected_sequel_title": "Shrek 2",
        "ground_truth_source": "https://www.dreamworks.com/movies/shrek-2",
    },
    "q069": {
        "query_type": "sequel",
        "text_en": 'Which movie comes directly after "The Godfather"?',
        "text_it": 'Quale film viene subito dopo "The Godfather"?',
        "source_movie_id": 238,
        "source_movie_title": "The Godfather",
        "relevant_movie_ids": [240],
        "expected_sequel_title": "The Godfather Part II",
        "ground_truth_source": "https://www.paramountpictures.com/movies/the-godfather-part-ii",
    },
    "q070": {
        "query_type": "sequel",
        "text_en": (
            'I have seen "Back to the Future". What should I watch to continue the story?'
        ),
        "text_it": 'Ho visto "Back to the Future". Cosa devo guardare per continuare la storia?',
        "source_movie_id": 105,
        "source_movie_title": "Back to the Future",
        "relevant_movie_ids": [165],
        "expected_sequel_title": "Back to the Future Part II",
        "ground_truth_source": "https://www.backtothefuture.com/movies/backtothefuture2",
    },
}


def parse_tags(value: str) -> set[str]: #get the tags from the genres, keywords and production companies columns
    """Match complete hyphen-separated values, ignoring case and outside whitespace."""
    return {tag.strip().casefold() for tag in value.split("-") if tag.strip()}


def get_sequel_labels(query_id: str, definition: dict, titles: dict[int, str]) -> dict: #get a dictionary of labels for a sequel query, including the source movie ID, title, relevant movie IDs, and ground truth source
    """Validate an explicit next-movie answer and return its evaluation labels."""
    source_id = definition["source_movie_id"]
    relevant_ids = definition["relevant_movie_ids"]
    if len(relevant_ids) != 1 or source_id in relevant_ids:
        raise ValueError(f"{query_id} must name exactly one sequel, different from its source.")

    expected_titles = {
        source_id: definition["source_movie_title"],
        relevant_ids[0]: definition["expected_sequel_title"],
    }
    for movie_id, expected_title in expected_titles.items():
        if movie_id not in titles:
            raise ValueError(f"{query_id}: movie ID {movie_id} is missing from the input CSV.")
        if titles[movie_id] != expected_title:
            raise ValueError(
                f"{query_id}: movie ID {movie_id} should be {expected_title!r}, "
                f"but the CSV contains {titles[movie_id]!r}."
            )

    return {
        "query_type": "sequel",
        "source_movie_id": source_id,
        "source_movie_title": titles[source_id],
        "relevant_movie_ids": list(relevant_ids),
        "ground_truth_source": definition["ground_truth_source"],
    }


def build_queries(input_path: Path, output_dir: Path) -> None: #build the queries and save them to the output directory
    # Load the cleaned output of script 01; keep the overview for later embedding.
    movies = pd.read_csv(
        input_path,
        usecols=["id", "title", "overview", "genres", "keywords", "production_companies"],
        dtype={
            "id": "int64",
            "title": str,
            "overview": str,
            "genres": str,
            "keywords": str,
            "production_companies": str,
        },
        keep_default_na=False,
    )
    if movies["id"].duplicated().any():
        raise ValueError(
            "The input contains duplicate movie IDs. Run 01_prepare_dataset.py "
            "and use its df_modified_01.csv output."
        )

    # Index only the tags used by our queries, then intersect sets of movie IDs.
    genre_index = {
        genre.casefold(): set()
        for query in QUERY_DEFINITIONS.values()
        for genre in query.get("genres_all", [])
    } #dictionary where the keys are the genres and the values are sets of movie IDs that have that genre
    keyword_index = {
        keyword.casefold(): set()
        for query in QUERY_DEFINITIONS.values()
        for keyword in query.get("keywords_any", [])
    } #keyword index is a dictionary where the keys are the keywords and the values are sets of movie IDs that have that keyword
    company_index = {} #same for the production companies, but we don't know the list of companies in advance, so we build it from the queries
    for query in QUERY_DEFINITIONS.values():
        for company in query.get("production_companies_any", []):
            company_key = company.casefold()
            if company_key in company_index:
                continue
            # Match full names, including names with internal hyphens such as MGM.
            pattern = rf"(?:^|-)\s*{re.escape(company)}\s*(?:-|$)"
            matching_companies = movies["production_companies"].str.contains(
                pattern, case=False, regex=True
            )
            company_index[company_key] = set(movies.loc[matching_companies, "id"])
    titles = {} #for titles, we create a dictionary where the keys are the movie IDs and the values are the movie titles
    for movie in movies.itertuples(index=False):
        titles[movie.id] = movie.title
        for genre in parse_tags(movie.genres):
            if genre in genre_index:
                genre_index[genre].add(movie.id)
        for keyword in parse_tags(movie.keywords):
            if keyword in keyword_index:
                keyword_index[keyword].add(movie.id)

    queries_en = {}
    queries_it = {}
    ground_truth = {}
    for query_id, definition in QUERY_DEFINITIONS.items(): #for each query in the QUERY_DEFINITIONS dictionary, we get the query type and build the labels accordingly
        query_type = definition.get("query_type", "metadata") #to evaluate the query type, we check if it is a sequel or metadata query. If it is a sequel query, we call the get_sequel_labels function to get the labels for the query. If it is a metadata query, we build the labels based on the genres, keywords, and production companies specified in the definition.
        if query_type == "sequel":
            labels = get_sequel_labels(query_id, definition, titles)
        elif query_type == "metadata":
            # Each supplied category must match. Empty categories add no restriction.
            required_sets = [genre_index[tag.casefold()] for tag in definition["genres_all"]]
            if definition["keywords_any"]: #add the keywords to the required sets if they are specified in the definition. We use set.union to combine the sets of movie IDs for each keyword, so that we can find the intersection of all required sets later. If no keywords are specified, we raise a ValueError to indicate that at least one metadata condition must be specified.
                keyword_sets = [keyword_index[tag.casefold()] for tag in definition["keywords_any"]] 
                required_sets.append(set.union(*keyword_sets))
            companies = definition.get("production_companies_any", [])
            if companies: #same for the production companies, we add the sets of movie IDs for each company to the required sets if they are specified in the definition. We use set.union to combine the sets of movie IDs for each company, so that we can find the intersection of all required sets later. If no metadata are specified, we raise a ValueError to indicate that at least one metadata condition must be specified.
                company_sets = [company_index[company.casefold()] for company in companies]
                required_sets.append(set.union(*company_sets))
            if not required_sets:
                raise ValueError(f"{query_id} must specify at least one metadata condition.")
            labels = {"query_type": "metadata",
                "genres_all": definition["genres_all"],
                "keywords_any": definition["keywords_any"],
                "production_companies_any": companies,
                "relevant_movie_ids": sorted(set.intersection(*required_sets))} 
        else:
            raise ValueError(f"{query_id}: unknown query type {query_type!r}.")
        #NB the use of union is because we want to find movies that match any of the keywords or production companies, but all of the genres. The intersection is used to find movies that match all of the required sets, which includes the genres and any of the keywords or production companies.
        relevant_ids = labels["relevant_movie_ids"]
        if not relevant_ids:
            raise ValueError(f"{query_id} has no matching movies: {definition}")

        queries_en[query_id] = {"text": definition["text_en"], **labels}
        queries_it[query_id] = {"text": definition["text_it"], **labels}
        ground_truth[query_id] = {
            "query_type": query_type,
            "relevant_movie_count": len(relevant_ids),
            "relevant_movies": [
                {"movie_id": movie_id, "title": titles[movie_id]}
                for movie_id in relevant_ids
            ],
        } #build the ground truth dictionary for each query, which includes the query type, the number of relevant movies, and a list of relevant movies with their IDs and titles. If the query type is "sequel", we also add the source movie ID, title, and ground truth source to the ground truth dictionary.
        if query_type == "sequel":
            ground_truth[query_id].update({
                "source_movie_id": labels["source_movie_id"],
                "source_movie_title": labels["source_movie_title"],
                "ground_truth_source": labels["ground_truth_source"],
            }) #update the ground truth dictionary for sequel queries to include the source movie ID, title, and ground truth source.
        print(f"{query_id}: {len(relevant_ids):4d} relevant movies | {definition['text_en']}")

    output_dir.mkdir(parents=True, exist_ok=True) #create the output directory if it doesn't exist
    dataframe_path = output_dir / "df_modified_02.csv"
    movies.to_csv(dataframe_path, index=False, encoding="utf-8")
    print("Modified DataFrame saved to:", dataframe_path)
    for filename, content in [("queries_en.json", queries_en),
        ("queries_it.json", queries_it),
        ("ground_truth.json", ground_truth)]:
        output_path = output_dir / filename
        with output_path.open("w", encoding="utf-8") as destination:
            json.dump(content, destination, ensure_ascii=False, indent=2)
            destination.write("\n")
        print("Saved:", output_path)


if __name__ == "__main__":
    build_queries(DATA_DIR / "df_modified_01.csv", DATA_DIR)
