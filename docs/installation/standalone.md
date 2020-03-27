[Back - README](../../README.md)

# Setting up the code for standalone/modification

This only needs to be done if you want to modify the source code. Otherwise the `ASMBL.exe` can be used to eliminate the setup of the program.

**Windows**
```bash
git clone https://github.com/AndyEveritt/ASMBL.git
cd ASMBL
py -m venv env
source env/Scripts/activate
pip install -r requirements.txt
```

To run the standalone program, ensure the python virtual environment is enabled, then use `python main.py`

## Compiling source code for standalone

Run `pyinstaller --onefile main.py` to create the compiled `.exe` in the `dist` folder. The file will have the default name `main.exe`.