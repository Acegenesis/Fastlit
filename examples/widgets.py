"""Fastlit Phase 2 demo: Widget Gallery."""

import fastlit as st

st.title("Widget Gallery")

# Text input
name = st.text_input("Your name", "World")

# Slider
volume = st.slider("Volume", 0, 100, 50)

# Number input
age = st.number_input("Age", min_value=0, max_value=120, value=25, step=1)

# Checkbox
agree = st.checkbox("I agree to the terms")

# Selectbox
color = st.selectbox("Favorite color", ["Red", "Green", "Blue", "Yellow"])

# Radio
size = st.radio("T-shirt size", ["S", "M", "L", "XL"])

# Text area
bio = st.text_area("Tell us about yourself", placeholder="Write something...")

# Display results
st.header("Results")
st.write(f"Hello **{name}**!")
st.write(f"Volume: {volume}")
st.write(f"Age: {age}")
st.write(f"Agreed: {agree}")
st.write(f"Color: {color}")
st.write(f"Size: {size}")
if bio:
    st.write(f"Bio: {bio}")
