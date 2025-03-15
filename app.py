import json
import streamlit as st
from streamlit_echarts import st_echarts
from millify import millify
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from transform import parse_video, youtube_metrics
import re

# Page Configurations
st.set_page_config(page_title="YouTube Analytics Dashboard", layout="wide")

# Custom Styling
st.markdown(
    """
    <style>
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            border-radius: 10px;
            font-size: 16px;
            padding: 8px 16px;
        }
        .stTextInput>div>div>input {
            font-size: 18px;
        }
    </style>
    """, unsafe_allow_html=True
)

# Title Section
st.title('📊 YouTube Analytics Dashboard')
st.markdown("---")

# Input Section
col_input, col_example = st.columns([0.8, 0.2])
VIDEO_URL = col_input.text_input('Enter YouTube Video URL:', placeholder="Paste a YouTube video link here...")

if col_example.button('Use Example 🎥'):
    VIDEO_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

# Function to convert shortened URLs
def convert_youtube_url(url):
    short_pattern = r"https://youtu\.be/([a-zA-Z0-9_-]+)"
    match = re.match(short_pattern, url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

# Convert and process the URL
try:
    VIDEO_URL = convert_youtube_url(VIDEO_URL)
    if VIDEO_URL:
        with st.spinner('Analyzing video data... ⏳'):
            df = parse_video(VIDEO_URL)
            df_metrics = youtube_metrics(VIDEO_URL)

            # Metrics Display
            st.markdown("### 📈 Video Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Views", millify(df_metrics[0], precision=2))
            col2.metric("Likes", millify(df_metrics[1], precision=2))
            col3.metric("Comments", millify(df_metrics[2], precision=2))
            
            # Display Video
            st.video(VIDEO_URL)
            st.markdown("---")

            # Top Comments Section
            st.subheader("💬 Most Liked Comments")
            df_top = df[['Author', 'Comment', 'Timestamp', 'Likes']].sort_values('Likes', ascending=False).reset_index(drop=True)
            gd1 = GridOptionsBuilder.from_dataframe(df_top.head(10))
            gridoptions1 = gd1.build()
            AgGrid(df_top.head(10), gridOptions=gridoptions1, theme='streamlit')
            
            # Language Distribution
            st.subheader("🌍 Comment Language Distribution")
            df_langs = df['Language'].value_counts().rename_axis('Language').reset_index(name='count')
            options2 = {
                "tooltip": {"trigger": 'axis'},
                "yAxis": {"type": "category", "data": df_langs['Language'].tolist()},
                "xAxis": {"type": "value"},
                "series": [{"data": df_langs['count'].tolist(), "type": "bar", "color": "#ff4b4b"}],
            }
            st_echarts(options=options2, height="400px")
            
            # Most Replied Comments
            st.subheader("💬 Most Replied Comments")
            df_replies = df[['Author', 'Comment', 'Timestamp', 'TotalReplies']].sort_values('TotalReplies', ascending=False).reset_index(drop=True)
            gd2 = GridOptionsBuilder.from_dataframe(df_replies.head(10))
            gridoptions2 = gd2.build()
            AgGrid(df_replies.head(10), gridOptions=gridoptions2, theme='streamlit')
            
            # Sentiments of the Commentors
            st.subheader("Reviews") 
            sentiments = df[df['Language'] == 'English']
            data_sentiments = sentiments['TextBlob_Sentiment_Type'].value_counts(
            ).rename_axis('Sentiment').reset_index(name='counts')

            data_sentiments['Review_percent'] = (
                100. * data_sentiments['counts'] / data_sentiments['counts'].sum()).round(1)

            result = data_sentiments.to_json(orient="split")
            parsed = json.loads(result)

            options = {
                "tooltip": {"trigger": "item",
                            "formatter": '{d}%'},
                "legend": {"top": "5%", "left": "center"},
                "series": [
                    {
                        "name": "Sentiment",
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "avoidLabelOverlap": False,
                        "itemStyle": {
                            "borderRadius": 10,
                            "borderColor": "#fff",
                            "borderWidth": 2,
                        },
                        "label": {"show": False, "position": "center"},
                        "emphasis": {
                            "label": {"show": True, "fontSize": "30", "fontWeight": "bold"}
                        },
                        "labelLine": {"show": False},
                        "data": [
                            {"value": parsed['data'][1][2], "name": parsed['data'][1][0], "itemStyle": {"color": "#008000"}},  # Positive (Green)
                            {"value": parsed['data'][0][2], "name": parsed['data'][0][0], "itemStyle": {"color": "#808080"}},  # Neutral (Gray)
                            {"value": parsed['data'][2][2], "name": parsed['data'][2][0], "itemStyle": {"color": "#FF0000"}}   # Negative (Red)
                        ],
                    }
                ],
            }
            st_echarts(
                options=options, height="500px",
            )

except:
    st.error(
        ' The URL Should be of the form: https://www.youtube.com/watch?v=videoID', icon="🚨")