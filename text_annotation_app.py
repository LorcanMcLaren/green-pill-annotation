import streamlit as st
import pandas as pd
import base64
import json

# Updated annotation schema
annotation_schema = {
    "Discrete Emotions": {
        "section_instruction": "Please evaluate the text for the presence of the following discrete emotions and select as appropriate.",
        "annotations": {
            "Anger": {"type": "checkbox", "tooltip": "Select if the content expresses anger, frustration, or irritation.", "example": "I can't believe they canceled my favorite show! It makes me so mad!"},
            "Fear": {"type": "checkbox", "tooltip": "Select if the content expresses fear, anxiety, or apprehension.", "example": "I'm really scared to walk alone at night in this neighborhood."},
            "Disgust": {"type": "checkbox", "tooltip": "Select if the content expresses disgust, revulsion, or strong disapproval.", "example": "The very idea of eating raw fish disgusts me."},
            "Sadness": {"type": "checkbox", "tooltip": "Select if the content expresses sadness, grief, or sorrow.", "example": "I felt so sad after hearing the news about the accident."},
            "Joy": {"type": "checkbox", "tooltip": "Select if the content expresses joy, happiness, or elation.", "example": "I was overjoyed when I found out I passed the exam!"},
            "Enthusiasm": {"type": "checkbox", "tooltip": "Select if the content expresses enthusiasm, excitement, or eagerness.", "example": "I'm so excited about the upcoming holiday trip!"}
        }
    },
    "Moral Foundations": {
        "section_instruction": "Assess the text for underlying moral foundations and check the relevant boxes.",
        "annotations": {
            "Care/Harm": {"type": "checkbox", "tooltip": "Select if the content relates to care or harm towards others.", "example": "Helping the homeless during winter shows true compassion and care."},
            "Fairness/Cheating": {"type": "checkbox", "tooltip": "Select if the content involves fairness or cheating.", "example": "Cheating in the exam undermines the fairness of the grading system."},
            "Loyalty/Betrayal": {"type": "checkbox", "tooltip": "Select if the content concerns loyalty or betrayal.", "example": "Sticking with your team through thick and thin demonstrates true loyalty."},
            "Authority/Subversion": {"type": "checkbox", "tooltip": "Select if the content involves respect for or defiance against authority.", "example": "Questioning the decisions of those in power can be seen as subversive."},
            "Purity/Degradation": {"type": "checkbox", "tooltip": "Select if the content involves themes of purity or degradation.", "example": "The purity of the environment is tarnished by pollution and waste."}
        }
    },
    "Psychological Distance": {
        "section_instruction": "Evaluate the content's psychological distance in various dimensions and provide your assessment.",
        "annotations": {
            "Spatial Distance": {"type": "likert", "tooltip": "Rate the spatial distance discussed in the content.", "scale": 5, "example": "She moved to another country, far from her hometown."},
            "Temporal Distance": {"type": "dropdown", "tooltip": "Select the temporal distance relevant to the content.", "options": ["Option1", "Option2", "Option3"], "example": "In the future, people might live on Mars."},
            "Social Group Distance": {"type": "dropdown", "tooltip": "Select the social group distance discussed in the content.", "options": ["Option1", "Option2", "Option3"], "example": "They felt like outsiders, unable to relate to the local customs."},
            "Probability": {"type": "likert", "tooltip": "Rate the probability of the event discussed in the content.", "scale": 5, "example": "There's a high chance of rain tomorrow according to the weather forecast."}
        }
    }
}

def process_data(uploaded_file, text_column):
    uploaded_file.seek(0)  # Reset file pointer
    df = pd.read_csv(uploaded_file)

    if text_column not in df.columns:
        raise ValueError(f"Selected column '{text_column}' not found in the uploaded file.")

    for section, content in annotation_schema.items():
        for annotation_option in content["annotations"].keys():
            full_column_name = f"{section} - {annotation_option}"
            if full_column_name not in df.columns:
                df[full_column_name] = None

    return df

