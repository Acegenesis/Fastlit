# Streamlit API Reference for Fastlit Compatibility

This file documents the core Streamlit API that Fastlit aims to replicate.

## Text Elements

```python
st.title(body)           # Display text in title formatting
st.header(body)          # Display text in header formatting
st.subheader(body)       # Display text in subheader formatting
st.markdown(body)        # Display string formatted as Markdown
st.write(*args)          # Write arguments to the app (magic method)
st.text(body)            # Write fixed-width and preformatted text
st.caption(body)         # Display small text
st.code(body, language)  # Display a code block with syntax highlighting
st.divider()             # Display a horizontal rule
```

## Input Widgets

```python
st.button(label, key=None, on_click=None)
st.checkbox(label, value=False, key=None)
st.radio(label, options, index=0, key=None)
st.selectbox(label, options, index=0, key=None)
st.multiselect(label, options, default=None, key=None)
st.slider(label, min_value, max_value, value, step=None, key=None)
st.text_input(label, value="", key=None, type="default")
st.text_area(label, value="", key=None)
st.number_input(label, min_value, max_value, value, step, key=None)
st.date_input(label, value, key=None)
st.time_input(label, value, key=None)
st.file_uploader(label, type=None, key=None)
st.color_picker(label, value, key=None)
```

## Data Display

```python
st.dataframe(data, width=None, height=None)  # Display a dataframe
st.table(data)                                # Display a static table
st.metric(label, value, delta=None)           # Display a metric
st.json(body)                                 # Display JSON
```

## Charts

```python
st.line_chart(data)
st.area_chart(data)
st.bar_chart(data)
st.pyplot(fig)
st.plotly_chart(figure_or_data)
st.altair_chart(altair_chart)
```

## Layout

```python
st.sidebar                    # Add widgets to sidebar
st.columns(spec)              # Insert containers laid out as columns
st.tabs(tabs)                 # Insert containers as tabs
st.expander(label)            # Insert a multi-element container that can expand/collapse
st.container()                # Insert a multi-element container
st.empty()                    # Insert a single-element container
```

## State Management

```python
st.session_state              # Dict-like object for session state
st.session_state.key = value  # Set a value
value = st.session_state.key  # Get a value
```

## Caching

```python
@st.cache_data(ttl=None)      # Cache data-returning functions
@st.cache_resource            # Cache resource-returning functions (DB connections, etc.)
```

## Control Flow

```python
st.rerun()                    # Rerun the script from the top
st.stop()                     # Stop execution
st.form(key)                  # Create a form
st.form_submit_button(label)  # Form submit button
```

## Status Elements

```python
st.progress(value)            # Display a progress bar
st.spinner(text)              # Temporarily displays a message while executing
st.success(body)              # Display a success message
st.info(body)                 # Display an informational message
st.warning(body)              # Display a warning message
st.error(body)                # Display an error message
st.exception(exception)       # Display an exception
st.toast(body)                # Display a toast notification
```

## Media

```python
st.image(image, caption=None, width=None)
st.audio(data, format="audio/wav")
st.video(data, format="video/mp4")
```

## User Info (with auth)

```python
st.user.email                 # User's email (when authenticated)
st.user.name                  # User's name
st.require_login()            # Require authentication
```

---
*Reference for Fastlit development - ensuring API compatibility with Streamlit*
