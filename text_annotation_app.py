import streamlit as st
import pandas as pd
import base64
import json

# Updated annotation options with types and potential options for Likert scales and dropdowns
annotation_schema = {
    "Discrete Emotions": {
        "Anger": {"type": "checkbox", "tooltip": "Updated annotation options with types and potential options for Likert scales and dropdowns. Updated annotation options with types and potential options for Likert scales and dropdowns. Updated annotation options with types and potential options for Likert scales and dropdowns."},
        "Fear": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Disgust": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Sadness": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Joy": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Enthusiasm": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"}
    },
    "Moral Foundations": {
        "Care/Harm": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Fairness/Cheating": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Loyalty/Betrayal": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Authority/Subversion": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Purity/Degradation": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"}
    },
    "Psychological Distance": {
        "Spatial Distance": {"type": "likert", "tooltip": "Tooltip for Likert1", "scale": 5},
        "Temporal Distance": {"type": "dropdown", "tooltip": "Tooltip for Dropdown1", "options": ["Option1", "Option2", "Option3"]},
        "Social Group Distance": {"type": "dropdown", "tooltip": "Tooltip for Dropdown1", "options": ["Option1", "Option2", "Option3"]},
        "Probability": {"type": "likert", "tooltip": "Tooltip for Likert1", "scale": 5}
    }
}

def process_data(uploaded_file, text_column):
    """Processes uploaded CSV file, adding missing annotation columns and setting the text column for annotation."""
    uploaded_file.seek(0)  # Reset file pointer
    df = pd.read_csv(uploaded_file)

    # Ensure the selected text column exists in the DataFrame
    if text_column not in df.columns:
        raise ValueError(f"Selected column '{text_column}' not found in the uploaded file.")

    for subsection, annotations in annotation_schema.items():
        for annotation_option in annotations.keys():
            if annotation_option not in df.columns:
                df[annotation_option] = None  # Use None to accommodate different types of data

    return df


def download_link(object_to_download, download_filename, download_link_text):
    """Generates a downloadable link for a provided object."""
    if isinstance(object_to_download, pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)
    b64 = base64.b64encode(object_to_download.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{download_filename}">{download_link_text}</a>'


def annotation_page():
    """Displays annotation interface and handles navigation."""
    st.title("The Green Pill Project 🧪")

    # Check if 'index' and 'data' are initialized in session state
    if 'index' not in st.session_state or 'data' not in st.session_state or st.session_state.data is None:
        st.warning("Please upload a CSV file to start annotating.")
        if st.button("Return to Landing Page"):
            st.session_state.page = 'landing'  # Change the page state
            st.session_state.pop('index', None)  # Optionally clear 'index' from session state
            st.session_state.pop('data', None)  # Optionally clear 'data' from session state
            st.rerun()  # Rerun the app to reflect the change
        return  # Exit the function to prevent further execution

    # Now it's safe to access 'index' and 'data'
    index = st.session_state.index - 1  # Adjust index for 1-based indexing
    data = st.session_state.data

    if 'data' not in st.session_state or data is None:
        st.warning("Please upload a CSV file to start annotating.")
        return

    # Create two columns for layout, with the left column being wider
    left_column, right_column = st.columns([0.7, 0.3], gap='large')

    with left_column:
        # Display the selected title above the current text
        title_column = st.session_state.title_column  # Retrieve the user-selected column for the title
        current_title = data.iloc[index][title_column]  # Get the current title from the data
        st.markdown(f"## {current_title}")  # Display the title as a header

        # Display the current text in a scrollable container
        current_text = data.iloc[index][st.session_state.text_column]
        st.markdown(f'<div style="height: 200px; overflow-y: scroll; border: 1px solid #ced4da; border-radius: 4px; padding: 10px;">{current_text}</div>', unsafe_allow_html=True)

        # Initialize or update annotation states for the current index
        if 'annotations' not in st.session_state:
            st.session_state.annotations = {}

        for subsection, annotations in annotation_schema.items():
            st.subheader(subsection)
            for annotation_option, config in annotations.items():
                if config['type'] == 'checkbox':
                    annotated = st.checkbox(annotation_option, value=bool(data.at[index, annotation_option]) if pd.notna(data.at[index, annotation_option]) else False, key=f'{index}_{annotation_option}', help=config['tooltip'])
                    st.session_state.annotations[annotation_option] = 1 if annotated else 0
                elif config['type'] == 'likert':
                    default_value = 0  # Assuming 0 is within your scale and represents the default/unset state
                    annotated = st.slider(annotation_option, 0, config['scale'], value=int(data.at[index, annotation_option]) if pd.notna(data.at[index, annotation_option]) else default_value, key=f'{index}_{annotation_option}', help=config['tooltip'], format="%d")
                    st.session_state.annotations[annotation_option] = annotated
                elif config['type'] == 'dropdown':
                    options = [""] + config['options']  # Prepend an empty option to represent no selection
                    current_value = data.at[index, annotation_option]
                    if pd.isna(current_value) or current_value not in options:
                        selected_index = 0
                    else:
                        selected_index = options.index(current_value)
                    annotated = st.selectbox(annotation_option, options, index=selected_index, key=f'{index}_{annotation_option}', help=config['tooltip'])
                    st.session_state.annotations[annotation_option] = annotated if annotated else None

    # Navigation controls and download button are now placed in a narrower right column
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
    """Displays instructions and upload functionality."""
    st.title("The Green Pill Project 🧪")
    st.write("Instructions: Upload your CSV file containing the texts to be annotated.")

    uploaded_file = st.file_uploader("Choose a file", type=['csv'])
    if uploaded_file is not None:
        # Temporarily load the file to get the column names
        temp_df = pd.read_csv(uploaded_file)
        column_names = temp_df.columns.tolist()
        
        # Allow the user to select the text column
        selected_column = st.selectbox("Select the column to annotate:", column_names)
        st.session_state.text_column = selected_column  # Store the selected column name in the session state

        selected_title_column = st.selectbox("Select the column containing the debate title:", column_names)
        st.session_state.title_column = selected_title_column  # Store the selected title column in session state

        # Reload the file and process the data using the selected column for text
        st.session_state.data = process_data(uploaded_file, selected_column)
        st.session_state.index = 1

    if st.button("Start Annotating"):
        st.session_state.page = 'annotate'
        st.rerun()


def update_data(index, data):
    """Updates the data dataframe with annotations from the current text."""
    for annotation_option in st.session_state.annotations:
        data.at[index, annotation_option] = st.session_state.annotations[annotation_option]


def update_index(new_index):
    """Updates the index and triggers a re-render."""
    st.session_state.index = new_index
    st.rerun()


if 'page' not in st.session_state:
    st.session_state.page = 'landing'

if st.session_state.page == 'landing':
    st.set_page_config(layout="centered")
    landing_page()
elif st.session_state.page == 'annotate':
    # Set the page to wide mode
    st.set_page_config(layout="wide")
    annotation_page()
