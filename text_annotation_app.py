import streamlit as st
import pandas as pd

# Initialize session state for navigation and annotations
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'annotations' not in st.session_state:
    st.session_state.annotations = {}
if 'page' not in st.session_state:
    st.session_state.page = 'landing'

# Function to display the landing page
def show_landing_page():
    st.title("Welcome to the Annotation App")
    st.header("Instructions")
    st.write("""
        - Read the text displayed on the screen.
        - Select the appropriate annotation based on the guidelines provided below.
        - Use the 'Next' and 'Previous' buttons to navigate through texts.
        - Your progress will be automatically saved.
        - Click 'Start Annotating' when you're ready to begin.
    """)

    if st.button('Start Annotating'):
        st.session_state.page = 'annotate'

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('data/sample.csv')  # Update the path to your data file
data = load_data()

# Annotation options with explanations
annotation_options = {
    'Option 1': 'Explanation for Option 1...',
    'Option 2': 'Explanation for Option 2...',
    'Option 3': 'Explanation for Option 3...'
}

# Main app logic
if st.session_state.page == 'landing':
    show_landing_page()
else:
    # Display the current text and agenda item
    current_text = data.iloc[st.session_state.current_index]['translated']
    current_agenda_item = data.iloc[st.session_state.current_index]['agenda_item']
    st.write("# Green Pill Project")
    st.write(f"### {current_agenda_item}")
    st.write(f"##### Intervention {st.session_state.current_index + 1} out of {len(data)}")
    st.write(current_text)

    # Local CSS for tooltips
    st.markdown("""
    <style>
    .tooltip {
      position: relative;
      display: inline-block;
      cursor: pointer;
    }

    .tooltip .tooltiptext {
      visibility: hidden;
      width: 200px;
      background-color: black;
      color: #fff;
      text-align: center;
      border-radius: 6px;
      padding: 5px 0;
      position: absolute;
      z-index: 1;
      bottom: 100%;
      left: 50%;
      margin-left: -100px;
      opacity: 0;
      transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
      visibility: visible;
      opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display the annotation options with tooltips
    for option, explanation in annotation_options.items():
        col1, col2 = st.columns([0.9, 0.1], gap="small")
        with col1:
            # Determine the initial state of the checkbox based on stored annotations
            initial_state = st.session_state.annotations.get(st.session_state.current_index, {}).get(option, False)
            # Update checkbox state based on user interaction or initial state
            checkbox_state = st.checkbox(option, value=initial_state, key=f"checkbox_{st.session_state.current_index}_{option}")
            # Store the checkbox state in session state annotations
            if checkbox_state:
                if st.session_state.current_index not in st.session_state.annotations:
                    st.session_state.annotations[st.session_state.current_index] = {}
                st.session_state.annotations[st.session_state.current_index][option] = checkbox_state
            elif option in st.session_state.annotations.get(st.session_state.current_index, {}):
                # Uncheck and remove from annotations if previously checked but now unchecked
                del st.session_state.annotations[st.session_state.current_index][option]
        with col2:
            # Tooltip icon next to each option
            st.markdown(f"""<div class="tooltip">?
                            <span class="tooltiptext">{explanation}</span>
                            </div>""", unsafe_allow_html=True)

    # Navigation buttons with explicit action tracking
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Previous'):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1

    with col2:
        if st.button('Next'):
            if st.session_state.current_index < len(data) - 1:
                st.session_state.current_index += 1
                # Only reset annotations for unseen next text
                if st.session_state.current_index not in st.session_state.annotations:
                    for option in annotation_options.keys():
                        st.session_state[option] = False

    # Save button
    if st.button('Save Annotations'):
        # Iterate through all annotated texts to update the DataFrame
        for index, annotations in st.session_state.annotations.items():
            for option, value in annotations.items():
                # Update the DataFrame with the selected annotation
                if value:  # Ensure the checkbox was checked
                    data.at[index, 'Annotation'] = option
        data.to_csv('data/annotated_data.csv', index=False)
        st.success('Annotations saved!')
