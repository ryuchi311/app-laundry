# Headless test: fetch /daily-calendar and print a sample day cell showing Total and Earn
import re
import sys
import os
from bs4 import BeautifulSoup

# Ensure project path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

YEAR = 2025
MONTH = 8

app = create_app()
app.testing = True

with app.app_context():
    client = app.test_client()

    # Ensure test user exists
    test_email = 'test+calendar@example.com'
    test_pass = 'testpass'
    user = User.query.filter_by(email=test_email).first()
    if not user:
        u = User(email=test_email, full_name='Test Calendar', role='admin')
        u.password = generate_password_hash(test_pass)
        db.session.add(u)
        db.session.commit()
        print('Created test user')

    # Login via auth route
    login_data = {'email': test_email, 'password': test_pass}
    resp = client.post('/auth/login', data=login_data, follow_redirects=True)
    print('Login status:', resp.status_code)

    # Fetch daily calendar
    url = f'/daily-calendar?year={YEAR}&month={MONTH:02d}'
    resp = client.get(url)
    print('GET', url, 'status:', resp.status_code)
    if resp.status_code != 200:
        print('Failed to fetch daily calendar')
        sys.exit(1)

    # Parse HTML and find first non-empty day cell
    soup = BeautifulSoup(resp.data, 'html.parser')
    # cells: td.border
    cells = soup.select('table tbody td')
    sample = None
    for c in cells:
        # ignore empty cells visually (they have bg-gray-50)
        if 'bg-gray-50' in c.get('class', []):
            continue
        text = c.get_text(separator=' ').strip()
        if 'Total:' in text:
            sample = c
            break

    if sample is None:
        print('No day cell with Total found')
        sys.exit(1)

    # Print the HTML for the sample cell and whether Earn appears
    cell_html = str(sample)
    has_earn = 'Earn:' in cell_html
    print('\nSample day cell HTML:')
    print(cell_html)
    print('\nContains Earn:', has_earn)

    # Also print the line that shows Total and Earn text
    match = re.search(r'<div[^>]*>(?:\s|\S)*?Total:(?:\s|\S)*?<', cell_html)
    # Instead, extract the small text div
    small_div = sample.find('div', {'class': 'text-xs text-gray-500'})
    if small_div:
        print('\nSmall info div text:')
        print(small_div.get_text(' ', strip=True))
    
    print('\nDone')
