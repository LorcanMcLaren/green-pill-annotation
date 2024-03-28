import streamlit as st
import pandas as pd
import base64
import json

def process_data(uploaded_file, text_column):
    uploaded_file.seek(0)  # Reset file pointer
    df = pd.read_csv(uploaded_file)

    if text_column not in df.columns:
        raise ValueError(f"Selected column '{text_column}' not found in the uploaded file.")

    for section, content in st.session_state.annotation_schema.items():
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

        for section, content in st.session_state.annotation_schema.items():
            st.subheader(section)
            st.write(content["section_instruction"])
            for annotation_option, config in content["annotations"].items():
                full_column_name = f"{section} - {annotation_option}"
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
                if config['example']:
                    with st.expander(f"See examples for {annotation_option}"):
                        st.write(config['example'], unsafe_allow_html=True)

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
    st.write("Instructions: Upload your CSV file containing the texts to be annotated. You can also choose to upload your own annotation schema in JSON format.")
    
    # File uploader for the CSV file
    uploaded_file = st.file_uploader("Choose a text CSV file", type=['csv'], key="csv_uploader")

    # Load default annotation schema
    with open('default_annotation_schema.json', 'r') as file:
            st.session_state.annotation_schema = json.load(file)

    # File uploader for the annotation schema JSON file
    schema_file = st.file_uploader("Optionally, upload your own annotation schema", type=['json'], key="json_uploader")

    # Load default annotation schema if no file is uploaded
    if schema_file is not None:
        st.session_state.annotation_schema = json.load(schema_file)

    # Proceed only if both the CSV and annotation schema (either default or custom) are ready
    if uploaded_file is not None:
        temp_df = pd.read_csv(uploaded_file)
        column_names = temp_df.columns.tolist()

        selected_column = st.selectbox("Select the column to annotate:", column_names, key="text_column_selector")
        st.session_state.text_column = selected_column

        selected_title_column = st.selectbox("Select the column containing the debate title:", column_names, key="title_column_selector")
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
