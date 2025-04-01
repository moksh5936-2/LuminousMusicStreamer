"""
Web interface for LuminousMusicBot - A lightweight Telegram music bot
"""
import os
import asyncio
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "luminousmusicbot_secret_key")

# configure the database, handle Heroku's DATABASE_URL format
database_url = os.environ.get("DATABASE_URL", "sqlite:///bot.db")
# Heroku uses postgres:// but SQLAlchemy requires postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension
db.init_app(app)

# Create models
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    duration = db.Column(db.String(50))
    video_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search for YouTube videos"""
    if request.method == 'POST':
        query = request.form.get('query', '')
        
        if not query:
            flash('Please enter a search query', 'warning')
            return redirect(url_for('search'))
            
        try:
            # Import the YouTube search function
            try:
                from bot.ytdl import get_video_info
                
                # Run the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                info = loop.run_until_complete(get_video_info(query))
            except ImportError:
                app.logger.error("Could not import necessary modules. Please install yt-dlp package.")
                flash('YouTube search functionality is not available. Required packages are not installed.', 'danger')
                return render_template('search.html', result=False, query=query, error="Missing required packages")
            
            if info:
                title, duration, thumbnail, video_url = info
                
                # Save to search history
                search_record = SearchHistory(
                    query=query,
                    title=title,
                    duration=duration,
                    video_url=video_url
                )
                db.session.add(search_record)
                db.session.commit()
                
                flash(f'Found video: {title}', 'success')
                return render_template('search.html', 
                                       result=True, 
                                       query=query,
                                       title=title,
                                       duration=duration,
                                       thumbnail=thumbnail,
                                       video_url=video_url)
            else:
                flash('No results found', 'warning')
                return render_template('search.html', result=False, query=query)
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            app.logger.error(f'Search error: {e}')
            return render_template('search.html', result=False, query=query, error=str(e))
    
    # GET request
    return render_template('search.html', result=None)

@app.route('/history')
def history():
    """Search history page"""
    # Fixed query syntax for newer SQLAlchemy versions
    searches = db.session.query(SearchHistory).order_by(SearchHistory.created_at.desc()).all()
    return render_template('history.html', searches=searches)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)