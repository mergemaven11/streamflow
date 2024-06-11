<h1 align="center">
  <img alt="cgapp logo" src="/src/icons/logo.png" width="260px"/><br/><br/>
   <!-- <p style="font-family: Verdana;"> StreamFlow </p> -->
</h1>

StreamFlow is a versatile virtual stream deck application designed to enhance the streaming experience for content creators. It empowers users to create custom button layouts tailored to their unique streaming needs, providing intuitive control over various streaming functionalities.

<div style="position: relative; width: max-content;">
  <img src="/src/icons/demo1.png" alt="Demo 1" style="width: 500px;">
  <img src="/src/icons/demo2.png" alt="Demo 2" style="position: absolute; bottom: -1px; right: -7px; width: 350px;">
</div>

## Features

- **Customizable Button Layouts:** Design your own button layouts, arranging buttons in a way that suits your workflow best.
- **Flexible Button Functionality:** Assign specific functions or actions to each button, such as starting/stopping a stream, switching scenes, adjusting audio levels, launching applications, or triggering custom scripts.
- **Interactive Visual Feedback:** Get interactive visual feedback indicating the current state of each button and relevant information.
- **Multi-Platform Support:** Compatible with Windows, macOS, and Linux.
- **Extensibility:** Extend functionality through plugins or custom scripts.

### Installation

Clone the repository:
  ```sh
   git clone https://github.com/streamflow/streamflow.git
   cd streamflow
```

### Setting Up a Virtual Environment

1. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ```
2. **Activate the Virtual Environment:**
  ```bash
  #windows 
  .\venv\Scripts\activate

  #macos and linux
   
  source venv/bin/activate
  ```

3. Install Dependencies:

```bash
pip install -r requirements.txt

```

Run the script:
```sh
python3 src/main.py
```