import streamlit as st
import praw
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from docx import Document
import io
from time import sleep
from stqdm import stqdm  # Import the stqdm progress bar

# Initialize the Reddit API (PRAW)
reddit = praw.Reddit(client_id="41Huqnmhw4KOlpZth6nAWQ", 
                     client_secret="GPt_YaaJ4Iyv9ZVmyXFkerO0nCdfkQ", 
                     user_agent="AggressiveCommentDetector/1.0 by u/Separate-Donkey-7902")

# Initialize the sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Function to fetch and analyze comments from a user's last 10 posts
def fetch_aggressive_comments_by_user(username):
    try:
        user = reddit.redditor(username)
        aggressive_comments = []
        total_comments = 0

        posts = list(user.submissions.new(limit=10))  # Fetch posts first
        total_posts = len(posts)  # Get the total number of posts
        with stqdm(posts, desc="Fetching posts...", total=total_posts) as progress_bar:
            for post in progress_bar:
                post.comments.replace_more(limit=0)
                for comment in post.comments.list():
                    total_comments += 1
                    sentiment_score = analyzer.polarity_scores(comment.body)
                    if sentiment_score['compound'] <= -0.5:
                        aggressive_comments.append({
                            'post_title': post.title,
                            'comment_body': comment.body,
                            'score': sentiment_score['compound']
                        })

        return aggressive_comments, total_comments
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return [], 0

# Function to fetch and analyze comments from a subreddit
def fetch_aggressive_comments_by_subreddit(subreddit_name):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        aggressive_comments = []
        total_comments = 0

        posts = list(subreddit.new(limit=10))  # Fetch posts first
        total_posts = len(posts)  # Get the total number of posts
        with stqdm(posts, desc="Fetching posts...", total=total_posts) as progress_bar:
            for post in progress_bar:
                post.comments.replace_more(limit=0)
                for comment in post.comments.list():
                    total_comments += 1
                    sentiment_score = analyzer.polarity_scores(comment.body)
                    if sentiment_score['compound'] <= -0.5:
                        aggressive_comments.append({
                            'post_title': post.title,
                            'comment_body': comment.body,
                            'score': sentiment_score['compound']
                        })

        return aggressive_comments, total_comments
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return [], 0

# Function to generate a Word document
def generate_word_doc(aggressive_comments):
    doc = Document()
    doc.add_heading('Aggressive Comments Report', level=1)

    for comment in aggressive_comments:
        doc.add_heading(f"Post Title: {comment['post_title']}", level=2)
        doc.add_paragraph(f"Comment: {comment['comment_body']}")
        doc.add_paragraph(f"Sentiment Score: {comment['score']}")

    word_output = io.BytesIO()
    doc.save(word_output)
    word_output.seek(0)
    return word_output

# Streamlit app
def main():
    st.title("Reddit Behavior Detection")

    search_type = st.radio(
        "Search By:",
        ('Username/Profile Link', 'Subreddit'),
        help="Choose whether to search by Reddit username/profile link or by subreddit."
    )

    user_input = st.text_input(
        "Enter Reddit Username, Profile Link, or Subreddit Name:",
        placeholder="e.g., u/username, https://www.reddit.com/user/username, or subreddit_name"
    )

    if st.button("Search"):
        if user_input:
            if search_type == 'Username/Profile Link':
                if "reddit.com" in user_input:
                    username = re.search(r'reddit\.com/user/([a-zA-Z0-9_]+)', user_input).group(1)
                else:
                    username = user_input.strip()

                with st.spinner("Fetching data..."):
                    aggressive_comments, total_comments = fetch_aggressive_comments_by_user(username)

            elif search_type == 'Subreddit':
                subreddit_name = user_input.strip()
                with st.spinner("Fetching data..."):
                    aggressive_comments, total_comments = fetch_aggressive_comments_by_subreddit(subreddit_name)

            if total_comments > 0:
                aggressive_count = len(aggressive_comments)
                st.write(f"Total Comments Analyzed: {total_comments}")
                st.write(f"Aggressive Comments Found: {aggressive_count}")

                # First progress bar for generating the report
                with stqdm(range(100), desc="Generating Report...", total=100) as progress_bar:
                    for i in range(100):  # Looping through the range to simulate progress
                        sleep(0.1)  # Simulate time for generating report
                        progress_bar.update(1)  # Update progress bar by 1 each iteration

                # Once the progress bar is complete, show the download button for the report
                if aggressive_comments:
                    word_file = generate_word_doc(aggressive_comments)
                    st.download_button(
                        label="Download Report as Word Document",
                        data=word_file,
                        file_name="aggressive_comments_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                else:
                    st.write("No aggressive comments found.")
            else:
                st.write("No comments available for analysis.")
        else:
            st.error("Please enter a valid input.")

if __name__ == "__main__":
    main()
