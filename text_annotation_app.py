import streamlit as st
import pandas as pd
import base64
import json

def render_header():
    header = """
        <style>
        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: black;
            padding: 30px 0 0 20px;
            text-align: left;
            z-index: 1000;
        }
        .content {
            margin-top: 60px;
        }
        </style>

        <div class="header">
            <h2>The Green Pill Project 🧪</h2>
        </div>
    """
    st.markdown(header, unsafe_allow_html=True)

def process_data(uploaded_file, text_column):
    uploaded_file.seek(0)  # Reset file pointer
    df = pd.read_csv(uploaded_file)

    if text_column not in df.columns:
        raise ValueError(f"Selected column '{text_column}' not found in the uploaded file.")

    for section_key, section_content in st.session_state.custom_schema.items():
        if "section" in section_key:
            for _, annotation_content in section_content["annotations"].items():
                full_column_name = f"{section_content['section_name']}_{annotation_content['name']}"
                if full_column_name not in df.columns:
                    df[full_column_name] = None

    return df


def annotation_page():
    render_header()

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
        title_column = st.session_state.custom_schema["header_column"]
        text_column = st.session_state.custom_schema["text_column"]
        current_title = data.iloc[index][title_column]
        st.markdown(f"### {current_title}")

        current_text = data.iloc[index][text_column]
        st.markdown(f'<div style="height: 300px; overflow-y: scroll; border: 1px solid #ced4da; border-radius: 4px; padding: 10px;">{current_text}</div>', unsafe_allow_html=True)

        if 'annotations' not in st.session_state:
            st.session_state.annotations = {}

        for key, content in st.session_state.custom_schema.items():
            if "section" in key:
                st.subheader(content['section_name'])
                st.write(content["section_instruction"])
                for _, config in content["annotations"].items():
                    full_column_name = f"{content['section_name']}_{config['name']}"
                    if config['type'] == 'checkbox':
                        annotated = st.checkbox(config['name'], value=bool(data.at[index, full_column_name]) if pd.notna(data.at[index, full_column_name]) else False, key=f'{index}_{full_column_name}', help=config['tooltip'])
                        st.session_state.annotations[full_column_name] = 1 if annotated else 0
                    elif config['type'] == 'likert':
                        default_value = 0
                        min_value = config.get('min_value', 0)
                        max_value = config.get('max_value', config['scale'])
                        annotated = st.slider(config['name'], min_value, max_value, value=int(data.at[index, full_column_name]) if pd.notna(data.at[index, full_column_name]) else default_value, key=f'{index}_{full_column_name}', help=config['tooltip'], format="%d")
                        st.session_state.annotations[full_column_name] = annotated
                    elif config['type'] == 'dropdown':
                        options = [""] + config['options']
                        current_value = data.at[index, full_column_name]
                        if pd.isna(current_value) or current_value not in options:
                            selected_index = 0
                        else:
                            selected_index = options.index(current_value)
                        annotated = st.selectbox(config['name'], options, index=selected_index, key=f'{index}_{full_column_name}', help=config['tooltip'])
                        st.session_state.annotations[full_column_name] = annotated if annotated else None
                    elif config['type'] == 'textbox':
                        default_text = '' if pd.isna(data.at[index, full_column_name]) else data.at[index, full_column_name]
                        annotated = st.text_input(config['name'], value=default_text, key=f'{index}_{full_column_name}', help=config['tooltip'])
                        st.session_state.annotations[full_column_name] = annotated
                    if config['example']:
                        with st.expander(f"See examples for {config['name']}"):
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

        if st.session_state.data is not None:
            csv_data = st.session_state.data.copy()  # Create a copy to update only when needed
            update_data(index, csv_data)  # Update the data copy
            csv = csv_data.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Annotated CSV", data=csv, file_name='annotated_data.csv', mime='text/csv')


        if st.button("Annotate New Data"):
            st.session_state.prepare_return = True

        if st.session_state.get('prepare_return', False):
            st.warning("Warning: Annotations that have not been downloaded will not be saved.")
            confirmed = st.checkbox("I understand and wish to proceed.")

            if confirmed:
                st.session_state.data = None
                st.session_state.custom_schema = {}
                st.session_state.page = 'landing'
                st.session_state.prepare_return = False
                st.rerun()

