import streamlit as st
import praw
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from docx import Document
import io
from time import sleep
from stqdm import stqdm  # For a progress bar in Streamlit
import matplotlib.pyplot as plt

# Setting up the Reddit API using PRAW
reddit = praw.Reddit(
    client_id="41Huqnmhw4KOlpZth6nAWQ", 
    client_secret="GPt_YaaJ4Iyv9ZVmyXFkerO0nCdfkQ", 
    user_agent="AggressiveCommentDetector/1.0 by u/Separate-Donkey-7902"
)

# Initializing the sentiment analyzer (VADER)
analyzer = SentimentIntensityAnalyzer()

# Function to analyze a user's comments for aggressive behavior
def fetch_aggressive_comments_by_user(username):
    try:
        # Access the user's Reddit profile
        user = reddit.redditor(username)
        aggressive_comments = []
        total_comments = 0

        # Get the user's last 10 posts
        posts = list(user.submissions.new(limit=10))
        total_posts = len(posts)

        # Process posts with a progress bar
        with stqdm(posts, desc="Fetching posts...", total=total_posts) as progress_bar:
            for post in progress_bar:
                post.comments.replace_more(limit=0)  # Flatten nested comments
                for comment in post.comments.list():
                    total_comments += 1
                    # Analyze comment sentiment
                    sentiment_score = analyzer.polarity_scores(comment.body)
                    if sentiment_score['compound'] <= -0.5:  # Check if the comment is aggressive
                        aggressive_comments.append({
                            'post_title': post.title,
                            'comment_body': comment.body,
                            'score': sentiment_score['compound']
                        })

        return aggressive_comments, total_comments
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return [], 0

# Function to analyze comments in a subreddit
def fetch_aggressive_comments_by_subreddit(subreddit_name):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        aggressive_comments = []
        total_comments = 0

        # Get the last 10 posts in the subreddit
        posts = list(subreddit.new(limit=10))
        total_posts = len(posts)

        # Process posts with a progress bar
        with stqdm(posts, desc="Fetching posts...", total=total_posts) as progress_bar:
            for post in progress_bar:
                post.comments.replace_more(limit=0)  # Flatten nested comments
                for comment in post.comments.list():
                    total_comments += 1
                    # Analyze comment sentiment
                    sentiment_score = analyzer.polarity_scores(comment.body)
                    if sentiment_score['compound'] <= -0.5:  # Check if the comment is aggressive
                        aggressive_comments.append({
                            'post_title': post.title,
                            'comment_body': comment.body,
                            'score': sentiment_score['compound']
                        })

        return aggressive_comments, total_comments
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return [], 0

# Function to create a Word document with the aggressive comments
def generate_word_doc(aggressive_comments):
    doc = Document()
    doc.add_heading('Aggressive Comments Report', level=1)

    # Add each comment to the Word document
    for comment in aggressive_comments:
        doc.add_heading(f"Post Title: {comment['post_title']}", level=2)
        doc.add_paragraph(f"Comment: {comment['comment_body']}")
        doc.add_paragraph(f"Sentiment Score: {comment['score']}")

    # Save the document to an in-memory buffer
    word_output = io.BytesIO()
    doc.save(word_output)
    word_output.seek(0)
    return word_output

# Function to display a pie chart of aggressive vs non-aggressive comments
def plot_aggressive_comments(total_comments, aggressive_count):
    fig, ax = plt.subplots()
    labels = ['Aggressive', 'Non-Aggressive']
    sizes = [aggressive_count, total_comments - aggressive_count]
    colors = ['#FF5733', '#4CAF50']
    explode = (0.1, 0)  # Highlight the aggressive slice
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Ensure the pie chart is circular

    # Render the pie chart in Streamlit
    st.pyplot(fig)

# Main Streamlit app function
def main():
    st.title("Reddit Behavior Detection")

    # Let the user choose between analyzing a profile or a subreddit
    search_type = st.radio(
        "Search By:",
        ('Username/Profile Link', 'Subreddit'),
        help="Choose whether to search by Reddit username/profile link or by subreddit."
    )

    # Input field for the username or subreddit name
    user_input = st.text_input(
        "Enter Reddit Username, Profile Link, or Subreddit Name:",
        placeholder="e.g., u/username, https://www.reddit.com/user/username, or subreddit_name"
    )

    if st.button("Search"):
        if user_input:
            if search_type == 'Username/Profile Link':
                # Extract username from a link if provided
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

            # Display results if comments were found
            if total_comments > 0:
                aggressive_count = len(aggressive_comments)
                st.write(f"Total Comments Analyzed: {total_comments}")
                st.write(f"Aggressive Comments Found: {aggressive_count}")

                # Progress bar for generating the report
                with stqdm(range(100), desc="Generating Report...", total=100) as progress_bar:
                    for _ in range(100):
                        sleep(0.1)
                        progress_bar.update(1)

                # Provide a download button for the Word document report
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

                # Show a pie chart of the analysis
                plot_aggressive_comments(total_comments, aggressive_count)
            else:
                st.write("No comments available for analysis.")
        else:
            st.error("Please enter a valid input.")

if __name__ == "__main__":
    main()
