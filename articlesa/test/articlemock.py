""" mocks nonsense articles in a deterministic way. """

from pathlib import Path
import random

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from jinja2 import Template
from newspaper.text import StopWords


app = FastAPI()


words_file = Path("/usr/share/dict/words")
words = set(words_file.read_text().splitlines())

stop_words = StopWords().STOP_WORDS


article_template = Template("""\
<html>
    <head>
        <title>Article {{ article_id }}</title>
        <style>
            body {
                background-color: black;
                color: white;
            }
        </style>
    </head>
    <body>
        <h1>Article {{ article_id }}</h1>
        <h2>Authors: {{ article_authors }}</h2>
        <p>{{ article_text }}</p>
    </body>
</html>\
""")


@app.get("/articles/{article_id}", response_class=HTMLResponse)
async def random_article(article_id: str) -> HTMLResponse:
    """Make and return a random article initialized from article_id in path."""
    random.seed(article_id)
    n_words = 200
    article_authors = f"Alex Cannan, {' '.join(random.sample(words, 2)).title()}"
    article_words = random.sample(words, n_words)
    article_words += random.sample(stop_words, 10)
    random.shuffle(article_words)
    n_links = random.randint(1, 5)  # noqa: S311
    link_indices = random.sample(range(n_words), n_links)
    for link_index in link_indices:
        new_article_id = random.randbytes(8).hex()
        article_words[link_index] = f'<a href="/articles/{new_article_id}">{article_words[link_index]}</a>'
    article_text = " ".join(article_words)
    article_html = article_template.render(
        article_id=article_id,
        article_authors=article_authors,
        article_text=article_text,
    )
    return HTMLResponse(content=article_html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
