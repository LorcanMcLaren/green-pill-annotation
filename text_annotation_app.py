import streamlit as st
import pandas as pd
import base64
import json

# Updated annotation schema
annotation_schema = {
    "Discrete Emotions": {
        "section_instruction": "Please evaluate the text for the presence of the following discrete emotions and select as appropriate.",
        "annotations": {
            "Anger": {
                "type": "checkbox",
                "tooltip": "Select if the content expresses anger, frustration, or irritation.",
                "example": "Pro: 'It's outrageous that we've ignored climate scientists for so long!' <br> Anti: 'The anger towards economic progress in the name of climate change is misguided!'"
            },
            "Fear": {
                "type": "checkbox",
                "tooltip": "Select if the content expresses fear, anxiety, or apprehension.",
                "example": "Pro: 'The prospect of irreversible climate change is terrifying.' <br> Anti: 'Fear-mongering about climate change stifles economic innovation.'"
            },
            "Disgust": {
                "type": "checkbox",
                "tooltip": "Select if the content expresses disgust, revulsion, or strong disapproval.",
                "example": "Pro: 'The pollution in our oceans is a disgrace to humanity.' <br> Anti: 'The disdain for industrial progress by environmentalists is counterproductive.'"
            },
            "Sadness": {
                "type": "checkbox",
                "tooltip": "Select if the content expresses sadness, grief, or sorrow.",
                "example": "Pro: 'The destruction of natural habitats fills me with deep sorrow.' <br> Anti: 'It's sad to see jobs lost due to unrealistic environmental regulations.'"
            },
            "Joy": {
                "type": "checkbox",
                "tooltip": "Select if the content expresses joy, happiness, or elation.",
                "example": "Pro: 'The transition to renewable energy sources brings me great hope.' <br> Anti: 'The joy of economic growth and prosperity should not be overshadowed by climate alarmism.'"
            },
            "Enthusiasm": {
                "type": "checkbox",
                "tooltip": "Select if the content expresses enthusiasm, excitement, or eagerness.",
                "example": "Pro: 'I'm eager to see the advancements in green technology.' <br> Anti: 'We should be excited about the opportunities that come with exploring all forms of energy.'"
            }
        }
    },
    "Moral Foundations": {
        "section_instruction": "Assess the text for underlying moral foundations and check the relevant boxes.",
        "annotations": {
            "Care/Harm": {
                "type": "checkbox",
                "tooltip": "Select if the content relates to care or harm towards others.",
                "example": "Care Pro: 'Adopting sustainable practices showcases our care for the planet and future generations.' <br> Care Anti: 'Overemphasizing environmental protection can neglect immediate human needs and economic development.' <br> Harm Pro: 'Ignoring climate change inflicts harm on the most vulnerable populations globally.' <br> Harm Anti: 'Exaggerating climate risks can harm economies, leading to job losses and social instability.'"
            },
            "Fairness/Cheating": {
                "type": "checkbox",
                "tooltip": "Select if the content involves fairness or cheating.",
                "example": "Fairness Pro: 'Equitable climate policies ensure that all nations contribute their fair share to global efforts.' <br> Fairness Anti: 'Imposing strict environmental standards on developing countries isn't fair to their economic growth.' <br> Cheating Pro: 'Companies that bypass environmental regulations are cheating the system and must be held accountable.' <br> Cheating Anti: 'Accusations of environmental cheating often ignore the economic realities and constraints businesses face.'"
            },
            "Loyalty/Betrayal": {
                "type": "checkbox",
                "tooltip": "Select if the content concerns loyalty or betrayal.",
                "example": "Loyalty Pro: 'Supporting international climate agreements demonstrates loyalty to our global commitments.' <br> Loyalty Anti: 'Prioritizing global climate agreements can betray our national interests and workers.' <br> Betrayal Pro: 'Countries that withdraw from climate accords betray the collective effort needed to tackle global warming.' <br> Betrayal Anti: 'Forcing stringent climate policies can feel like a betrayal to communities dependent on traditional industries.'"
            },
            "Authority/Subversion": {
                "type": "checkbox",
                "tooltip": "Select if the content involves respect for or defiance against authority.",
                "example": "Authority Pro: 'Upholding the guidelines set by environmental scientists respects their authority and expertise.' <br> Authority Anti: 'Blindly following environmental authorities without considering economic impacts can be detrimental.' <br> Subversion Pro: 'Challenging the status quo is necessary when it hinders progress on climate action.' <br> Subversion Anti: 'Subverting traditional energy sectors under the guise of climate action can destabilize our economy.'"
            },
            "Purity/Degradation": {
                "type": "checkbox",
                "tooltip": "Select if the content involves themes of purity or degradation.",
                "example": "Purity Pro: 'Promoting clean energy reflects our desire for a pure, unspoiled environment.' <br> Purity Anti: 'The pursuit of environmental purity should not come at the expense of practical and immediate human needs.' <br> Degradation Pro: 'The degradation of our planet's ecosystems is a pressing concern that requires immediate action.' <br> Degradation Anti: 'Claims of environmental degradation often overlook the benefits and necessities of industrial development.'"
            }
        }
    },
    "Psychological Distance": {
        "section_instruction": "Evaluate the content's psychological distance in various dimensions and provide your assessment.",
        "annotations": {
            "Spatial Distance": {
                "type": "likert",
                "tooltip": "Rate the spatial distance discussed in the content.",
                "scale": 5,
                "example": "Pro: 'Climate change knows no borders; its effects are felt globally.' <br> Anti: 'Local environmental issues should take precedence over distant global concerns.'"
            },
            "Temporal Distance": {
                "type": "dropdown",
                "tooltip": "Select the temporal distance relevant to the content.",
                "options": ["Immediate", "Near Future", "Distant Future"],
                "example": "Pro: 'Immediate action is needed to prevent long-term climate catastrophe.' <br> Anti: 'We should focus on current economic challenges rather than distant climate predictions.'"
            },
            "Social Group Distance": {
                "type": "dropdown",
                "tooltip": "Select the social group distance discussed in the content.",
                "options": ["Local Communities", "National Populations", "Global Citizens"],
                "example": "Pro: 'Climate change affects everyone, transcending national identities.' <br> Anti: 'Our primary responsibility is to our own citizens, not to an abstract global community.'"
            },
            "Probability": {
                "type": "likert",
                "tooltip": "Rate the probability of the event discussed in the content.",
                "scale": 5,
                "example": "Pro: 'The probability of severe climate impacts is high without drastic changes.' <br> Anti: 'The likelihood of catastrophic climate change is overstated by alarmists.'"
            }
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
                        st.write(config['example'], unsafe_allow_html=True)
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