def landing_page():
    render_header()
    st.header("Instructions")
    st.write("""Upload your CSV file containing the texts to be annotated.""")
    
    # File uploader for the CSV file
    uploaded_file = st.file_uploader("Choose a text CSV file", type=['csv'], key="csv_uploader")

    # Check if a CSV file has been uploaded and if an annotation schema is present
    if uploaded_file is not None:
        temp_df = pd.read_csv(uploaded_file)
        st.session_state.column_names = temp_df.columns.tolist()

        st.session_state.uploaded_file = uploaded_file
        st.session_state.index = 1

        # File uploader for the annotation schema JSON file
        schema_file = st.file_uploader("Optionally, upload your own annotation schema", type=['json'], key="json_uploader")

        # Load the uploaded annotation schema
        if schema_file is not None:
            st.session_state.custom_schema = json.load(schema_file)

        # Load default annotation schema if available and no custom schema has been uploaded yet
        if 'custom_schema' not in st.session_state:
            st.session_state.custom_schema = {}  # Use an empty schema if default is not found

        if st.button("Start Annotating"):
            # Check if the annotation schema is empty before proceeding to annotation
            if st.session_state.custom_schema:
                st.session_state.data = process_data(st.session_state.uploaded_file, st.session_state.custom_schema["text_column"])
                st.session_state.page = 'annotate'
            else:
                # Redirect to schema creation page if no schema is present
                st.session_state.page = 'create_schema'
            st.rerun()

