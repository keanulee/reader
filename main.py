import logging
from datetime import datetime
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

    title = doc.find('title').string
    items = map(process_item, doc.find_all('item'))

    if request.args.get('json'):
      return jsonify(title=title, items=items)

    return render_template('list.html', title=title, items=items)

  except urllib2.HTTPError, e:
    return '%s Error' % e.code, e.code


def process_item(item):
  image = item.image.string if item.image else None
  # if not image:
  #   content = bs4.BeautifulSoup(item.description.string, 'html.parser')
  #   img = content.img
  #   if img:
  #     image = img['src']

  return dict(title=item.title.string,
              link=item.link.string.replace('https://blog.google/', '/'),
              image=image,
              category=item.category.string,
              date=datetime.strptime(item.pubdate.string, '%a, %d %b %Y %H:%M:%S +0000'),
              author=item.author.find('name').string,
              description=item.og.description.string)


@app.route('/<section>/<category>/<post>/')
def post(section, category, post):
  try:
    url = 'https://blog.google/%s/%s/%s/' % (section, category, post)
    result = urllib2.urlopen(url)
    doc = bs4.BeautifulSoup(result.read(), 'html.parser')

    title = doc.find('title').string
    html = process_post(doc)

    if request.args.get('json'):
      return jsonify(title=title, html=html)

    return render_template('post.html', title=title, html=html)

  except urllib2.HTTPError, e:
    return '%s Error' % e.code, e.code


def process_post(doc):
  shell = doc.find('div', class_='uni-blog-article-content')

  # Convert carousels into custom elements
  carousels = shell.find_all(attrs={'uni-component':'carousel'})
  for carousel in carousels:
    # Make it a custom element
    carousel.name = 'read-carousel'
    del carousel['class']
    del carousel['uni-component']

    # Move content up so they are immediate children
    carousel.find('div', class_='uni-carousel-container').unwrap()

    # Remove controls (since they will be added to the shadow root by the element definition)
    carousel.find('div', class_='uni-carousel-arrows-container').decompose()
    carousel.find('nav').decompose()

    # Append import script
    link = doc.new_tag('link')
    link['rel'] = 'import'
    link['href'] = '/elements/read-carousel.html'
    carousel.insert_after(link)

  # Convert videos into custom elements
  videos = shell.find_all(attrs={'uni-component':'video'})
  for video in videos:
    # Make it a custom element
    video.name = 'read-video'
    video['video-id'] = video['uni-video-id']
    del video['class']
    del video['uni-component']
    del video['uni-options']
    del video['uni-video-id']
    del video['uni-block-index']

    # Move content up so they are immediate children
    video.find('div', class_='uni-video').unwrap()

    # Remove controls (since they will be added to the shadow root by the element definition)
    overlay = video.find('div', class_='uni-video-overlay')
    if overlay:
      overlay.decompose()
    video.find('div').decompose()
    button = video.find('button')
    if button:
      button.decompose()

    # Append import script
    link = doc.new_tag('link')
    link['rel'] = 'import'
    link['href'] = '/elements/read-video.html'
    video.insert_after(link)

  return unicode(shell)


@app.errorhandler(500)
def server_error(e):
  return '500 Error', 500
