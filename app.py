import streamlit as st
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- 1. SETUP & CACHING ---
st.set_page_config(page_title="Review Analyzer", layout="wide")

@st.cache_data
def load_data():
    """Loads and cleans the scraped data."""
    try:
        df = pd.read_csv("reviews.csv")
        
        # Convert date to datetime objects
        df['date'] = pd.to_datetime(df['date'])
        
        # CLEANING: Drop rows with missing text to prevent AI crashes
        df = df.dropna(subset=['text'])
        df['text'] = df['text'].astype(str)
        
        return df
    except FileNotFoundError:
        return None

@st.cache_resource
def load_sentiment_model():
    """Loads the AI model once and caches it."""
    from transformers import pipeline
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Load Data and Model
df = load_data()
if df is None:
    st.error("Error: 'reviews.csv' not found. Please run scraper.py first!")
    st.stop()

try:
    sentiment_pipeline = load_sentiment_model()
except Exception as e:
    st.error(f"Error loading AI Model: {e}")
    st.stop()

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Products", "Testimonials", "Reviews"])

# --- 3. PAGE BEHAVIOR ---

if page == "Products" or page == "Testimonials":
    st.title(f"{page} Data")
    st.write("Displaying raw scraped data:")
    st.dataframe(df)

elif page == "Reviews":
    st.title("Review Sentiment Analysis")
    
    # --- Month Selection ---
    st.subheader("Filter by Month")
    
    month_options = [
        "Jan 2023", "Feb 2023", "Mar 2023", "Apr 2023", "May 2023", "Jun 2023",
        "Jul 2023", "Aug 2023", "Sep 2023", "Oct 2023", "Nov 2023", "Dec 2023"
    ]
    
    selected_month_str = st.select_slider(
        "Select a Month in 2023:",
        options=month_options
    )
    
    # --- Filtering Logic ---
    # Convert "May 2023" -> Datetime object
    selected_date = pd.to_datetime(selected_month_str, format="%b %Y")
    
    # Filter DataFrame by Month and Year
    mask = (df['date'].dt.year == selected_date.year) & (df['date'].dt.month == selected_date.month)
    filtered_df = df[mask].copy()
    
    st.info(f"Analyzing reviews for: **{selected_month_str}**")
    
    if filtered_df.empty:
        st.warning("No reviews found for this specific month.")
    else:
        st.write(f"Found {len(filtered_df)} reviews.")
        st.dataframe(filtered_df)

      # --- AI Analysis Section ---
        st.subheader("AI Sentiment Analysis")
        
        if st.button("Run AI Analysis"):
            with st.spinner("The AI is reading your reviews..."):
                try:
                    # 1. Run the AI Model
                    results = sentiment_pipeline(filtered_df['text'].tolist())
                    
                    # 2. Extract Labels and Scores
                    labels = [r['label'] for r in results]
                    scores = [r['score'] for r in results]
                    
                    # 3. Add to DataFrame
                    filtered_df['sentiment'] = labels
                    filtered_df['confidence'] = scores
                    
                    # 4. Display Classified Data
                    st.success("Analysis Complete!")
                    st.write("### Classified Reviews")
                    st.dataframe(filtered_df[['date', 'text', 'sentiment', 'confidence']])
                    
                    # 5. Advanced Visualization (Altair)
                    st.write("### Sentiment Overview")
                    
                    chart_data = filtered_df.groupby('sentiment').agg({
                        'text': 'count',
                        'confidence': 'mean'
                    }).reset_index()
                    chart_data.columns = ['Sentiment', 'Count', 'Avg Confidence']
                    
                    chart = alt.Chart(chart_data).mark_bar().encode(
                        x='Sentiment',
                        y='Count',
                        color=alt.Color('Sentiment', scale=alt.Scale(domain=['POSITIVE', 'NEGATIVE'], range=['green', 'red'])),
                        tooltip=['Sentiment', 'Count', alt.Tooltip('Avg Confidence', format='.2%')]
                    ).properties(
                        title="Review Counts & AI Confidence"
                    )
                    st.altair_chart(chart, use_container_width=True)
                    
                    # 6. Summary Metrics
                    col1, col2 = st.columns(2)
                    def get_metric(sentiment_label):
                        row = chart_data[chart_data['Sentiment'] == sentiment_label]
                        if not row.empty:
                            return row['Count'].values[0], row['Avg Confidence'].values[0]
                        return 0, 0.0

                    pos_count, pos_conf = get_metric("POSITIVE")
                    neg_count, neg_conf = get_metric("NEGATIVE")
                    col1.metric("Total Positive", pos_count, f"{pos_conf:.1%} Confidence")
                    col2.metric("Total Negative", neg_count, f"{neg_conf:.1%} Confidence")

                    # --- 7. BONUS: WORD CLOUD ---
                    st.write("### ☁️ Word Cloud")
                    st.write("What words appear most frequently in these reviews?")
                    
                    # Combine all review text into one big string
                    text = " ".join(review for review in filtered_df.text)
                    
                    # Generate the cloud
                    # We use a white background to make it look clean
                    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
                    
                    # Display using Matplotlib
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis("off") # Turn off the X and Y axis numbers
                    st.pyplot(fig)
                    
                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")
