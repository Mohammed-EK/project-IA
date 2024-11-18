import streamlit as st
import praw
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from docx import Document
import io

# Initialize the Reddit API (PRAW)
reddit = praw.Reddit(client_id="41Huqnmhw4KOlpZth6nAWQ", 
                     client_secret="GPt_YaaJ4Iyv9ZVmyXFkerO0nCdfkQ", 
                     user_agent="AggressiveCommentDetector/1.0 by u/Separate-Donkey-7902")

# Initialize the sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Function to fetch and analyze comments from a user's last 10 posts
def fetch_aggressive_comments(username):
    try:
        # Get the user profile
        user = reddit.redditor(username)
        aggressive_comments = []

        # Fetch the last 10 submissions
        posts = user.submissions.new(limit=10)

        for post in posts:
            post.comments.replace_more(limit=0)  # Avoids recursion of "MoreComments"
            for comment in post.comments.list():
                # Analyze sentiment of each comment
                sentiment_score = analyzer.polarity_scores(comment.body)
                if sentiment_score['compound'] <= -0.5:  # Threshold for aggressive comments
                    aggressive_comments.append({
                        'post_title': post.title,
                        'comment_body': comment.body,
                        'score': sentiment_score['compound']
                    })
        
        return aggressive_comments
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

# Function to generate a Word document in memory
def generate_word_doc(aggressive_comments):
    # Create a Word Document
    doc = Document()

    # Add a title
    doc.add_heading('Aggressive Comments Report', level=1)

    # Add content for each comment
    for comment in aggressive_comments:
        try:
            # Add post title
            doc.add_heading(f"Post Title: {comment['post_title']}", level=2)

            # Add comment body
            comment_paragraph = doc.add_paragraph()
            comment_paragraph.add_run("Comment: ").bold = True
            comment_paragraph.add_run(comment['comment_body'])

            # Add sentiment score
            score_paragraph = doc.add_paragraph()
            score_paragraph.add_run("Sentiment Score: ").bold = True
            score_paragraph.add_run(str(comment['score']))

            doc.add_paragraph("")  # Add a blank line
        except Exception as e:
            print(f"Error adding content to Word document: {e}")

    # Save the Word document to a memory buffer
    word_output = io.BytesIO()
    doc.save(word_output)
    word_output.seek(0)
    return word_output

# Function to extract username from a Reddit profile URL
def extract_username_from_url(profile_url):
    # Regex to match Reddit profile URLs, e.g., 'https://www.reddit.com/user/username/'
    match = re.search(r'https?://(?:www\.)?reddit\.com/user/([a-zA-Z0-9_]+)', profile_url)
    if match:
        return match.group(1)  # Extract the username part
    else:
        return None

# Streamlit app
def main():
    # Custom CSS for styling
    st.markdown("""
        <style>
            body {
                background-color: #f0f2f6;
            }
            .container {
                width: 80%;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            .title {
                font-size: 40px;
                font-weight: bold;
                color: #4CAF50;
                
            }
            .description {
                font-size: 18px;
                color: #333333;
                
                margin-bottom: 20px;
            }
            .btn-download {
                background-color: #FF5733;
                color: white;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 16px;
                text-align: center;
                display: block;
                margin: 0 auto;
            }
            .btn-download:hover {
                background-color: #FF6F61;
            }
            .input-box {
                background-color: #fff;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }
            .input-box input {
                width: 100%;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
            .input-box input:focus {
                outline: none;
                border-color: #4CAF50;
            }
            .input-box button {
                width: 100%;
                padding: 12px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
            }
            .input-box button:hover {
                background-color: #45a049;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("Reddit Behavior Detection", anchor="title")
    
    # Add a container for the app content
    with st.container():
        st.markdown("<div class='description'>Enter a Reddit username or profile link below to analyze aggressive comments based on sentiment analysis.</div>", unsafe_allow_html=True)

        # Input for username or profile link
        user_input = st.text_input("Reddit Username or Profile Link:", key="input", placeholder="e.g., u/username or https://www.reddit.com/user/username", help="Enter the Reddit username or profile link")

        if st.button("Search", key="search_button"):
            if user_input:
                # Check if the input is a URL or username
                if "reddit.com" in user_input:
                    # It's a profile link; extract the username from the link
                    username = extract_username_from_url(user_input)
                    if not username:
                        st.error("Invalid Reddit profile link. Please provide a valid link.")
                        return
                else:
                    # It's a username
                    username = user_input.strip()

                # Fetch aggressive comments
                with st.spinner('Fetching data...'):
                    aggressive_comments = fetch_aggressive_comments(username)
                
                if aggressive_comments:
                    # Generate Word document
                    word_file = generate_word_doc(aggressive_comments)
                    
                    # Provide download link for the Word document
                    st.download_button(
                        label="Download Report as Word Document",
                        data=word_file,
                        file_name="aggressive_comments_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_button",
                        use_container_width=True,
                    )
                else:
                    st.write("No aggressive comments found.")
            else:
                st.write("Please enter a Reddit username or profile link.")

if __name__ == "__main__":
    main()
