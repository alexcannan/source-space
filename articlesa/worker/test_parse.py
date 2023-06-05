from articlesa.worker.parse import app

articles = [
    'https://www.nytimes.com/2020/04/06/technology/coronavirus-video-conference.html',
    'https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/'
]

for article in articles:
    app.send_task('parse_article', args=[article])
