from flask import Flask, render_template, request
import pickle
import numpy as np
import requests

app = Flask(__name__)

# Load the preprocessed data
popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

# Google Books API key (replace with your own key)
GOOGLE_BOOKS_API_KEY = "YOUR_GOOGLE_BOOKS_API_KEY"

def fetch_book_summary(book_title, author):
    """
    Fetch the summary of a book using the Google Books API.
    """
    query = f"{book_title} by {author}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={GOOGLE_BOOKS_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get("items"):
            # Find the best match
            for item in data["items"]:
                volume_info = item.get("volumeInfo", {})
                if (
                    volume_info.get("title", "").lower() == book_title.lower()
                    and author.lower() in [a.lower() for a in volume_info.get("authors", [])]
                ):
                    return volume_info.get("description", "No summary available.")
    return "No summary found."

@app.route('/')
def index():
    return render_template(
        'index.html',
        book_name=list(popular_df['Book-Title'].values),
        author=list(popular_df['Book-Author'].values),
        image=list(popular_df['Image-URL-M'].values),
        votes=list(popular_df['num_ratings'].values),
        rating=list(popular_df['avg_rating'].values)
    )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['POST'])
def recommend():
    user_input = request.form.get('user_input')
    print(f"User input: {user_input}")

    if user_input in pt.index:
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

        data = []
        for i in similar_items:
            item = []
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

            # Fetch the summary for the book
            summary = fetch_book_summary(item[0], item[1])
            item.append(summary)  # Add the summary to the item

            data.append(item)

        print(data)

        return render_template('recommend.html', data=data)
    else:
        return render_template('recommend.html', error="Book not found in index")

if __name__ == '__main__':
    app.run(debug=True)
