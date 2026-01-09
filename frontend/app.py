import streamlit as st
import requests
from loguru import logger
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io

st.set_page_config(page_title="Reconnaissance de nombre", page_icon="🔢")

st.title("Reconaissance de nombre")
st.markdown("Dessinez un nombre (0-9) ci-dessous et laisse l'IA deviner!")

# Create a layout with two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Dessinez ici")
    # Drawable canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=15,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=280,
        width=280,
        drawing_mode="freedraw",
        key="canvas",
    )

prediction_state = st.session_state.get('prediction_state', None)
last_image_bytes = st.session_state.get('last_image_bytes', None)

if canvas_result.image_data is not None:
    # Check if the canvas is not empty (has some drawing)
    # canvas_result.image_data is a numpy array (height, width, 4)
    # A simple check is if the sum of the array is different from the background (all black)
    # But checking if user clicked "Predict" is better control
    
    if st.button("Prédire"):
        try:
            # Prepare image for API
            img = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
            img = img.convert("L")  # Convert to grayscale
            img = img.resize((28, 28))  # Resize to 28x28 (MNIST size)
            
            # Save to bytes
            img_bytes_io = io.BytesIO()
            img.save(img_bytes_io, format="PNG")
            img_bytes = img_bytes_io.getvalue()
            
            # Store for correction
            st.session_state['last_image_bytes'] = img_bytes

            # Call API
            files = {"file": ("canvas.png", img_bytes, "image/png")}
            response = requests.post("http://backend:8000/predict", files=files)
            response.raise_for_status()
            
            result = response.json()
            prediction = result.get("prediction")
            probabilities = result.get("probabilities")
            
            st.session_state['prediction_state'] = prediction
            
            with col2:
                st.subheader("Résultats")
                st.success(f"Prédiction: **{prediction}**")
                
                # Show probabilities
                if probabilities:
                    st.bar_chart(probabilities)

        except Exception as e:
            st.error(f"Error connecting to backend: {e}")
            logger.error(f"Frontend error: {e}")

# Correction section
if st.session_state.get('prediction_state') is not None:
    st.divider()
    st.subheader("Est-ce correct?")
    
    with st.expander("Non, aide moi à apprendre!"):
        correct_label = st.selectbox("Quel était le bon chiffre?", range(10))
        
        if st.button("Soumettre la correction"):
            if st.session_state.get('last_image_bytes'):
                try:
                    files = {
                        "file": ("correction.png", st.session_state['last_image_bytes'], "image/png")
                    }
                    data = {
                        "true_label": correct_label,
                        "predicted_label": st.session_state['prediction_state']
                    }
                    
                    response = requests.post("http://backend:8000/correct", files=files, data=data)
                    if response.status_code == 200:
                        st.success("Thank you! The model will learn from this mistake.")
                        # Clear state
                        st.session_state['prediction_state'] = None
                        st.session_state['last_image_bytes'] = None
                    else:
                        st.error("Failed to submit correction.")
                except Exception as e:
                    st.error(f"Error submitting correction: {e}")