def download_link(object_to_download, download_filename, download_link_text):
    if isinstance(object_to_download, pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)
    b64 = base64.b64encode(object_to_download.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{download_filename}">{download_link_text}</a>'

def annotation_page():
    st.title("The Green Pill Project 🧪")

    if 'index' not in st.session_state or 'data' not in st.session_state or st.session_state.data is None:
        st.warning("Please upload a CSV file to start annotating.")
        if st.button("Return to Landing Page"):
            st.session_state.page = 'landing'
            st.session_state.pop('index', None)
            st.session_state.pop('data', None)
            st.rerun()
        return

    index = st.session_state.index - 1
    data = st.session_state.data

    if 'data' not in st.session_state or data is None:
        st.warning("Please upload a CSV file to start annotating.")
        return

    left_column, right_column = st.columns([0.7, 0.3], gap='large')

    with left_column:
        title_column = st.session_state.title_column
        current_title = data.iloc[index][title_column]
        st.markdown(f"### {current_title}")

        current_text = data.iloc[index][st.session_state.text_column]
        st.markdown(f'<div style="height: 300px; overflow-y: scroll; border: 1px solid #ced4da; border-radius: 4px; padding: 10px;">{current_text}</div>', unsafe_allow_html=True)

        if 'annotations' not in st.session_state:
            st.session_state.annotations = {}

        for section, content in annotation_schema.items():
            st.subheader(section)
            st.write(content["section_instruction"])
            for annotation_option, config in content["annotations"].items():
                full_column_name = f"{section} - {annotation_option}"
                if config['example']:
                    with st.expander(f"See examples for {annotation_option}"):
                        st.write(config['example'])
                if config['type'] == 'checkbox':
                    annotated = st.checkbox(annotation_option, value=bool(data.at[index, full_column_name]) if pd.notna(data.at[index, full_column_name]) else False, key=f'{index}_{full_column_name}', help=config['tooltip'])
                    st.session_state.annotations[full_column_name] = 1 if annotated else 0
                elif config['type'] == 'likert':
                    default_value = 0
                    annotated = st.slider(annotation_option, 0, config['scale'], value=int(data.at[index, full_column_name]) if pd.notna(data.at[index, full_column_name]) else default_value, key=f'{index}_{full_column_name}', help=config['tooltip'], format="%d")
                    st.session_state.annotations[full_column_name] = annotated
                elif config['type'] == 'dropdown':
                    options = [""] + config['options']
                    current_value = data.at[index, full_column_name]
                    if pd.isna(current_value) or current_value not in options:
                        selected_index = 0
                    else:
                        selected_index = options.index(current_value)
                    annotated = st.selectbox(annotation_option, options, index=selected_index, key=f'{index}_{full_column_name}', help=config['tooltip'])
                    st.session_state.annotations[full_column_name] = annotated if annotated else None

    with right_column:
        st.markdown("### Navigation Controls")

        if st.button("Next") and index < len(data) - 1:
            st.session_state.prepare_return = False
            update_data(index, data)
            update_index(index + 2)

        if st.button("Previous") and index > 0:
            st.session_state.prepare_return = False
            update_data(index, data)
            update_index(index)

        new_index = st.slider("Go to Item", 1, len(data), index + 1, format="%d")
        if new_index != index + 1:
            st.session_state.prepare_return = False
            update_data(index, data)
            update_index(new_index)

        if st.button("Download Annotated CSV"):
            st.session_state.prepare_return = False
            update_data(index, data)
            tmp_download_link = download_link(data, 'annotated_data.csv', 'Click here to download your annotated CSV')
            st.markdown(tmp_download_link, unsafe_allow_html=True)

        if st.button("Annotate New Data"):
            st.session_state.prepare_return = True

        if st.session_state.get('prepare_return', False):
            st.warning("Warning: Annotations that have not been downloaded will not be saved.")
            confirmed = st.checkbox("I understand and wish to proceed.")

            if confirmed:
                st.session_state.page = 'landing'
                st.session_state.prepare_return = False
                st.rerun()

def landing_page():
    st.title("The Green Pill Project 🧪")
    st.write("Instructions: Upload your CSV file containing the texts to be annotated.")

    uploaded_file = st.file_uploader("Choose a file", type=['csv'])
    if uploaded_file is not None:
        temp_df = pd.read_csv(uploaded_file)
        column_names = temp_df.columns.tolist()

        selected_column = st.selectbox("Select the column to annotate:", column_names)
        st.session_state.text_column = selected_column

        selected_title_column = st.selectbox("Select the column containing the debate title:", column_names)
        st.session_state.title_column = selected_title_column

        st.session_state.data = process_data(uploaded_file, selected_column)
        st.session_state.index = 1

    if st.button("Start Annotating"):
        st.session_state.page = 'annotate'
        st.rerun()

def update_data(index, data):
    for annotation_option in st.session_state.annotations:
        data.at[index, annotation_option] = st.session_state.annotations[annotation_option]

def update_index(new_index):
    st.session_state.index = new_index
    st.rerun()

if 'page' not in st.session_state:
    st.session_state.page = 'landing'

if st.session_state.page == 'landing':
    st.set_page_config(layout="centered")
    landing_page()
elif st.session_state.page == 'annotate':
    st.set_page_config(layout="wide")
    annotation_page()
