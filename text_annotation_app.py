import streamlit as st
import pandas as pd
import base64

# Define annotation options and their tooltips once at the top level
annotation_options = {
    'Basic Annotations': {
        'Annotation1': 'Tooltip for Annotation1',
        'Annotation2': 'Tooltip for Annotation2',
        'Annotation3': 'Tooltip for Annotation3'
    },
    'Subsection1': {
        'Annotation4': 'Tooltip for Annotation4',
        'Annotation5': 'Tooltip for Annotation5'
    },
    'Subsection2': {
        'Annotation6': 'Tooltip for Annotation6',
        'Annotation7': 'Tooltip for Annotation7'
    }
}

def process_data(uploaded_file):
    """Processes uploaded CSV file, adding missing annotation columns."""
    df = pd.read_csv(uploaded_file)

    for subsection, annotations in annotation_options.items():
        for annotation_option in annotations.keys():
            if annotation_option not in df.columns:
                df[annotation_option] = 0
    return df

def download_link(object_to_download, download_filename, download_link_text):
    """Generates a downloadable link for a provided object."""
    if isinstance(object_to_download, pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)
    b64 = base64.b64encode(object_to_download.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{download_filename}">{download_link_text}</a>'

def annotation_page():
    """Displays annotation interface and handles navigation."""
    st.title("Text Annotation")
    # Adjust index for 1-based indexing
    index = st.session_state.index - 1
    data = st.session_state.data

    if 'data' not in st.session_state or data is None:
        st.warning("Please upload a CSV file to start annotating.")
        return

    # Custom CSS to create a scrollable text block
    st.markdown(
        """
        <style>
        .scrollable-container {
            height: 200px;  /* Adjust height as needed */
            overflow-y: scroll;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    current_text = data.iloc[index]['translated']
    
    # Scrollable container for displaying text
    st.markdown(f'<div class="scrollable-container">{current_text}</div>', unsafe_allow_html=True)

    # Initialize or update a dictionary in session_state to hold annotation states
    if 'annotations' not in st.session_state:
        st.session_state.annotations = {}
    for i in range(len(data)):
        if i not in st.session_state.annotations:
            st.session_state.annotations[i] = {}
            for subsection, annotations in annotation_options.items():
                for annotation_option, tooltip_text in annotations.items():
                    # Initialize with values from the dataframe, default to False if missing
                    st.session_state.annotations[i][annotation_option] = bool(data.at[i, annotation_option]) if annotation_option in data.columns else False

    for subsection, annotations in annotation_options.items():
        st.subheader(subsection)  # Display subsection header
        for annotation_option, tooltip_text in annotations.items():
            # Use the stored value in session_state if available
            annotated = st.checkbox(annotation_option, value=st.session_state.annotations[index][annotation_option], key=f'{index}_{annotation_option}', help=tooltip_text)
            st.session_state.annotations[index][annotation_option] = annotated  # Update the session_state with the current checkbox state

            # Update the dataframe to reflect the current annotations
            data.at[index, annotation_option] = 1 if annotated else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Previous") and index > 0:
            update_index(index)

    with col2:
        if st.button("Next") and index < len(data) - 1:
            update_index(index + 2)  # Increment by 2 to account for 1-based indexing

    # Adjust slider range and display for 1-based indexing
    new_index = st.slider("Go to", 1, len(data), index + 1)
    if new_index != index + 1:
        update_index(new_index)

    if st.button("Download Annotated CSV"):
        tmp_download_link = download_link(data, 'annotated_data.csv', 'Click here to download your annotated CSV!')
        st.markdown(tmp_download_link, unsafe_allow_html=True)

def landing_page():
    """Displays instructions and upload functionality."""
    st.title("Text Annotation Tool")
    st.write("Instructions: Upload your CSV file containing the texts to be annotated.")

    uploaded_file = st.file_uploader("Choose a file", type=['csv'])
    if uploaded_file is not None:
        st.session_state.data = process_data(uploaded_file)
        st.session_state.index = 1  # Start indexing from 1

    if st.button("Start Annotating"):
        st.session_state.page = 'annotate'
        st.rerun()  # Force re-render

def update_index(new_index):
    """Updates the index and triggers a re-render."""
    st.session_state.index = new_index
    st.rerun()

if 'page' not in st.session_state:
    st.session_state.page = 'landing'

if st.session_state.page == 'landing':
    landing_page()
elif st.session_state.page == 'annotate':
    annotation_page()
