import streamlit as st
import gc
import torch
import os
from read_transcribe import process_prescription
from speech_avatar import process_transcription_to_avatar
import asyncio
import glob

# Initialize session state variables
if 'prescription_result' not in st.session_state:
    st.session_state.prescription_result = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'avatar_video_path' not in st.session_state:
    st.session_state.avatar_video_path = None

def free_memory():
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

async def process_prescription_ui():
    st.subheader("Prescription Processing")
    uploaded_file = st.file_uploader("Choose a prescription image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
    
    if st.session_state.uploaded_file:
        st.image(st.session_state.uploaded_file, caption="Uploaded Prescription", use_column_width=True)

        if st.button("Process Prescription"):
            with st.spinner("Processing..."):
                result = await process_prescription(st.session_state.uploaded_file)
                st.session_state.prescription_result = result  # Store the result

    # Display the result, whether it's from a new upload or from the session state
    if st.session_state.prescription_result:
        result = st.session_state.prescription_result
        st.subheader("Processed Information:")
        if 'medications' in result:
            for medication in result['medications']:
                st.write(medication)
        elif 'error' in result:
            st.error(f"Error: {result['error']}")
        else:
            st.write("No processed information available.")

        if 'disclaimer' in result:
            st.warning(result['disclaimer'])

def get_latest_video(output_dir):
    list_of_files = glob.glob(os.path.join(output_dir, '*.mp4'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def generate_avatar_video():
    st.subheader("Avatar Video Generation")
    
    if st.session_state.prescription_result is None:
        st.warning("Please process a prescription first.")
        return

    result = st.session_state.prescription_result

    if st.button("Generate Avatar Video") or st.session_state.avatar_video_path:
        if not st.session_state.avatar_video_path:
            st.warning("Creating avatar video may take some time and require significant computational resources.")
            with st.spinner("Generating Avatar Video..."):
                free_memory()
                
                base_dir = os.path.dirname(os.path.abspath(__file__))
                output_dir = os.path.join(base_dir, "output")
                image_loc = os.path.join(base_dir, "src", "doctor1.jpeg")
                print(f"Looking for avatar image at: {image_loc}")

                os.makedirs(output_dir, exist_ok=True)
                
                if not os.path.exists(image_loc):
                    st.error(f"Avatar image not found at {image_loc}")
                    return

                try:
                    medications_text = ""
                    for medication in result.get('medications', []):
                        medications_text += f"Medication: {medication['drug_name']}\n"
                    
                    process_transcription_to_avatar(medications_text, image_loc, output_dir)
                    
                    latest_video_path = get_latest_video(output_dir)
                    
                    if latest_video_path and os.path.exists(latest_video_path):
                        st.session_state.avatar_video_path = latest_video_path
                        st.success(f"Video created successfully")
                    else:
                        st.error("No video file found in the output directory.")
                except Exception as e:
                    st.error(f"Error during video creation: {str(e)}")
                    st.error("The avatar video could not be created. Please check the logs for more information.")
        
        if st.session_state.avatar_video_path:
            st.video(st.session_state.avatar_video_path)

async def main():
    st.title("Prescription Processing App")

    col1, col2 = st.columns(2)

    with col1:
        await process_prescription_ui()

    with col2:
        generate_avatar_video()

if __name__ == "__main__":
    asyncio.run(main())
