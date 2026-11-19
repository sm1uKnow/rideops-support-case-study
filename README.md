# Run the Streamlit app

1. Install Python 3.12 and extract RideOps_Desk.zip.
2. Open the folder containing app.py in VS Code. Choose Terminal → New Terminal.
3. In PowerShell, run each command in order.

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

4. Open the Local URL printed in the terminal. To stop, press Ctrl+C. To restart, repeat the last command.

# Run the notebook

1. Open Google Colab. Select File → Upload notebook and choose RideOps_Analysis.ipynb from the extracted folder.
2. Select Runtime → Run all. When prompted, upload the original RideOps_Desk.zip.

# Measure practice time

1. In the app, open Timed practice and choose Begin a practice pair.
2. Reveal each case, prepare a first reply, choose a reference decision and select Finish and record time. Complete both tasks.
3. Download practice_timings.csv. When running the notebook in Colab, upload this CSV alongside the project ZIP at the first prompt. For local notebooks, put the CSV beside the notebook.