def schema_creation_page():
    render_header()
    st.header("Create Your Annotation Schema")
    st.subheader("Instructions")
    st.write("This is where the instructions will go.")
    st.divider()

    header_column = st.selectbox("Select the header column:", st.session_state.column_names, key="header_column_selector")
    text_column = st.selectbox("Select the text column to annotate:", st.session_state.column_names, key="text_column_selector")
    
    # Initialize or update the session state for schema creation
    if not st.session_state.custom_schema:
        # Add these lines at an appropriate place in schema_creation_page()
        st.session_state.custom_schema = {
            "header_column": header_column,
            "text_column": text_column,
            "section_1": {"section_name": "", "section_instruction": "", "annotations": {}}}
    
    if 'annotations_count' not in st.session_state:
        st.session_state.annotations_count = {"section_1": 0}

    # Store the selected columns in custom_schema
    if st.session_state.custom_schema:
        st.session_state.custom_schema["header_column"] = header_column
        st.session_state.custom_schema["text_column"] = text_column

    # Function to add a new section
    def add_section():
        new_section_key = f"section_{len(st.session_state.custom_schema) - 1}"
        st.session_state.custom_schema[new_section_key] = {"section_name": "", "section_instruction": "", "annotations": {}}
        st.session_state.annotations_count[new_section_key] = 0  # Initialize with 0 annotations
        st.rerun()

    # Function to add a new annotation within a section
    def add_annotation(section_key):
        st.session_state.annotations_count[section_key] += 1
        st.rerun()

    def render_annotation(annotation, key):
        label = annotation['name'] if annotation['name'] else ""
        if annotation['type'] == 'checkbox':
            st.checkbox(label, help=annotation['tooltip'], key=key)
        elif annotation['type'] == 'likert':
            default_value = 0
            min_value = annotation.get('min_value', 0)
            max_value = annotation.get('max_value', annotation['scale'])
            st.slider(label, min_value, max_value, value=default_value, help=annotation['tooltip'], format="%d", key=key)
        elif annotation['type'] == 'dropdown':
            options = [""] + annotation['options']
            st.selectbox(label, options, index=0, help=annotation['tooltip'], key=key)
        elif annotation['type'] == 'textbox':
            st.text_input(label, help=annotation['tooltip'], key=key)
        if annotation['example']:
            with st.expander(f"See examples for {annotation['name']}"):
                st.write(annotation['example'], unsafe_allow_html=True)

    # Iterate through sections to display them
    for section_key in st.session_state.custom_schema.keys():
        if "section" in section_key:
            section = st.session_state.custom_schema[section_key]
            section_title = "Section " + section_key.split('section_')[1]
            with st.container():
                st.subheader(section_title)
                # Update section name and instructions directly in custom_schema
                section["section_name"] = st.text_input("Section Name", key=f"{section_key}_name", value=section.get("section_name", ""))
                section["section_instruction"] = st.text_area("Section Instructions", key=f"{section_key}_instructions", value=section.get("section_instruction", ""))

                # Iterate through annotations for this section based on the count
                for ann_idx in range(st.session_state.annotations_count[section_key]):
                    ann_key = f"annotation_{ann_idx + 1}"  # Start annotation naming from 1 for readability
                    with st.popover(f"Configure annotation {ann_idx + 1}"):
                        # Initialize annotation in the schema if it doesn't exist
                        if ann_key not in section["annotations"]:
                            section["annotations"][ann_key] = {"name": "", "type": "checkbox", "tooltip": "", "example": ""}

                        # Update annotation details directly in custom_schema
                        annotation = section["annotations"][ann_key]
                        annotation["name"] = st.text_input("Annotation Name", key=f"{section_key}_{ann_key}_name", value=annotation.get("name", ""))
                        annotation["type"] = st.selectbox("Annotation Type", ["checkbox", "likert", "dropdown", "textbox"], key=f"{section_key}_{ann_key}_type", index=["checkbox", "likert", "dropdown", "textbox"].index(annotation.get("type", "checkbox")))
                        annotation["tooltip"] = st.text_area("Tooltip", key=f"{section_key}_{ann_key}_tooltip", value=annotation.get("tooltip", ""))
                        annotation["example"] = st.text_area("Example", key=f"{section_key}_{ann_key}_example", value=annotation.get("example", ""))

                        if annotation["type"] == "likert":
                            annotation["min_value"] = st.number_input("Minimum Value", value=0, key=f"{section_key}_{ann_key}_min_value")
                            annotation["max_value"] = st.number_input("Maximum Value", value=5, key=f"{section_key}_{ann_key}_max_value")
                            annotation["scale"] = annotation["max_value"]
                        elif annotation["type"] == "dropdown":
                            options_str = st.text_area("Options (comma-separated)", key=f"{section_key}_{ann_key}_options")
                            annotation["options"] = [option.strip() for option in options_str.split(',') if option.strip()]
                    
                    st.caption(f"Rendering of annotation {ann_idx + 1}")
                    render_annotation(annotation, key = f"{section_key}_{ann_key}_render")

                # Button to add a new annotation within this section
                if st.button("Add Annotation", key=f"add_annotation_{section_key}"):
                    add_annotation(section_key)
                st.divider()

    # Button to add a new section, placed at the end outside of the sections' loop
    if st.button("Add New Section"):
        add_section()

    st.divider()
    # Display the current schema for debugging purposes
    st.write("Current Schema:")
    st.json(st.session_state.custom_schema)

    # Option to download the current schema as JSON
    schema_str = json.dumps(st.session_state.custom_schema, indent=4)
    st.download_button(label="Download Schema as JSON", data=schema_str, file_name='custom_annotation_schema.json', mime='application/json')


    # Option to use the current schema for annotation
    if st.button("Use This Schema for Annotation"):
        st.session_state.data = process_data(st.session_state.uploaded_file, text_column)
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

page_title = "Green Pill"
page_icon = "🧪"

if st.session_state.page == 'landing':
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="centered")
    landing_page()
elif st.session_state.page == 'annotate':
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")
    annotation_page()
elif st.session_state.page == 'create_schema':
    st.set_page_config(page_title=page_title, page_icon=page_icon,layout="centered")
    schema_creation_page()


# Add a footer
footer = """<style>
a:link , a:visited{
color: grey;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: grey;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
# background-color: white;
color: grey;
text-align: right;
padding-right: 100px;
}
</style>
<div class="footer">
<p>Developed by <a href="https://www.lorcanmclaren.com" target="_blank">Lorcan McLaren</a></p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
