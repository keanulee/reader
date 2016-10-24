import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import bs4
import urllib2


app = Flask(__name__)
CORS(app)


@app.route('/')
@app.route('/<section>/<category>/')
def list(section=None, category=None):
  try:
    url = 'https://blog.google/rss/'
    if section and category:
      url = 'https://blog.google/%s/%s/rss/' % (section, category)
    result = urllib2.urlopen(url)
    doc = bs4.BeautifulSoup(result.read(), 'html.parser')

    title = doc.title.string
    items = map(process_item, doc.find_all('item'))

    if request.args.get('json'):
      return jsonify(title=title, items=items)

    return render_template('list.html', title=title, items=items)

  except urllib2.HTTPError, e:
    return '%s Error' % e.code, e.code


def process_item(item):
  image = item.image.string if item.image else None
  if not image:
    content = bs4.BeautifulSoup(item.description.string, 'html.parser')
    img = content.img
    if img:
      image = img['src']

  return dict(title=item.title.string,
              link=item.link.string.replace('https://blog.google/', '/'),
              image=image,
              category=item.category.string,
              date=item.pubdate.string,
              author=item.author.find('name').string,
              description=item.og.description.string)


@app.route('/<section>/<category>/<post>/')
def post(section, category, post):
  try:
    url = 'https://blog.google/%s/%s/%s/' % (section, category, post)
    result = urllib2.urlopen(url)
    doc = bs4.BeautifulSoup(result.read(), 'html.parser')

    title = doc.title.string
    html = unicode(doc.find('div', class_='uni-blog-article-content'))

    if request.args.get('json'):
      return jsonify(title=title, html=html)

    return render_template('post.html', title=title, html=html)

  except urllib2.HTTPError, e:
    return '%s Error' % e.code, e.code


@app.errorhandler(500)
def server_error(e):
  return '500 Error', 500
