import streamlit as st
import pandas as pd
import numpy as np
import tensorflow as tf
import base64
import pickle
from sklearn.preprocessing import StandardScaler
from tf.keras.layers import ReLU
# Function to set background image
def set_image_local(image_path):
    with open(image_path, "rb") as file:
        img = file.read()
    base64_image = base64.b64encode(img).decode("utf-8")
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{base64_image}");
            background-size: cover;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def load_pickle_model(model_path):
    with open(model_path, 'rb') as file:
        return pickle.load(file)

# Set background image (Ensure correct path with extension)
set_image_local(r"E:\Project1\final_project\gears")

# Load Models
try:
    machining_finalized_h5 = tf.keras.models.load_model(r"E:\Project1\final_project\machining_finalized.h5")
    passed_visual_inspection_h5 = tf.keras.models.load_model(r"E:\Project1\final_project\passed_visual_inspection.h5")
    tool_condition_h5 = tf.keras.models.load_model(r"E:\Project1\final_project\tool_condition.h5")
    encoder = load_pickle_model(r"E:\Project1\final_project\encoder.pkl")
    scaler = load_pickle_model(r"E:\Project1\final_project\scaler.pkl")
except Exception as e:
    st.error(f"Error loading models: {e}")
    st.stop()

# Streamlit UI
st.title("🛠️ CNC Milling Performance Analysis & Fault Detection")
st.markdown("""
    <style>
    .big-font {
        font-size: 18px !important;
        color: #2E86C1;
    }
    </style>
    <p class="big-font">Analyze CNC milling performance and detect faults using machine learning models.</p>
    """, unsafe_allow_html=True)

# Sidebar for additional options
with st.sidebar:
    st.header("⚙️ Settings")
    task = st.selectbox("Select Classification Task", 
                        ["Tool condition", "Machining Completion status", "Visual Inspection status", "All Predictions"])
    st.markdown("---")
    st.markdown("### 📤 Upload Data")
    uploaded_file = st.file_uploader("Upload CNC Sensor Data (CSV)", type=["csv"])

# Main content
st.header("📊 Input Data")
col1, col2 = st.columns(2)
with col1:
    feed_rate = st.number_input("Enter Feed Rate:", min_value=0.0, step=0.1, help="Feed rate in mm/min")
with col2:
    clamp_pressure = st.number_input("Enter Clamp Pressure:", min_value=0.0, step=0.1, help="Clamp pressure in psi")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Remove target columns from input features
        target_columns = ["tool_condition", "machining_finalized", "passed_visual_inspection","material","feedrate","clamp_pressure"]
        df = df.drop(columns=[col for col in target_columns if col in df.columns], errors='ignore')

        # Ensure all columns except 'Machining_Process' and 'material' are numeric
        for col in df.columns:
            if col not in ["Machining_Process", "material"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert, setting invalid values to NaN

        # Encode categorical columns if present
        if "Machining_Process" in df.columns:
            df["Machining_Process"] = encoder.transform(df[["Machining_Process"]])
        else:
            st.warning("⚠️ 'Machining_Process' column not found in uploaded data.")

        # Add user inputs
        df["feedrate"] = feed_rate
        df["clamp_pressure"] = clamp_pressure

        # Prediction button
        if st.button("🚀 Predict", help="Click to make predictions"):
            with st.spinner("🔮 Making predictions..."):
                # Make Predictions
                df = df.apply(pd.to_numeric, errors="coerce").fillna(0)
                df_scale = scaler.transform(df)
                tool_condition_pred = tool_condition_h5.predict(df_scale)[0][0]
                machining_finalized = machining_finalized_h5.predict(df_scale)[0][0]
                passed_visual_inspection = passed_visual_inspection_h5.predict(df_scale)[0][0]

                # Extract values using .item()
                tool_condition_label = "✅ Unworn" if tool_condition_pred > 0.5 else "❌ Worn"
                machining_finalized_label = "✅ Completed" if machining_finalized < 0.5 else "❌ Incomplete"
                passed_visual_inspection_label = "✅ Passed" if passed_visual_inspection < 0.5 else "❌ Failed"

                # Display Predictions
                st.success("🎉 Predictions completed!")
                st.markdown("---")
                if task == "Tool condition":
                    st.markdown(f"### 🔧 Predicted Tool Condition: **{tool_condition_label}**")
                elif task == "Machining Completion status":
                    st.markdown(f"### 📦 Job Status: **{machining_finalized_label}**")
                elif task == "Visual Inspection status":
                    st.markdown(f"### 👀 Job Visual Inspection Status: **{passed_visual_inspection_label}**")
                else:  # "All Predictions"
                    st.markdown(f"### 🔧 Predicted Tool Condition: **{tool_condition_label}**")
                    st.markdown(f"### 📦 Job Status: **{machining_finalized_label}**")
                    st.markdown(f"### 👀 Job Visual Inspection Status: **{passed_visual_inspection_label}**")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
else:
    st.info("ℹ️ Please upload a CSV file to get started.")

