import streamlit as st
import pandas as pd
import base64
import json

# Updated annotation options with types and potential options for Likert scales and dropdowns
annotation_schema = {
    "Checkbox Annotations": {
        "Checkbox Annotation1": {"type": "checkbox", "tooltip": "Tooltip for Annotation1"},
        "Checkbox Annotation2": {"type": "checkbox", "tooltip": "Tooltip for Annotation2"}
    },
    "Likert Scale Annotations": {
        "Likert Annotation1": {"type": "likert", "tooltip": "Tooltip for Likert1", "scale": 5}, 
        "Likert Annotation2": {"type": "likert", "tooltip": "Tooltip for Likert2", "scale": 7}
    },
    "Dropdown Annotations": {
        "Dropdown Annotation1": {"type": "dropdown", "tooltip": "Tooltip for Dropdown1", "options": ["Option1", "Option2", "Option3"]},
        "Dropdown Annotation2": {"type": "dropdown", "tooltip": "Tooltip for Dropdown2", "options": ["OptionA", "OptionB"]}
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
    st.title("Text Annotation")
    index = st.session_state.index - 1  # Adjust index for 1-based indexing
    data = st.session_state.data

    if 'data' not in st.session_state or data is None:
        st.warning("Please upload a CSV file to start annotating.")
        return

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
                # Set a default value for the Likert scale
                default_value = 0  # Assuming 0 is within your scale and represents the default/unset state
                annotated = st.slider(annotation_option, 0, config['scale'], value=int(data.at[index, annotation_option]) if pd.notna(data.at[index, annotation_option]) else default_value, key=f'{index}_{annotation_option}', help=config['tooltip'], format="%d")
                st.session_state.annotations[annotation_option] = annotated
            elif config['type'] == 'dropdown':
                # Adjusted dropdown logic to ensure selected_index is always valid
                options = [""] + config['options']  # Prepend an empty option to represent no selection
                current_value = data.at[index, annotation_option]
                if pd.isna(current_value) or current_value not in options:
                    selected_index = 0  # Default to no selection if current value is NA or not in options
                else:
                    selected_index = options.index(current_value)
                annotated = st.selectbox(annotation_option, options, index=selected_index, key=f'{index}_{annotation_option}', help=config['tooltip'])
                st.session_state.annotations[annotation_option] = annotated if annotated else None

    # Add a separator and a label for clarity
    st.markdown("---")
    st.markdown("### Navigation Controls")

    # Navigation buttons with increased spacing
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        if st.button("Previous") and index > 0:
            st.session_state.prepare_return = False
            update_data(index, data)  # Update the data dataframe before navigating
            update_index(index)

    with col2:
        if st.button("Next") and index < len(data) - 1:
            st.session_state.prepare_return = False
            update_data(index, data)  # Update the data dataframe before navigating
            update_index(index + 2)

    with col3:  # Use the third column for the slider to provide more separation
        new_index = st.slider("Go to Page", 1, len(data), index + 1, format="%d")
        if new_index != index + 1:
            st.session_state.prepare_return = False
            update_data(index, data)  # Update the data dataframe before navigating
            update_index(new_index)

    if st.button("Download Annotated CSV"):
        st.session_state.prepare_return = False
        update_data(index, data)  # Make sure the last viewed text's annotations are saved
        tmp_download_link = download_link(data, 'annotated_data.csv', 'Click here to download your annotated CSV!')
        st.markdown(tmp_download_link, unsafe_allow_html=True)

    # Add a button to initiate the return to landing page process
    if st.button("Annotate New Data"):
        st.session_state.prepare_return = True  # Flag to show the warning and confirmation checkbox

    # If the flag is set, show the warning and confirmation checkbox
    if st.session_state.get('prepare_return', False):
        st.warning("Warning: Annotations that have not been downloaded will not be saved.")
        confirmed = st.checkbox("I understand and wish to proceed.")

        # If confirmed, change the page to landing and reset the prepare_return flag
        if confirmed:
            st.session_state.page = 'landing'
            st.session_state.prepare_return = False  # Reset the flag
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
    landing_page()
elif st.session_state.page == 'annotate':
    annotation_page()
